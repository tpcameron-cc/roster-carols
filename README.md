<div align="center">

# ❄ Roster Carols

**Turn a Christmas carol into printable parts for the band or orchestra you *actually* have.**

Winds, brass, strings, mallets and percussion, voiced for your roster, in a concert key that keeps everyone in range, at the grade you pick.

A holiday edition of [Roster Chorale](https://github.com/tpcameron-cc/roster-chorale).

</div>

---

## What's in the book

**13 carols**, each a clean four-part (SATB) setting written for this app on the traditional melody:

| Carol | Melody |
|---|---|
| Joy to the World | Lowell Mason (1839), after Handel |
| Hark! The Herald Angels Sing | Felix Mendelssohn (1840) |
| Silent Night | Franz Xaver Gruber (1818) |
| O Come, All Ye Faithful | John Francis Wade (c. 1743) |
| Away in a Manger | W. J. Kirkpatrick (1895), *Cradle Song* |
| The First Noel | Traditional English |
| O Come, O Come, Emmanuel | 15th-century French |
| Good King Wenceslas | *Piae Cantiones* (1582) |
| Deck the Halls | Traditional Welsh |
| We Wish You a Merry Christmas | Traditional English |
| Jingle Bells (verse and chorus) | James Lord Pierpont (1857) |
| God Rest Ye Merry, Gentlemen | Traditional English |
| What Child Is This? | *Greensleeves* |

**16 of Bach's Christmas chorales** from the music21 corpus: *In dulci jubilo*, six chorales from the *Christmas Oratorio* (including *Brich an, o schönes Morgenlicht*), *Puer natus in Bethlehem*, *Nun komm, der Heiden Heiland* and more.

## How it works

Everything from Roster Chorale carries over: upload, paste or type a roster; pick a grade (½ to 5) and *one part per instrument* or *split sections*; the app tries every allowed concert key, voices the four lines across your instruments, fixes octaves by whole part and then by phrase, writes timpani and percussion parts, and engraves every transposed part for printing or MusicXML download.

What's different for carols:

- **Phrases are marked by breath marks**, not fermatas, so octave fixes and phrase rests happen at the ends of sung lines, and every part prints a breath mark there. Percussion frames each phrase (bass drum at the start, suspended cymbal at the end).
- **Gentler rhythm simplification**, so the tunes stay recognisable: grade ½ merges eighths into quarters; grades 1 and 2 only merge sixteenths into eighths; grade 3 plays as written.
- **Grades 4 and 5 (Pro).** As written, a hymn-style carol is easy, so the top grades add notes: grade 4 decorates the alto, tenor and bass with passing eighths; grade 5 decorates every line (the melody too) with passing eighths, passing sixteenths across fourths in the tenor and bass, and neighbour notes, then keeps the long notes moving: the alto and tenor pulse in quarter notes and the bass leaps an octave halfway through held notes. Every added note is a scale step checked against the other lines (no crossings, no parallel fifths or octaves). Both grades also widen the ranges, open up harder keys (up to six flats or sharps at grade 5) and make the percussion busier: bass drum on every downbeat, timpani on every tonic and dominant beat. Bach's chorales already have this kind of motion, so they get the wider ranges and keys but no added notes.
- **No "start from a key" mode.** With a small book you just pick the carol; the app picks the key. (The API still accepts a `key` to force one.)

## The carol settings

The carols live in [`data/carols.txt`](data/carols.txt) in a small text format, one block per carol:

```text
== silent-night
title: Silent Night
credit: Franz Xaver Gruber (1818)
key: C major
time: 3/4
S: G4q. A4e G4q | E4h., | ...
A: E4h. | C4h. | ...
```

Notes are pitch + duration (`w h q e s`, `.` for dotted); `,` ends a phrase, `^` is a fermata, `~` ties, `r` is a rest, `|` is a barline. Every setting is checked by [`scripts/check_carols.py`](scripts/check_carols.py) (and by the test suite) for parallel fifths and octaves, voice crossing, spacing, vocal ranges and chord spelling. The melodies were checked note for note and rhythm for rhythm against a published carol tunebook.

To add a carol: write its block, then

```bash
uv run python scripts/check_carols.py your-carol-id -v
uv run python scripts/build_catalog.py
```

### Brass choirs and small groups

With fewer instrument types than lines, the four lines are shared out by register and by number of players, top-down: a tuba quartet gets Tuba 1–4 on soprano to bass; 4 euphoniums + 4 tubas gives euphoniums soprano/alto and tubas tenor/bass; 6 euphoniums + 2 tubas gives euphoniums soprano/alto/tenor and tubas bass. In *split sections*, a low section that only suits the bass line (tuba, bari sax, string bass) with two or more players divides into two parts an octave apart where the range allows.

## Run it locally

```bash
uv sync
uv run uvicorn app:app --port 8322
```

Open <http://localhost:8322>. Tests: `uv run pytest` (about 440).

Command line:

```bash
uv run python -m roster_carols samples/lopsided-band.xlsx --piece silent-night --grade 1 --out out/
uv run python -m roster_carols samples/lopsided-band.xlsx --piece 368 --grade 2 --parts multiple --out out/
```

## API

| Method | Path | Body | Returns |
|---|---|---|---|
| `GET` | `/api/chorales` | — | the carols and chorales, instruments and grades |
| `POST` | `/api/roster` | multipart `file` (.xlsx/.csv) **or** form field `text` | cleaned counts + unrecognised names |
| `POST` | `/api/arrange` | `{"roster": {...}, "chorale": "silent-night", "grade": "1", "parts": "single"}` (optional `"key": "Bb major"`) | key decision, voicing, fit report, MusicXML per part |
| `POST` | `/api/zip` | same as `/api/arrange` | `application/zip` of all parts + `fit-report.txt` |

## Deploy

Same as Roster Chorale: `vercel deploy --prod` (one static page plus one Python function).

## Credits

- Traditional and public-domain carol melodies; four-part settings written for this project (MIT).
- **J. S. Bach**: the chorales (public domain), via **[music21](https://www.music21.org/)** (BSD).
- **[Verovio](https://www.verovio.org/)** (LGPL) for engraving; **FastAPI**, **openpyxl**, **uv**.

[MIT](LICENSE). The grade table is a starting point, not an official standard.
