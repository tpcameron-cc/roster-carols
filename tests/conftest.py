import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

LOPSIDED = {"Flute": 9, "Clarinet": 5, "Bass Clarinet": 1, "Alto Sax": 3, "Tenor Sax": 1,
            "Bari Sax": 1, "Trumpet": 4, "Horn": 1, "Trombone": 2, "Tuba": 1}

# A spread of carols and Bach Christmas chorales: major and minor, with pickups, sixteenths and ties.
SAMPLE_CHORALES = ["joy-to-the-world", "hark-the-herald", "silent-night", "the-first-noel",
                   "o-come-o-come-emmanuel", "good-king-wenceslas", "deck-the-halls", "god-rest-ye-merry-gentlemen",
                   "what-child-is-this", "jingle-bells", "bwv368", "bwv65.2"]


@pytest.fixture
def lopsided():
    return dict(LOPSIDED)


@pytest.fixture
def sample_xlsx():
    return ROOT / "samples" / "lopsided-band.xlsx"
