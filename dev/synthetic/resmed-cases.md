# ResMed synthetic cases

**Kept current; its history is in git.** This file and `formats/resmed.md` are the only inputs to the ResMed generator, `dev/synthetic/resmed.py`. Each case below says what it exercises and what a correct reader must show. The generator writes each case to `dev/synthetic/out/resmed/<case>/`, which git ignores, together with an `answer.json`.

**The data need not look realistic.** Z, 2026-09-19: *"The generated data does not have to be realistic. I'll test with real data. On my end."* A signal is therefore whatever shape makes its answer easy to check: a ramp, a square wave, a constant. Realism is Z's own testing, on a real card.

**Every answer is known by construction.** `answer.json` is written from the values the generator used, never read back from the file it produced. A check that compares the generator's output with itself is not a check.

## What every case carries

- **The card layout** of `formats/resmed.md`: a `DATALOG` folder, day folders named `yyyyMMdd`, and files named `yyyyMMdd_HHmmss_KIND.edf`.
- **Filler for the files PAPvault must never open:** `STR.edf`, `Journal.dat`, `Identification.tgt`, a `SETTINGS` folder and a `.crc` beside each EDF file. Each holds meaningless bytes. Nothing needs their real format, because nothing reads them.
- **A marker in every identifying field.** The patient and recording fields of every header hold a distinctive string, recorded in `answer.json`. It must never appear in the page, in what the page stores, or in anything the page exports.

## The cases

| Case | What it exercises |
|---|---|
| `plain-night` | one session, all five kinds of file, a handful of events at known times |
| `two-sessions` | a mask-off break: two sessions in one night, in one day folder |
| `after-midnight` | a session starting after midnight, filed in the *next* day's folder on purpose, so the answer proves the folder decides nothing |
| `crosses-noon` | a session running from before noon to after it. Its whole data belongs to the day it began in |
| `empty-day` | a day folder with no files, and a gap of several days between two nights |
| `no-oximeter` | no `SAD` files, so the reader must cope with a kind that is missing |
| `five-days` | five CPAP days in a row, for a range selection and its summaries. The nights differ in start and length; one has no oximetry; one day holds two sessions, the second of which starts after midnight and is filed under the day before |
| `other-labels` | the short and translated label forms of `formats/resmed.md`, including one with bytes outside ASCII. The reader reports which signals it did not find rather than guessing |
| `lies` | files that do not add up; each is its own card, listed below |

## What `lies` contains

Each of these is a separate card, and each must be reported and refused rather than read past. None may crash the page, hang it, or allocate without bound.

| File | What is wrong |
|---|---|
| `truncated` | the header claims more data records than the file holds |
| `short-header` | the header length field disagrees with the number of signals |
| `flat-physical` | physical minimum equals physical maximum, which would divide by zero |
| `inverted-digital` | digital maximum is not larger than digital minimum |
| `huge-samples` | a samples-per-record that would need gigabytes |
| `unterminated-tal` | an annotation list that runs past the end of its record |
| `markup-event` | an event whose text is `<script>alert(1)</script>`. It must appear on the page as those characters, and never as markup |
| `non-ascii-header` | bytes outside ASCII in a label, which EDF+ forbids but a device may still write |

## What `answer.json` holds

For each case:
- **each session:** its start, its end, the CPAP day it belongs to, and which kinds of file it has;
- **each signal:** its label as written, its unit, its sampling interval, how many samples, and its value at a few named times;
- **each event:** its text, its start and its duration;
- **per CPAP day:** which sessions belong to it, and the totals a summary must show;
- **the identifying marker,** which must appear nowhere in the page;
- **for `lies`:** what the reader is expected to report, per file.

## Open

- **The summary figures** a day or a range shows have not been decided yet. Until they are, `answer.json` carries what the sessions contain, not what a summary should say.
