# ResMed synthetic cases

**Kept current; its history is in git.** This file and `dev/formats/resmed.md` are the only inputs to the ResMed generator, `dev/synthetic/resmed.py`. Each case below says what it exercises and what a correct reader must show. The generator writes each case to `dev/synthetic/out/resmed/<case>/`, which git ignores, together with an `answer.json`.

**The data need not look realistic.** Z, 2026-09-19: *"The generated data does not have to be realistic. I'll test with real data. On my end."* A signal is therefore whatever shape makes its answer easy to check: a ramp, a square wave, a constant. Realism is Z's own testing, on a real card.

**Every answer is known by construction.** `answer.json` is written from the values the generator used, never read back from the file it produced. A check that compares the generator's output with itself is not a check.

## What every case carries

- **The card layout** of `dev/formats/resmed.md`: a `DATALOG` folder, day folders named `yyyyMMdd`, and files named `yyyyMMdd_HHmmss_KIND.edf`.
- **Filler for the files PAPvault must never open:** `STR.edf`, `Journal.dat`, `Identification.tgt`, a `SETTINGS` folder and a `.crc` beside each EDF file. Each holds meaningless bytes. Nothing needs their real format, because nothing reads them.
- **A marker in every identifying field.** The patient and recording fields of every header hold a distinctive string, recorded in `answer.json`. It must never appear in the page, in what the page stores, or in anything the page exports.

## The cases

