"""The carol settings in data/carols.txt: well-formed, cleanly voiced, and in the catalog."""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from check_carols import check  # noqa: E402

from roster_carols import carols as carmod  # noqa: E402
from roster_carols import chorale as chmod  # noqa: E402

CAROLS = list(carmod.carols())


@pytest.mark.parametrize("cid", CAROLS)
def test_carol_voice_leading_is_clean(cid):
    assert check(carmod.carols()[cid]) == []


@pytest.mark.parametrize("cid", CAROLS)
def test_carol_loads_with_phrases_and_final_fermata(cid):
    ch = chmod.load(cid)
    for v, bars in ch.voices.items():
        evs = [e for b in bars for e in b.events]
        assert max(e.phrase for e in evs) >= 2, (cid, v)
        assert [e for e in evs if not e.is_rest][-1].fermata, (cid, v)


def test_catalog_is_in_sync_with_the_carol_file():
    cat = json.loads((ROOT / "data" / "catalog.json").read_text(encoding="utf-8"))
    assert [c["id"] for c in cat if c["source"] == "carol"] == CAROLS
    assert sum(c["source"] == "bach" for c in cat) >= 10


def test_bad_carol_text_is_rejected():
    bad = carmod._parse_file("== x\ntitle: X\ncredit: Y\nkey: C major\ntime: 4/4\n"
                             "S: C5w | C5h\nA: E4w | E4w\nT: G3w | G3w\nB: C3w | C3w\n")[0]
    with pytest.raises(carmod.CarolError):
        carmod.to_score(bad)


# ---------------------------------------------------------------------------
# Grades 4 and 5: decorated carols
# ---------------------------------------------------------------------------
from music21 import meter, note, stream  # noqa: E402

from check_carols import check_score  # noqa: E402
from roster_carols.arrange import arrange, grade_cfg  # noqa: E402
from roster_carols.embellish import embellish  # noqa: E402


def _score(ch, ts):
    sc = stream.Score()
    for v in "SATB":
        part = stream.Part()
        for i, b in enumerate(ch.voices[v]):
            m = stream.Measure(number=b.number)
            if i == 0:
                m.insert(0, meter.TimeSignature(ts))
                m.paddingLeft = b.padding
            for e in b.events:
                m.append(note.Rest(quarterLength=e.dur) if e.is_rest else note.Note(e.pitch, quarterLength=e.dur))
            part.append(m)
        sc.insert(0, part)
    return sc


@pytest.mark.parametrize("level", [1, 2])
@pytest.mark.parametrize("cid", CAROLS)
def test_decorated_carol_keeps_clean_voice_leading_and_bar_lengths(cid, level):
    ch = chmod.load(cid)
    dec, added = embellish(ch, level)
    assert sum(added.values()) >= 5
    if level == 1:
        assert "S" not in added           # grade 4 leaves the melody alone
    for v in "SATB":
        assert [round(b.length, 4) for b in dec.voices[v]] == [round(b.length, 4) for b in ch.voices[v]]
    issues = [i for i in check_score(_score(dec, carmod.carols()[cid].time), carmod.carols()[cid].time)
              if "parallel" in i or "below" in i or "wider" in i]
    assert issues == []


def test_grade5_is_busier_than_grade3_and_says_so():
    roster = {"Flute": 4, "Clarinet": 4, "Alto Sax": 2, "Trumpet": 3, "Horn": 2, "Trombone": 2, "Tuba": 1,
              "Percussion": 2}
    g3 = arrange("deck-the-halls", roster, "3")
    g5 = arrange("deck-the-halls", roster, "5")
    count = lambda res: sum(p["musicxml"].count("<note") for p in res["parts"] if p["instrument"] != "Percussion")
    assert count(g5) > count(g3) * 1.2
    assert any("decorated" in n for n in g5["notes"]) and not any("decorated" in n for n in g3["notes"])
    assert any("<type>16th</type>" in p["musicxml"] for p in g5["parts"])
    assert grade_cfg("5")["label"] == "Grade 5 (Pro)"


def test_bach_chorales_are_not_decorated():
    res = arrange("bwv368", {"Flute": 4, "Clarinet": 4, "Trombone": 2, "Tuba": 1}, "5", with_parts=False)
    assert not any("decorated" in n for n in res["notes"])
