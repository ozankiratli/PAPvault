# A night that looks like one

**Written 2026-09-23, against the tree at `a1d61ab` plus the generator work described here, uncommitted.** What the card *is* belongs in `dev/synthetic/realistic-night.md`, which is kept current and cites a source for every fact in it. This is how it got there.

## Why a realistic card at all, when realism was ruled out

Z, 2026-09-19, when the first synthetic cards were built: *"The generated data does not have to be realistic. I'll test with real data. On my end."* That held for four days and it was right: a case built to exercise a reader wants a signal whose answer is obvious, not one that looks like breathing.

What changed is who the data is for. Z, 2026-09-22: *"Provide a test data for potential users to test the website before using it. They will be able to download it and use it on the website to test it."* A card strangers download is published, so what it shows has to be defensible, and a sine wave under an apnea annotation is not.

## The shape of it: script first, render second

The night is a list of what happened and when -- an obstructive apnea of eighteen seconds here, a stretch of rising effort there, a period of Cheyne-Stokes at a quarter past three -- and every signal is a rendering of that one list. Flow stops where an apnea is annotated. Pressure answers the events. The rate, the tidal volume and the minute ventilation are arithmetic over the flow rather than channels of their own.

**That ordering is what lets a card be realistic and still carry an answer known by construction**, which is the rule every other case here obeys. `answer.json` is written from the script, not read back from the samples, so the parser and the reader can still be checked against it: 1,387 and 1,700 checks, no mismatches.

It also fixes something no other case has. Open `plain-night` and the flow under its apnea annotation is a sine wave, because the annotation and the signal were built separately and never had to agree.

## The first draft was wrong in kind, not only in degree

It was built from the facts in `realistic-night.md` and came out looking nothing like therapy. Z, 2026-09-23, sent three screenshots of a night of successful therapy, tampered with first and carrying no dates, and said: *"Your numbers are quite high, can be cut, the data I show you is successful therapy."*

Measured before and after:

| | First draft | After | What Z's night showed |
|---|---|---|---|
| Events an hour | 13.4 | 1.0 to 3.4 across five nights | a handful |
| Pressure | 8 to 16, median 13.6 | 6.0 to 10.9, median 6.0 | about 4 to 10 |
| How fast it came back | minutes | the better part of two hours | long slopes |
| Tidal volume | median 480 mL | median 373 mL | 350 to 450 |
| Minute ventilation | 6 to 9 L/min | median 5.5 | about 5 |
| Snore | a block at every arousal | silent 99% of the night | all but silent |
| Flow limitation | a few long stretches | many short spikes | many short spikes |

**Two of those were mistakes about what the channel is, not about its level**, and they are the ones worth remembering:

- **The rate spikes after an event, so it cannot be a windowed measure.** The first draft averaged the rate, the tidal volume and the minute ventilation over the minute before each sample. That smooths away the run of quicker, deeper breaths that follows an event -- which is exactly what puts the spikes on all three channels in a real night -- and it drops the rate to nothing during an apnea, which a real night does not do. They are reported breath by breath now: the breathing continues through an apnea and carries almost no air, so the rate holds while the volume collapses. That is the shape of the thing.
- **A two-second sample of a pressure that swings every breath has to be a mean over a breath.** The mask pressure swings by the whole of EPR every four seconds or so. A two-second mean lands on the inhale or the exhale by turns and draws a band across the whole swing; the plot showed a filled block where a real card shows a line between the therapy pressure and the EPR pressure. Averaging over a breath fixed it.

Both were found by looking at the rendered page beside Z's screenshots. Neither would have been found by reading the code, and neither is a level that could be nudged.

## What was taken from Z's screenshots, and what was not

The pictures were of Z's own therapy. **They are not in this repository and neither is any figure read off them.** What is written down, in `dev/synthetic/realistic-night.md`, is Z's direction in Z's words -- the same way Z's statement about breathing rate is recorded -- because a level Z sets is not a measurement of a night.

`CLAUDE.md` is what makes the distinction matter: nothing derived from real data goes into the repository unless Z has approved that item by name. The rule is about what gets written down and published, and it is kept by writing down the instruction rather than the observation.

## The one reading that rests on nothing

A plain `Apnea` is one the device did not classify, and what the pressure does after one is not stated in anything read so far. The generator answers it like an obstructive apnea, reasoning that the guide has AutoSet adjusting *"as a function of ... apnoea"* and names the central case as the exception that moves nothing (R-022) -- so raising is the rule and not raising is the special case.

That is a reading, not a fact. It is marked as one in the format file and it is the only one there. Z, 2026-09-23, asked for the events (*"Add A events too"*) and has not ruled on the pressure response.

## What it costs

Five nights of flow at 25 Hz is three million samples, and the generator writes them twice on every run of the suite. **The suite went from about a minute to two and a half.** The card is 13 MB on disk.

Both are worth knowing before the card grows. If either becomes a problem the lever is the number of nights carrying a waveform, not the realism: the waveform is the whole point of the card.
