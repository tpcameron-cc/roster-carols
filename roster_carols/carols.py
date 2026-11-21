"""The carol book: four-part carol settings written in a small text format.

data/carols.txt holds one block per carol:

    == joy-to-the-world
    title: Joy to the World
    credit: Tune ANTIOCH (Lowell Mason, 1839)
    key: D major
    time: 2/4
    S: D5q C#5e. B4s | A4q. G4e | ...
    A: ...
    T: ...
    B: ...

Notes are <pitch><duration>[flags]: pitch in scientific notation (C4 = middle C,
sharps #, flats b) or r for a rest; duration w h q e s (whole ... sixteenth), with
a trailing . for dotted. Flags: ~ tie to the next note, , phrase end (a breath),
^ fermata (also a phrase end). Bars are separated by |. A first bar shorter than
the time signature is a pickup. A voice line may continue on the next line by
starting it with the same voice letter again (each line holds whole bars). // starts a comment.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from music21 import articulations, expressions, key, meter, note, stream, tie

DATA = Path(__file__).resolve().parent.parent / "data"
DUR = {"w": 4.0, "h": 2.0, "q": 1.0, "e": 0.5, "s": 0.25}
TOKEN = re.compile(r"^(r|[A-G](?:bb|b|##|#)?\d)([whqes])(\.?)([~,^]*)$")


class CarolError(ValueError):
    pass


@dataclass
class Carol:
    id: str
    title: str
    credit: str
    key: str
    time: str
    note: str = ""
    voices: dict[str, list[list[str]]] = field(default_factory=dict)   # voice -> bars -> tokens


def _parse_file(text: str) -> list[Carol]:
    carols: list[Carol] = []
    cur: Carol | None = None
    for raw in text.splitlines():
        line = raw.split("//", 1)[0].rstrip()
        if not line.strip():
            continue
        if line.startswith("=="):
            cur = Carol(line[2:].strip(), "", "", "", "")
            carols.append(cur)
            continue
        if cur is None:
            raise CarolError(f"text before the first carol: {line!r}")
        tag, _, val = line.partition(":")
        tag, val = tag.strip(), val.strip()
        if tag in ("S", "A", "T", "B"):
            cur.voices.setdefault(tag, [])
            cur.voices[tag].append(val)
        elif tag in ("title", "credit", "key", "time", "note"):
            setattr(cur, tag, val)
        else:
            raise CarolError(f"{cur.id}: unknown field {tag!r}")
    for c in carols:
        joined = {v: " | ".join(parts) for v, parts in c.voices.items()}
        c.voices = {v: [bar.split() for bar in s.split("|") if bar.strip()] for v, s in joined.items()}
    return carols


@lru_cache(maxsize=1)
def carols() -> dict[str, Carol]:
    return {c.id: c for c in _parse_file((DATA / "carols.txt").read_text(encoding="utf-8"))}


def parse_token(tok: str) -> tuple[str | None, float, set[str]]:
    m = TOKEN.match(tok)
    if not m:
        raise CarolError(f"can't read note {tok!r}")
    p, d, dot, flags = m.groups()
    ql = DUR[d] * (1.5 if dot else 1.0)
    name = None if p == "r" else p[0] + p[1:].replace("b", "-")
    return name, ql, set(flags)


def bar_length(ts: str) -> float:
    n, d = ts.split("/")
    return int(n) * 4.0 / int(d)


def to_score(c: Carol) -> stream.Score:
    """Build a four-part music21 score (Soprano/Alto/Tenor/Bass) from a carol."""
    if sorted(c.voices) != ["A", "B", "S", "T"]:
        raise CarolError(f"{c.id}: needs S, A, T and B lines")
    counts = {v: len(bars) for v, bars in c.voices.items()}
    if len(set(counts.values())) != 1:
        raise CarolError(f"{c.id}: voices have different numbers of bars {counts}")
    full = bar_length(c.time)
    tonic, mode = c.key.split()
    ks = key.Key(tonic.replace("b", "-") if len(tonic) > 1 else tonic, mode)
    sc = stream.Score()
    lengths: list[list[float]] = []
    for v, name in zip("SATB", ("Soprano", "Alto", "Tenor", "Bass")):
        part = stream.Part()
        part.partName = name
        row = []
        for i, toks in enumerate(c.voices[v]):
            m = stream.Measure(number=i if _is_pickup(c) else i + 1)
            if i == 0:
                m.insert(0, ks)
                m.insert(0, meter.TimeSignature(c.time))
            total = 0.0
            for tok in toks:
                p, ql, flags = parse_token(tok)
                n = note.Rest(quarterLength=ql) if p is None else note.Note(p, quarterLength=ql)
                if "~" in flags and p is not None:
                    n.tie = tie.Tie("start")
                if "^" in flags:
                    n.expressions.append(expressions.Fermata())
                if "," in flags:
                    n.articulations.append(articulations.BreathMark())
                m.append(n)
                total += ql
            row.append(total)
            if i == 0 and total < full - 1e-6:
                m.paddingLeft = full - total
            part.append(m)
        lengths.append(row)
        _fix_ties(part)
        sc.insert(0, part)
    for i in range(len(lengths[0])):
        bar = {v: lengths[k][i] for k, v in enumerate("SATB")}
        if len(set(bar.values())) != 1:
            raise CarolError(f"{c.id}: bar {i + 1} has different lengths per voice {bar}")
        first, last = i == 0, i == len(lengths[0]) - 1
        if not (first or last) and abs(bar["S"] - full) > 1e-6:
            raise CarolError(f"{c.id}: bar {i + 1} is {bar['S']} quarters, expected {full}")
    return sc


def _is_pickup(c: Carol) -> bool:
    return sum(parse_token(t)[1] for t in c.voices["S"][0]) < bar_length(c.time) - 1e-6


def _fix_ties(part: stream.Part) -> None:
    """Turn the '~' starts into proper start/continue/stop chains."""
    ns = list(part.recurse().notes)
    for a, b in zip(ns, ns[1:]):
        if a.tie is not None and a.tie.type in ("start", "continue"):
            if b.pitch.ps != a.pitch.ps:
                raise ValueError(f"tie between different pitches {a.pitch} -> {b.pitch} in m. {a.measureNumber}")
            b.tie = tie.Tie("continue" if b.tie is not None else "stop")
