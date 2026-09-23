# Events the machine did not call

**Written 2026-09-22, against the tree at `c5ccbb0` plus the uncommitted work of that day.** Nothing here has been built, and this note exists so that nothing is built from it by accident.

## What Z asked for, and what it is not

Z, 2026-09-22: *"One thing for our own research but not to implement. I want to investigate the potential events (including the ones shorter than 10s) that the machine does not call, for any reason. This is purely research oriented."*

**So this is a question to look into, not a feature waiting for a slot.** A later session reading this note should treat "not to implement" as the operative half of the sentence. If PAPvault ever marked a dip in the flow as an event, it would be declaring something the device did not declare -- which is the one thing `CLAUDE.md` rules out from the first day, under *It displays; it does not conclude*: *"We will not make any conclusions beyond what the PAP machine declares."* Research can find the dips. Only Z can decide that finding them is something the product does, and that decision would need its own argument, not this note as a precedent.

## Why there is something to find

The machine calls an event by its own rule, and the rule has a floor. From ResMed's clinical guide (`dev/READING-LOG.md`, R-022): *"An apnoea is when the respiratory flow decreases by more than 75% for at least 10 sec. A hypopnoea is when the respiratory flow decreases to 50% for at least 10 sec."* The AASM's general rule has the same ten-second floor with different depths, 90% and 30% (R-023).

Two kinds of thing therefore never get an annotation:

- **Too short.** A flow that stops for six seconds and resumes is nothing to the rule, whatever it looks like.
- **Too shallow.** A drop of 40% held for a minute is not an apnea by either rule and not a hypopnea by the machine's.

And the evidence is on the card either way, because the flow is recorded at 25 Hz whether or not anything is written about it (R-022, and it is why `Flow.40ms` is the signal it is). A night's annotations are the machine's *summary* of a recording PAPvault already holds in full.

## Where it will live, when it happens

Z, 2026-09-22: *"We will build an R based research module. Again no assertions, nothing. Keep it as an idea. I'm not ready for that research yet."*

So it is **a module in R, beside the page and not inside it** -- which settles the thing this note was written to protect. Nothing a research module finds can reach what a reader sees unless Z later decides it should, as a separate decision with its own argument. The page stays what it is: it draws what the device recorded and repeats what the device declared.

**And it is not started.** No module, no script, no case, no measurement. The two routes below are here because naming them costs nothing and because the first thing anyone would otherwise do is reach for real data.

## How it could be investigated without breaking the project's own rules

**Not on a real card, in this conversation.** `CLAUDE.md` is unconditional: real data never enters the agent's context, because the context is not local. That rules out the obvious approach -- point something at Z's card and count what it finds. Two routes remain.

1. **Z runs it locally.** A script over Z's own card, on Z's machine, with Z's go-ahead, whose output is a verdict and never a per-night value. That is the only route that touches real breathing.
2. **Synthetic data with the answer built in.** `dev/synthetic/resmed.py` already builds a night from a script of what happened. It could build a night holding dips that are deliberately below what the machine calls -- an eighty percent drop lasting six seconds, a forty percent drop lasting a minute -- and annotate none of them. Then any method can be measured against an answer known by construction: it found four of the five, and invented one that was not there.

Route 2 is where the agent can be useful, and it is also the honest one: a method that has never been measured against a known answer is an opinion. Route 1 is what would say whether the thing is real on real breathing.

## What would have to be decided before any of it means anything

**What counts as an event the machine did not call.** A drop of what depth, held for how long, measured against what baseline. Until that is written down, "the machine missed something" is not a claim that can be true or false -- every recording contains arbitrarily many small dips, and a method with a loose enough threshold finds thousands of them and is useless. The two published rules (R-022, R-023) are the obvious yardsticks to vary from, not to adopt.

**What the answer would be for.** Knowing that a night held eleven six-second dips is either interesting or noise depending on a question nobody has asked yet. That question is Z's.
