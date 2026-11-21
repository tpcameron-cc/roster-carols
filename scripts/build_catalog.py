"""Build data/catalog.json: the carols in data/carols.txt plus Bach's Christmas chorales.

Run after editing data/carols.txt:  uv run python scripts/build_catalog.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from music21 import corpus  # noqa: E402

from roster_carols import carols as carmod  # noqa: E402

OUT = ROOT / "data" / "catalog.json"

# Bach's chorales for Advent, Christmas and Epiphany in the music21 corpus (all clean SATB).
# (file, title, subtitle)
BACH = [
    ("bwv368", "In dulci jubilo", "In sweet rejoicing (Good Christian friends, rejoice)"),
    ("bwv248.12-2", "Brich an, o schönes Morgenlicht", "Break forth, O beauteous heavenly light · Christmas Oratorio, Part II"),
    ("bwv248.5", "Wie soll ich dich empfangen", "How shall I fitly meet thee? · Christmas Oratorio, Part I"),
    ("bwv248.28", "Dies hat er alles uns getan", "All this he has done for us · Christmas Oratorio, Part III"),
    ("bwv248.33-3", "Ich will dich mit Fleiß bewahren", "I will keep you close · Christmas Oratorio, Part III"),
    ("bwv248.46-5", "Dein Glanz all Finsternis verzehrt", "Your light consumes all darkness · Christmas Oratorio, Part V"),
    ("bwv248.53-5", "Zwar ist solche Herzensstube", "Though my heart is but a poor room · Christmas Oratorio, Part V"),
    ("bwv65.2", "Puer natus in Bethlehem", "A child is born in Bethlehem"),
    ("bwv62.6", "Nun komm, der Heiden Heiland", "Savior of the nations, come (Advent)"),
    ("bwv64.2", "Gelobet seist du, Jesu Christ", "All praise to you, Jesus Christ"),
    ("bwv151.5", "Lobt Gott, ihr Christen, allzugleich", "Praise God, you Christians, all together"),
    ("bwv414", "Uns ist ein Kindlein heut' gebor'n", "To us a child is born today"),
    ("bwv40.3", "Wir Christenleut'", "We Christian folk"),
    ("bwv121.6", "Christum wir sollen loben schon", "Now praise we Christ, the holy one"),
    ("bwv40.8", "Freuet euch, ihr Christen alle", "Rejoice, all you Christians"),
    ("bwv36.4-2", "Wie schön leuchtet der Morgenstern", "How brightly shines the morning star (Epiphany)"),
]


def main() -> None:
    out = []
    for c in carmod.carols().values():
        sc = carmod.to_score(c)
        out.append({"id": c.id, "source": "carol", "title": c.title, "subtitle": c.note, "credit": c.credit,
                    "key": c.key, "measures": len(sc.parts[0].getElementsByClass("Measure"))})
    for fn, title, sub in BACH:
        s = corpus.parse(f"bach/{fn}")
        names = [(p.partName or "").strip() for p in s.parts]
        assert names == ["Soprano", "Alto", "Tenor", "Bass"], (fn, names)
        k = s.analyze("key")
        out.append({"id": fn, "source": "bach", "file": fn, "bwv": fn.removeprefix("bwv"),
                    "title": title, "subtitle": sub, "credit": f"J. S. Bach · BWV {fn.removeprefix('bwv')}",
                    "key": f"{k.tonic.name.replace('-', 'b')} {k.mode}",
                    "measures": len(s.parts[0].getElementsByClass("Measure"))})
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {len(out)} pieces ({sum(c['source'] == 'carol' for c in out)} carols)")


if __name__ == "__main__":
    main()
