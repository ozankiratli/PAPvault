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
| `policy.py` | the Content-Security-Policy in the built page: every directive says exactly what it must, no directive carries `'unsafe-inline'`, `'unsafe-eval'`, a nonce, a scheme or a wildcard, the policy arrives before the first style and script, every inlined element is hashed and every hash belongs to an element, the page loads nothing of its own but a `data:` URI, and the frame check and referrer policy are present. **34 checks** |
| `outbound.py` | that nothing leaves the page and nothing could: a plain load watched with Chrome's own network log must request exactly one URL and resolve no hostname, and a probe that tries eighteen ways to send a loaded card's data to an outside host must be refused by the policy every time, with the log showing no request and no DNS lookup. **11 checks** |
| `page/run.py` | the built page driven in a browser: both views, the event strip's pixels, the event chart's order and labels, the wheel, the legend, the manual's groups, the landing page, the sticky bar, the calendar's day buttons, and the identifying marker reaching neither the rendered page nor local storage. **66 checks** |

## How the derived cards work

Every case in `dev/synthetic/out` is a night the machine stamped in one go, with a leak that never reaches zero. Real cards are not like that, and two rules had no case that could fail on them. `cards/derived.js` therefore builds cards from the committed ones: it moves a file's stamp and its header start together, or writes physical zero over half a signal through the file's own calibration. The answers stay known by construction, because what was changed is known.

They are built into `dev/tests/out/`, which git ignores, and rebuilt on every run.

## Each check was shown to fail

A check that cannot fail is not a check. These were each broken on purpose and seen to fail:

- moving the day cut from 6 to 5: `day-boundary.js` reported 9 mismatches;
- drawing the event bars bottom-up again: `page/run.py` reported 2 failures, naming the palette order and the lengths;
- adding `'unsafe-inline'` to the policy in `build.py`: `policy.py` reported 4 failures, from four independent directions -- the directive holding something that is not a hash, the forbidden token, a hash with no element, and the counts disagreeing;
- naming the card's folder with the marker: the marker check failed and pointed at `folder-status`;
- opening the policy with `connect-src https:`: `outbound.py` reported 3 failures, and the network log carried the outside host's URL and its DNS lookup -- the attempt really did leave. `policy.py` catches the same edit from the other side, by reading the directive;
- the earlier ones are recorded where they were found, in `.claude/development-notes/drawing-the-plots.md`.

**One of those runs is worth keeping in mind.** With the day cut moved to 5 o'clock, `card-vs-answer.js` still passed all 822 checks. Every session in the committed cases begins at an hour where a 5 o'clock cut and a 6 o'clock cut agree, so the reader suite cannot see the boundary move at all; only `day-boundary.js` can. That is not a gap in the suite, though: `day-boundary.js` exercises the rule directly, at every edge it has. It is a fact about which check earns its keep -- the smallest one here is the only one that can see the cut move.

## The marker check, and what it deliberately does not assert yet

Every synthetic card carries `SYNTHETIC-DO-NOT-DISPLAY-7Q4Z` in each field that would name a person or a machine. `page/run.py` now searches the whole rendered document and all of local storage for it, which passes: those fields live in EDF header bytes 8 to 167 and in `Identification.tgt`, and PAPvault reads neither.

It does **not** cover the name of the folder the card came from. That name is shown, on purpose: Z settled it on 2026-09-21 by saying what the page does rather than changing it, since the name is what tells a reader which folder they actually opened. `CLAUDE.md` and the manual both say so now, including that it goes along with a screenshot of that dialog. Running the probe with the marker as the folder name -- `python3 dev/tests/page/make-marker-probe.py . <out> SYNTHETIC-DO-NOT-DISPLAY-7Q4Z` -- makes the check fail and names `folder-status`, which is how it was shown to be able to fail, and which would be the standing check if that decision ever went the other way.

## Hand tools, which `run.sh` does not call

Two scripts here assert nothing. They print what `src/card.js` makes of a card, which is what you want when a real card is behaving in a way no check explains. They were written while working out what a session is, and they are kept because that question will come back.

    node dev/tests/cards/sessions-of.js . <card dir> [expected count]
    node dev/tests/cards/samples-of.js  . <card dir>

The first lists every session with its day, its start and end, its kinds of file, and which stamps it was built from. The second loads each session and prints how many samples and how much span each signal came out with, which is how a dropped file shows up. Neither is in `run.sh`, so neither can fail a run.

**Two more like them are not here.** `card-shape.py` and `session-gaps.py` printed the shape of a real card -- how many recordings a day folder holds, how long the gaps between them are, what a session count would be at each threshold -- from file names and headers only, with no date and no value in the output. They lived in a session scratchpad, which is not durable, and they are gone from this machine. If a real card needs diagnosing again they belong here, next to these two.

## What it does not cover

- **Anything about a real card.** Only Z has one, and no real data ever reaches these.
- **Whether a figure is the right figure.** The suite checks that the reader agrees with the generator. Both were written here, so where a fact came from one source, the suite cannot be the check on it -- `dev/READING-LOG.md` says where each fact came from.
- **Oximetry**, which is turned off and has no card to test against.
- **How it looks.** Layout is checked only where it can be measured: that a stack shares one plotting area, that a count sits to the right of its bar, that the sticky bar is drawn over the plots. Whether it reads well is Z's eye.