| Case | What it exercises |
|---|---|
| `plain-night` | one session, all five kinds of file, a handful of events at known times, and a Cheyne-Stokes period written the way a device writes one: a `CSR Start` and a `CSR End` in the `CSL` file, ten minutes apart. A correct reader draws them as **one** event lasting those ten minutes (Z, 2026-09-22), so `answer.json` carries the annotations as written and, separately, the events the page must show |
| `two-sessions` | a mask-off break: two sessions in one night, in one day folder |
| `after-midnight` | a session starting after midnight, filed in the *next* day's folder on purpose, so the answer proves the folder decides nothing |
| `crosses-the-cut` | a session running from before 6 in the morning to well after it. Its whole data belongs to the day it began in |
| `morning-nap` | a session starting between 6 in the morning and noon. **Not built. Closed by Z on 2026-09-21:** *"I think it is closed. The system covers it now. Go to bed at 5:59am it is the previous day's session. Go to bed at 6:00am it is today's session. Case closed."* The rule was never in doubt, and `dev/tests/day-boundary.js` already exercises it at every edge it has -- 05:59:59 to the previous day, 06:00:00 to that day, both daylight-saving changes, three time zones. The agent kept listing this as an open gap by pointing at the reader suite, which cannot see the cut move, while under-crediting the boundary test, which can |
| `bathroom-break` | one night's sleep in three sessions: a break of a few minutes across 6 in the morning, then a break of an hour and a quarter. All three would be one day under the break rule but for the last, which begins its own. **Not built. Proposed 2026-09-23**, the day Z set the rule. **The rule is not what is open.** It is in `src/card.js` and `dev/tests/day-boundary.js` exercises it at 33 points in three time zones -- a break of five minutes across 6 in the morning, a break of exactly an hour, of an hour and one second, of an hour and a quarter, a chain of three sessions, a chain broken in the middle, a chain reaching the middle of the day, a break across 6 on the morning the clocks go back, and a break after a session that has no flow. What is open is narrower, and it is two things a card would reach and that check cannot. **The moment the break is measured from**: `endOf()` takes `session.flowEnd`, which on a real card the reader works out from the flow signal's own span rather than from the files' -- and `day-boundary.js` supplies `flowEnd` itself, so a reader deriving it wrongly would leave all 33 checks passing. **And a session the rule actually decides**: `five-days` has one two-session night and `long-range` has eight, but in all nine the second session begins before 6, so the boundary alone already gives the same answer and the rule is never load-bearing in any card. **Both were built on 2026-09-24, and not here.** They are derived cards, in `dev/tests/cards/make-break-cards.js`, built from this card's shortest night into `dev/tests/out/` on every run: `bathroom-break`, five sessions carrying across 6 in the morning down a chain, still carrying at a minute to noon, and stopped by a session that begins after it, and `break-from-flow`, whose flow stops twelve minutes before its files do. The blocker recorded here for a day was wrong -- the answer does not need `cpap_day()` to know what came before, because each session's day is **written down** beside its stamp rather than computed. A generator that worked the day out with the rule would have been checking the reader against a second copy of the same rule |
| `empty-day` | a day folder with no files, and a gap of several days between two nights |
| `no-oximeter` | no `SAD` files, so the reader must cope with a kind that is missing |
| `five-days` | five CPAP days in a row, for a range selection and its summaries. The nights differ in start and length; one has no oximetry; one day holds two sessions, the second of which starts after midnight and is filed under the day before |
| `long-range` | a hundred nights over a hundred and five days, crossing a year's end, for the weekly, monthly and yearly views. **Agreed by Z on 2026-09-24.** No card before it could exercise them at all: the longest was `five-days`, whose five nights fall in one calendar week, so every grouping above daily collapsed to a single point and no grouped chart could be drawn or checked. This one gives each grouping something to draw -- a hundred days, sixteen weeks, four months and two years -- and its answer carries how many points each level must have, worked out from the nights rather than read back from the page. Five days in the span hold no recording, so the rule that a group is the mean of the nights it has is exercised rather than assumed. Seven nights begin after midnight, one of them at twenty past midnight on the first of January, which belongs to the CPAP day of the thirty-first of December: it is in the 2025 year group and the December month group, and a view that grouped by the calendar date would put it in the wrong one of each. Some nights hold a second session, after a break of more than an hour that still begins before 6, so the count of sessions differs between nights without depending on the break rule. **It carries no `BRP` and no `SAD` file, and its nights run two to five hours.** A period longer than a day opens no waveform, so leaving them out costs the case nothing; `PLD` is the only signal file here and it is written in full. What that buys is a card of about ten megabytes that builds in seconds and can be carried whole into a probe page, which a hundred nights of flow could not be |
| `on-and-off-leak` | one session whose leak goes on and off, so the time it ran above zero is not the time the machine ran. **Asked for by Z on 2026-09-21.** Every other case carries a leak that never reaches zero, so their total is bound to equal the recorded time and a reader that ignored every value would pass. This one holds several runs above zero, of different lengths and different levels, separated by runs at zero of different lengths. One run is at half a liter a minute, which counts, since PAPvault sets no threshold of its own; one reaches the end of the recording, where there is no sample after it; and the night begins at zero. The total in `answer.json` follows the rule Z set on 2026-09-20 -- a run lasts from the sample before it to the sample after it, less one step, which comes to its own samples times the step between them -- and it is a little over a third of the recorded time, so a reader returning the running time is wrong by a figure nobody has to squint at |
| `realistic` | five nights that look like nights, for someone to try the site with before they open their own card. **Asked for by Z on 2026-09-22 and shaped by Z on 2026-09-23.** It is scripted first -- what happened and when -- and every signal is a rendering of that one script, so the flow stops where an apnea is annotated, halves where a hypopnea is, flattens where an arousal follows a stretch of rising effort, and waxes and wanes through a Cheyne-Stokes period. The pressure answers events the way Z described: up at once after an obstructive apnea, a little after a hypopnea, never after a central one, and back down over an hour or more. It holds a handful of events a night, because it is meant to look like therapy that is working, and every word a card carries appears somewhere across the five. The nights differ from each other and only two of them hold a Cheyne-Stokes stretch. Everything it rests on is in `dev/synthetic/realistic-night.md`, fact by fact |
| `other-labels` | the short and translated label forms of `dev/formats/resmed.md`, including one with bytes outside ASCII. The reader reports which signals it did not find rather than guessing |
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
- **how long the leak ran above zero,** per session, in seconds, and for a case built from runs the start and length of each run above zero;
- **the events a correct reader draws**, which is not one per annotation: a pair of marks bracketing a period is one event spanning it. The answer carries both lists, so the parser can be checked against the file and the page against what it must put on screen;
- **the unit each signal is shown in**, where that is not the unit its header could spell. EDF gives a unit eight bytes, so a header says `bpm` where the page must say `breaths/min`;
- **per CPAP day:** which sessions belong to it, and the totals a summary must show;
- **the identifying marker,** which must appear nowhere in the page;
- **for `lies`:** what the reader is expected to report, per file.

## The summary figures

Decided by Z on 2026-09-19, for the top card over whichever period is selected. Each is arithmetic over what the device recorded, and none of them judges it:

- **hours of machine use** per CPAP day, from session start and end times;
- **the number of sessions** per CPAP day;
- **events per hour**, per CPAP day, kept apart by the device's own annotation text. Nothing is grouped into kinds of PAPvault's own, and nothing is summed across labels;
- **pressure**, its median and its 95th percentile per CPAP day;
- **leak**, its median and its 95th percentile per CPAP day.

So `answer.json` gains these per CPAP day, derived from how each case was built and never read back from the files. The cases in `out/` were generated before this was decided and do not carry them yet.

## Open

- **Which signal each of pressure and leak is taken from** when a session has more than one that could serve, since `Press.2s`, `MaskPress.2s` and `Press.40ms` are all pressures. Named as a gap rather than guessed. **Deferred by Z on 2026-09-21:** *"Currently we are not doing any extra analysis. We just display the data. Maybe for a future release we might. Not now."*
- **Nothing.** The leak case that stood here from 2026-09-20 was asked for by Z on 2026-09-21 and is built; it is `on-and-off-leak` in the table above.
