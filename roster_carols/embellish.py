"""Make a carol harder for advanced grades by decorating its lines.

The carols are written as plain hymn settings, mostly block chords, so even "as written"
they are easy. For grade 4 and up, this adds the kind of figuration an arranger would:

* level 1 (grade 4): passing eighth notes that fill the thirds in the alto, tenor and bass.
* level 2 (grade 5): the same in all four lines (the melody too), plus passing sixteenths
  across fourths in the tenor and bass, and neighbour notes between repeated half notes
  in the lower three lines; long alto and tenor notes pulse in quarters and long bass notes
  leap an octave halfway through.

Every added note is a step of the key's scale between two chord tones, sits inside the
note it decorates (bar lengths never change), and is checked against the other lines so it
never crosses them or makes parallel fifths or octaves. Phrase ends (breaths and fermatas)
and tied notes are left alone.
"""
from __future__ import annotations

import copy

from music21 import pitch

from .chorale import EPS, Bar, Chorale, Ev, _timeline, mark_phrases

ORDER = ["B", "T", "A", "S"]
ABOVE = {"B": "T", "T": "A", "A": "S", "S": None}
BELOW = {"S": "A", "A": "T", "T": "B", "B": None}


def _sounding(bars: list[Bar], t: float) -> Ev | None:
    for st, _, e in _timeline(bars):
        if st - EPS <= t < st + e.dur - EPS:
            return e
    return None


def _midi(e: Ev | None) -> float | None:
    return None if e is None or e.is_rest else e.pitch.ps


def _scale_step(sc: set[int], p: pitch.Pitch, up: bool) -> pitch.Pitch | None:
    """The nearest pitch above (or below) p whose pitch class is in the scale."""
    for k in (1, 2):
        q = p.transpose(k if up else -k)
        if int(q.ps) % 12 in sc:
            return pitch.Pitch(midi=int(q.ps))
    return None


def _passing(sc, a: pitch.Pitch, b: pitch.Pitch, n: int) -> list[pitch.Pitch] | None:
    """n scale steps strictly between a and b, each a half or whole step apart."""
    up = b.ps > a.ps
    out, cur = [], a
    for _ in range(n):
        cur = _scale_step(sc, cur, up)
        if cur is None:
            return None
        out.append(cur)
    chain = [a.ps] + [p.ps for p in out] + [b.ps]
    if any(not 1 <= abs(y - x) <= 2 for x, y in zip(chain, chain[1:])):
        return None
    if any((y - x) * (1 if up else -1) <= 0 for x, y in zip(chain, chain[1:])):
        return None
    return out


def _neighbour(sc, a: pitch.Pitch) -> pitch.Pitch | None:
    p = _scale_step(sc, a, True)
    return p if p is not None and 1 <= p.ps - a.ps <= 2 else None


def _safe(ch: Chorale, v: str, t0: float, notes: list[tuple[float, float, float]], end_pitch: float) -> bool:
    """Would these new notes [(start, dur, midi)] in voice v (which then moves to end_pitch)
    cross another line or make parallel fifths/octaves with it?"""
    others = [o for o in ch.voices if o != v]
    up, down = ABOVE[v], BELOW[v]
    for start, dur, m in notes:
        for o, limit in ((up, "above"), (down, "below")):
            if o is None:
                continue
            for probe in (start, start + dur - 1e-3):
                om = _midi(_sounding(ch.voices[o], probe))
                if om is None:
                    continue
                if (limit == "above" and m >= om) or (limit == "below" and m <= om):
                    return False
    # motions this voice makes: into each new note, and out of the last one
    moves = []
    prev = _midi(_sounding(ch.voices[v], t0 - 1e-3))
    for start, dur, m in notes:
        moves.append((start, prev, m))
        prev = m
    moves.append((notes[-1][0] + notes[-1][1], prev, end_pitch))
    for t, a1, a2 in moves:
        if a1 is None or a2 is None or a1 == a2:
            continue
        for o in others:
            b1, b2 = _midi(_sounding(ch.voices[o], t - 1e-3)), _midi(_sounding(ch.voices[o], t + 1e-3))
            if b1 is None or b2 is None or b1 == b2:
                continue
            i1, i2 = abs(a1 - b1) % 12, abs(a2 - b2) % 12
            if i1 == i2 and i1 in (0, 7) and (a2 - a1) * (b2 - b1) > 0:
                return False
    return True


