# The checks

    dev/tests/run.sh              everything
    dev/tests/run.sh --no-page    everything but the headless browser

Needs `python3`, `node` and a chromium. Nothing from a package manager, and nothing here reaches a network.

**These run here, on the machine the change was made on.** Z, 2026-09-20: *"We will test only if it builds there. All the other tests should be on this machine."* A GitHub runner is asked one question, in `.github/workflows/build.yml`: does the source still build, and build the same twice. Everything below is run before a change is handed over, and what it found is said with the change.

**This does not decide whether a release is good.** `dev/CHECKLIST.md` is what decides that, and a person runs it against a real card. What this does is notice when something that used to work has stopped, which is the part a person cannot do after every change. It was built on 2026-09-20, when Z judged the page ready to ship and asked for it; before that there was deliberately none, because a suite the agent writes and runs is the agent vouching for itself.

## What each part proves

| Part | What it would catch |
|---|---|
| `no_markup`, `ascii_only` in `run.sh` | a sink that lets a file's text become markup, or a byte outside ASCII in what ships |
| `deterministic` | a build that does not give the same bytes twice, which would make the published checksum meaningless |
| `shows_its_version` | a page that claims a version it was not built as |
| `synthetic_cards` | a generator that does not write the same card twice, which would mean its answers described nothing |
| `edf-vs-answer.js` | the EDF parser against the generator's own answers: headers, units, intervals, sample counts, sample values, every event. **665 checks** |
| `card-vs-answer.js` | the card reader the way the page uses it: sessions, their ends, CPAP days, kinds, signals with their sample times, events, the day-by-day grouping, and the identifying marker never reaching the page. **822 checks** |
| `day-boundary.js` | the 6 o'clock cut at every edge it has, in three time zones and across both daylight-saving changes. **17 checks** |
| `cards/derived.js` | the rules the committed cases cannot exercise: a session being a stretch of flow, a file with no flow never making a night nor moving one, two files of one kind in one session keeping both their samples, and how long the leak ran above zero. **17 checks** |
| `page/run.py` | the built page driven in a browser: both views, the event strip's pixels, the event chart's order and labels, the wheel, the legend, the manual's groups, the landing page, the sticky bar, and the calendar's day buttons. **63 checks** |

## How the derived cards work

Every case in `dev/synthetic/out` is a night the machine stamped in one go, with a leak that never reaches zero. Real cards are not like that, and two rules had no case that could fail on them. `cards/derived.js` therefore builds cards from the committed ones: it moves a file's stamp and its header start together, or writes physical zero over half a signal through the file's own calibration. The answers stay known by construction, because what was changed is known.

They are built into `dev/tests/out/`, which git ignores, and rebuilt on every run.

## Each check was shown to fail

A check that cannot fail is not a check. These were each broken on purpose and seen to fail:

- moving the day cut from 6 to 5: `day-boundary.js` reported 9 mismatches;
- drawing the event bars bottom-up again: `page/run.py` reported 2 failures, naming the palette order and the lengths;
- the earlier ones are recorded where they were found, in `.claude/development-notes/drawing-the-plots.md`.

**One of those runs is worth keeping in mind.** With the day cut moved to 5 o'clock, `card-vs-answer.js` still passed all 822 checks. Every session in the committed cases begins at an hour where a 5 o'clock cut and a 6 o'clock cut agree, so the reader suite cannot see the boundary move at all; only `day-boundary.js` can. That is the gap the proposed `morning-nap` case in `dev/synthetic/resmed-cases.md` would close.

## What it does not cover

- **Anything about a real card.** Only Z has one, and no real data ever reaches these.
- **Whether a figure is the right figure.** The suite checks that the reader agrees with the generator. Both were written here, so where a fact came from one source, the suite cannot be the check on it -- `dev/READING-LOG.md` says where each fact came from.
- **Oximetry**, which is turned off and has no card to test against.
- **How it looks.** Layout is checked only where it can be measured: that a stack shares one plotting area, that a count sits to the right of its bar, that the sticky bar is drawn over the plots. Whether it reads well is Z's eye.
