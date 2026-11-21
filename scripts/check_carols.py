"""Check the four-part writing of the carols in data/carols.txt.

    uv run python scripts/check_carols.py            # every carol
    uv run python scripts/check_carols.py joy-to-the-world -v

Flags: parallel fifths/octaves between any two voices, voice crossing, wide spacing,
vocal ranges, and beats whose sounding notes aren't a triad or seventh chord.
-v prints every onset's chord so the harmony can be read through.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from music21 import chord, pitch  # noqa: E402

from roster_carols import carols as carmod  # noqa: E402

RANGES = {"S": ("A3", "G5"), "A": ("F#3", "D5"), "T": ("C3", "G4"), "B": ("E2", "D4")}
V = "SATB"


# chord templates (semitones above the root): triads and seventh chords
TEMPLATES = [{0, 4, 7}, {0, 3, 7}, {0, 3, 6}, {0, 4, 7, 10}, {0, 3, 7, 10}, {0, 4, 7, 11}, {0, 3, 6, 10}, {0, 3, 6, 9}]


def chord_ok(pcs: set[int]) -> bool:
    """A complete or incomplete triad/seventh chord: every note fits a template, root and third present
    (or just two pitch classes, e.g. an open fifth or octave)."""
    if len(pcs) <= 2:
        return True
    for r in pcs:
        rel = {(p - r) % 12 for p in pcs}
        for t in TEMPLATES:
            if rel <= t and (3 in rel or 4 in rel):
                return True
    return False


def timeline(part):
    """[(abs offset, end, midi or None, measure, beat)]"""
    out = []
    t0 = 0.0
    for m in part.getElementsByClass("Measure"):
        pad = float(m.paddingLeft or 0)
        for n in m.notesAndRests:
            st = t0 + float(n.offset)
            out.append((st, st + float(n.quarterLength), None if n.isRest else n.pitch, m.number,
                        pad + float(n.offset), bool(n.tie and n.tie.type in ("stop", "continue"))))
        t0 += float(m.duration.quarterLength)
    return out


def sounding(tl, t):
    for st, en, p, *_ in tl:
        if st <= t + 1e-6 < en:
            return p
    return None


def check(c, verbose=False):
    return check_score(carmod.to_score(c), c.time, verbose)


def check_score(sc, time_sig, verbose=False):
    tls = {v: timeline(p) for v, p in zip(V, sc.parts)}
    onsets = sorted({round(st, 4) for tl in tls.values() for st, *_ in tl})
    issues = []
    meas = {round(st, 4): (m, b) for st, en, p, m, b, _ in tls["S"]}
    for v in V:
        lo, hi = (pitch.Pitch(x).ps for x in RANGES[v])
        for st, en, p, m, b, _ in tls[v]:
            if p is not None and not lo <= p.ps <= hi:
                issues.append(f"m{m} {v} {p.nameWithOctave} out of {RANGES[v]}")
    prev = None
    ts = time_sig
    beat_len = 1.5 if ts.endswith("/8") and int(ts.split("/")[0]) % 3 == 0 else 1.0
    for t in onsets:
        cur = {v: sounding(tls[v], t) for v in V}
        m = next((tl_m for st, en, p, tl_m, b, _ in tls["S"] if st <= t + 1e-6 < en), "?")
        beat_pos = next((b + (t - st) for st, en, p, tl_m, b, _ in tls["S"] if st <= t + 1e-6 < en), 0)
        ps = [p for p in cur.values() if p is not None]
        ch = chord.Chord(ps) if ps else None
        on_beat = abs(beat_pos / beat_len - round(beat_pos / beat_len)) < 1e-6
        ok = not ps or chord_ok({p.pitchClass for p in ps})
        s_dur = next((en - st for st, en, p, *_ in tls["S"] if st <= t + 1e-6 < en), 1.0)
        if not ok and s_dur < 1.0 - 1e-6:   # a short melody note over a chord: passing tone
            ok = chord_ok({cur[v].pitchClass for v in "ATB" if cur[v] is not None})
        label = f"m{m} b{beat_pos + 1:g}"
        if verbose:
            names = " ".join(f"{v}:{(cur[v].nameWithOctave if cur[v] else '-'):5}" for v in V)
            print(f"  {label:9} {names}  {ch.pitchedCommonName if ch else ''}")
        if not ok and on_beat:
            issues.append(f"{label} not a triad/7th: {[p.nameWithOctave for p in ps]}")
        for a, b in zip(V, V[1:]):
            if cur[a] and cur[b] and cur[a].ps < cur[b].ps:
                issues.append(f"{label} {a} below {b}")
        for a, b in (("S", "A"), ("A", "T")):
            if cur[a] and cur[b] and cur[a].ps - cur[b].ps > 12:
                issues.append(f"{label} {a}-{b} wider than an octave")
        if prev:
            for i, a in enumerate(V):
                for b in V[i + 1:]:
                    p1, p2, q1, q2 = prev[a], prev[b], cur[a], cur[b]
                    if None in (p1, p2, q1, q2):
                        continue
                    if p1.ps == q1.ps and p2.ps == q2.ps:
                        continue
                    i1, i2 = (p1.ps - p2.ps) % 12, (q1.ps - q2.ps) % 12
                    if i1 == i2 and i1 in (0, 7) and (q1.ps - p1.ps) * (q2.ps - p2.ps) > 0:
                        issues.append(f"{label} parallel {'octaves' if i1 == 0 else 'fifths'} {a}/{b} "
                                      f"({p1.nameWithOctave}-{p2.nameWithOctave} -> {q1.nameWithOctave}-{q2.nameWithOctave})")
        prev = cur
    return issues


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    verbose = "-v" in sys.argv
    allc = carmod.carols()
    ids = args or list(allc)
    total = 0
    for cid in ids:
        try:
            iss = check(allc[cid], verbose)
        except Exception as e:  # noqa: BLE001
            iss = [f"ERROR {e}"]
        total += len(iss)
        print(f"{cid}: {'ok' if not iss else str(len(iss)) + ' issues'}")
        for i in iss:
            print("   ", i)
    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main()
