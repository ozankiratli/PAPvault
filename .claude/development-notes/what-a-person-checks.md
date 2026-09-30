# What a person checks

**Written 2026-09-29, against the tree at `cfacb45`.** `dev/CHECKLIST.md` had grown to 32 entries, each with a paragraph of reasoning. Z, reading it:

> This file is insane! Not humanly anymore. We need to automate a lot of it. Everything that can be recovered in text should be tested with the suite. [...] What the human needs to do should be limited to how things are rendered and if they look as they should, if the data is correctly represented on the website etc. We should divide the work between AI and human in the right way.

And on what the list should then look like:

> The checklist must only contain what I check manually. Anything that can be checked automatically must be automated and removed from this list completely. The checklist should look like a checklist.

## The division

**A machine answers what can be recovered from text, bytes, computed styles, the DOM, a network log or a checksum.** That turned out to be most of it, including things that read like judgment: whether a color is legible is a ratio, whether a bar is reachable is `elementFromPoint`, whether a setting survives a reload is a reload.

**A person answers two kinds of question.** The first is what only a real card can settle, because no check in this repository has ever seen one: does the page's account of a card match the card, does a night you remember come out as one night, does an event sit where the breathing stopped. The second is judgment: does it look right, does it feel right, is the manual still true.

**Where a machine check and an eye overlap, the eye can stay** -- but only where the thing is seen before any check runs. `oximetry-off` is kept for exactly that reason, at Z's word: *"The suite checks this and it can stay for this one because it is a fail safe of a visual."*

## What was automated out of the list, and into what

| was | is now |
|---|---|
| `headers`, `policy-blocks`, `no-outbound`, `rebuild` | `dev/tests/live.py`, run once after a release from `dev/RELEASING.md` |
| `vendored` | `dev/tests/vendored.py` in `run.sh` |
| `framed` | the `frame` probe, which frames the built page and reads what is inside it |
| `sticky-bar` | the `sticky` probe: the bar's box after scrolling, and what the pointer lands on at its middle |
| `contrast` | the `contrast` probe: the pairs a reader sees, in both themes, as ratios |
| `shared-origin`, `time-format`, half of `oximetry-off` | the `settings` probe, which stands in front of every read of a file and counts what is kept |
| `calendar-select` | the `calendar` probe: seven states, what the grid marks and what the bar says at each |
| `landing`, `manual-nav`, `calendar-step`, `day-plots`, `flow-detail`, `event-colors`, `summary-plots`, `averaging`, `narrow-*`, `touch-gestures` | probes that already existed |

Eleven entries are left, and two of those are "look at it" and "use it".

## Two things the automation found while it was being written

**Storage held one key, not three.** The hand check said *"There must be exactly three keys"*; after reading a card there is one, because the chart choices are only written once changed. A person had been reading that sentence and seeing what they expected.

**The oximetry file is opened.** Its header is read -- that is how the file is placed in the night it belongs to -- and its samples never are. `dev/CHECKLIST.md` and `docs/manual.md` both said no oximetry file is opened, which was not true. The wording was corrected rather than the code, and the reason it is off at all is now recorded as Z gave it: ResMed records oximetry only with an oximeter of its own, and no compatible one could be found to buy.

## What the list is not

It is not the record of a release: that is `dev/VERIFICATION.md`. It is not the reasoning behind any check: what a check protects, and why it is worded the way it is, belongs here or in the note for that feature. The list itself is a list.