def embellish(ch: Chorale, level: int) -> tuple[Chorale, dict[str, int]]:
    """Return a decorated copy of the carol and how many notes were added per voice."""
    out = copy.deepcopy(ch)
    if not level:
        return out, {}
    sc = {int(p.ps) % 12 for p in out.key.getScale(out.key.mode if out.key.mode in ("major", "minor") else "major").getPitches()}
    voices = ORDER if level >= 2 else ["B", "T", "A"]
    added: dict[str, int] = {}
    for v in voices:
        bars = out.voices[v]
        flat = [(st, b, e) for st, b, e in _timeline(bars)]
        for (st, b, e1), (st2, _, e2) in zip(flat, flat[1:]):
            if e1.is_rest or e2.is_rest or e1.fermata or e1.breath or e1.phrase != e2.phrase:
                continue
            if e1.tie is not None or e2.tie in ("stop", "continue"):
                continue
            if abs(st + e1.dur - st2) > EPS:
                continue
            semis = e2.pitch.ps - e1.pitch.ps
            plan: list[tuple[float, pitch.Pitch]] | None = None   # (duration, pitch) of each new note
            if abs(semis) in (3, 4) and e1.dur >= 1 - EPS:
                ps = _passing(sc, e1.pitch, e2.pitch, 1)
                plan = ps and [(0.5, ps[0])]
            elif level >= 2 and v in "TB" and abs(semis) == 5 and e1.dur >= 1 - EPS:
                ps = _passing(sc, e1.pitch, e2.pitch, 2)
                plan = ps and [(0.25, ps[0]), (0.25, ps[1])]
            elif level >= 2 and v != "S" and semis == 0 and e1.dur >= 2 - EPS:
                nb = _neighbour(sc, e1.pitch)
                plan = nb and [(0.5, nb)]
            if not plan:
                continue
            total = sum(d for d, _ in plan)
            start = st + e1.dur - total
            new = []
            t = start
            for d, p in plan:
                new.append((t, d, p.ps))
                t += d
            if not _safe(out, v, start, new, e2.pitch.ps):
                continue
            # apply: shorten e1 and insert the new notes right after it, in the same bar
            idx = b.events.index(e1)
            e1.dur -= total
            off = e1.offset + e1.dur
            for d, p in plan:
                idx += 1
                b.events.insert(idx, Ev(off, d, p, phrase=e1.phrase))
                off += d
            added[v] = added.get(v, 0) + len(plan)
    if level >= 2:
        _drive(out, added)
    mark_phrases(out)
    return out, added


def _drive(ch: Chorale, added: dict[str, int]) -> None:
    """Grade 5 rhythmic drive: long inner-voice notes pulse in quarter notes, and long bass
    notes leap an octave halfway through (the way a band arranger keeps a hymn moving)."""
    for v in ("A", "T"):
        for b in ch.voices[v]:
            new: list[Ev] = []
            for e in b.events:
                pos = b.padding + e.offset
                if (e.is_rest or e.fermata or e.tie is not None or e.dur < 2 - EPS
                        or abs(pos - round(pos)) > EPS):
                    new.append(e)
                    continue
                n = int(e.dur + EPS)
                pieces = [1.0] * n + ([e.dur - n] if e.dur - n > EPS else [])
                off = e.offset
                for k, d in enumerate(pieces):
                    new.append(Ev(off, d, copy.deepcopy(e.pitch), phrase=e.phrase,
                                  breath=e.breath and k == len(pieces) - 1))
                    off += d
                added[v] = added.get(v, 0) + len(pieces) - 1
            b.events = new
    flat = list(_timeline(ch.voices["B"]))
    for i, (st, b, e) in enumerate(flat):
        if e.is_rest or e.fermata or e.tie is not None or e.dur < 2 - EPS:
            continue
        half = e.dur / 2
        if abs(half * 2 - round(half * 2)) > EPS:      # keep the split on an eighth-note grid
            continue
        jump = -12 if e.pitch.ps - 12 >= 40 else 12      # down an octave unless that falls below E2
        p2 = e.pitch.transpose(jump)
        nxt = flat[i + 1][2] if i + 1 < len(flat) else None
        end = p2.ps if nxt is None or nxt.is_rest else nxt.pitch.ps
        if not _safe(ch, "B", st + half, [(st + half, half, p2.ps)], end):
            continue
        idx = b.events.index(e)
        breath = e.breath
        e.dur, e.breath = half, False
        b.events.insert(idx + 1, Ev(e.offset + half, half, p2, phrase=e.phrase, breath=breath))
        added["B"] = added.get("B", 0) + 1
