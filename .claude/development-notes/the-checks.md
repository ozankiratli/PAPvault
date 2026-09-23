# The checks, and the day they became a suite

**Written 2026-09-20, against the tree at `6309c32` plus everything uncommitted after it.** What the suite *is* belongs in `dev/tests/README.md`, which travels with the checkout and is kept current. This is how it got here.

## There was deliberately none

`CLAUDE.md` said, from 2026-09-18: *"Z tests every change personally, and there is no automated test suite... a suite the agent writes and runs is the agent vouching for itself. A suite may come once there is enough synthetic data to build one on."*

That is a real position and it held for two days of work. What filled the gap in the meantime was a set of scripts in the agent's session scratchpad -- not in the repository, dying with the session. Every note written in that time reports measurements taken with scripts a reader could not re-run, and each one says so. Twice Z was asked whether they belonged in `dev/`, and twice it was left open, which was the right answer while the condition for a suite had not been met.

## What changed

Z, 2026-09-20, having gone through the page against a real card: *"We can build a test suite now, the website is ready to be shipped. I checked everything as best as I can. Confirmed it works."*

So the condition was met by Z's own testing, not by the agent deciding the scripts had become useful. That ordering matters: the suite exists because a person had already established that the thing works, and its job from here is to notice when that stops being true.

## What it is made of, and what each part was for

The scratchpad scripts moved into `dev/tests/` mostly as they were, since they had been written against the real problems as those appeared. Two were written new for the move:

- **`cards/derived.js`**, because the committed synthetic cases cannot fail on two of the rules the page now depends on. Every case is a night the machine stamped in one go, and every case's leak ramps from 60 to 120 L/min without ever reaching zero. So "a session is a stretch of flow" and "how long the leak ran above zero" had no case that could contradict them. It builds cards from the committed ones -- moving a file's stamp and its header start together, or writing physical zero over half a signal through the file's own calibration -- and the answers stay known by construction.
- **`page/run.py`**, which replaced nine separate probe scripts whose results the agent had been reading by eye. Turning an eye into an assertion is where the thinking was: the strip check now asserts that the rows are not inverted rather than that the first bar in row 0 is at pixel 75, and the event chart asserts palette order and falling lengths rather than 108, 81, 53, 27. A brittle number would have failed on the next honest change and taught everyone to ignore it.

## Two measurements from the day it was built

**Each check was broken on purpose and seen to fail.** Moving the day cut from 6 to 5 made `day-boundary.js` report 9 mismatches. Drawing the event bars bottom-up again made `page/run.py` report 2 failures, naming the palette order and the lengths.

**And one of those runs found a hole rather than confirming one.** With the day cut moved to 5 o'clock, `card-vs-answer.js` still passed all 822 of its checks. Every session in the committed cases begins at an hour where a 5 o'clock cut and a 6 o'clock cut agree, so the largest check in the suite is blind to the boundary moving. Only the 17-check boundary test can see it. That is exactly the gap the `morning-nap` case, proposed on 2026-09-19 and still not agreed, was proposed to close -- and it took breaking something to discover that the suite, on its own, would not have caught it.

## Where it runs

Z narrowed this three times in a row, which is worth recording because the first answer was the wrong shape.

The first attempt put the whole suite in CI, on every pull request. Z: *"OK don't run all the tests on github."* The second attempt kept the fast half in CI behind a flag. Z: *"We will test only if it builds there."* And then: *"All the other tests should be on this machine."*

So `.github/workflows/build.yml` asks a runner one question -- does the source still build, and build the same twice -- and nothing else. The suite runs here, before a change is handed over, and what it found is said with the change. The same narrowing took the grep and ASCII steps back out of `release.yml`, which now checks only things that are about the release itself: that the tag and `VERSION` agree, that the changelog describes the version, that the page carries the version it claims, and that the tarball rebuilds the page byte for byte.

The agent's instinct in all three attempts was to run more in more places. The instruction each time was the opposite, and the reason is not cost: a check that runs where nobody reads it is a check nobody acts on, and this project's testing has a person at the centre of it on purpose.

## Correction, 2026-09-21

The section above calls the day cut a hole the `morning-nap` case would close. Z closed that on 2026-09-21: *"I think it is closed. The system covers it now... Case closed."* The rule was settled long before, and `day-boundary.js` already exercises it at every edge, so there was no coverage gap -- only the observation that the largest check in the suite cannot see the cut move and the smallest one can. The agent had restated it as an open item several times, which is how a settled decision gets re-litigated by accident.

## The leak case, 2026-09-21

**Written 2026-09-21, against the tree at `c5ccbb0` plus the case and the two checks described here, uncommitted.**

Z asked for it: *"Let's do the leak synthetic case."* The hole it fills was named the day the figure was built, and it is the sharpest example in the project of a check that cannot fail.

**What was wrong.** `Dur.` is the one figure on the page that is not a reading of a signal: it is how long the leak ran above zero, by the rule Z set on 2026-09-20 -- a run lasts from the sample before it to the sample after it, less one step, which comes to its own samples times the step between them. Every synthetic case carried a leak that ramps from 60 to 120 L/min and never reaches zero. On such a night the right answer *is* the recorded time, so a reader that ignored every value and returned how long the machine ran would have passed every check in the suite. The rule had no case that could contradict it.

**What the case holds.** `on-and-off-leak` is one five-hour night, in `dev/synthetic/resmed.py`. Its leak is built run by run: twelve runs, six at zero and six above it, alternating, no two of the twelve the same length and each of the six levels its own. The night begins at zero; the last run reaches the end of the recording, where there is no sample after it; and one run is at half a liter a minute, which counts, since PAPvault sets no threshold of its own and a reader that had quietly adopted one would be wrong by three minutes. It comes to 7,080 seconds of 18,000 -- 118 minutes of a five-hour night -- so a reader returning the running time is out by an hour and a half.

The generator writes the total and each run into `answer.json`, and refuses to write a card whose runs and whose answer disagree: it checks that as many samples came out above zero as were asked for, so a run asked for above zero whose level rounded to digital zero would stop the build rather than quietly become part of the answer.

**Where it is checked.** Three places, and only one of them can see the rule itself change:

    node dev/tests/card-vs-answer.js .        the total, and every run against where the card put it
    node dev/tests/cards/derived.js .         the same rule at every record boundary
    python3 dev/tests/page/run.py .           the Leak box, read out of the rendered page

The first two add up samples above zero themselves, which means they re-implement the rule they are checking; they would catch a reader that misread the file, not a page that changed its mind about what counts. The third reads what the page worked out.

**Both new checks were broken on purpose.**

| The break | What it reported |
|---|---|
| `leak.y[i] >= 0` in `src/app.js`, so a sample at zero counts as leaking | the leak probe failed twice and printed `Dur. 300m`, the whole night. The day and range probes stayed green |
| the reader's zero shifted one digital step, in `src/edf.js` | `card-vs-answer.js` reported 169 mismatches, among them the total, the samples either side of every run, and the leak having run all night |

The first line is the case earning its keep. With every other night's leak never reaching zero, no other probe in the suite can tell `> 0` from `>= 0`; this one fails immediately and says what it saw.

Nothing in `src/` changed. `git status` at the end of the work shows the generator, the two checks, the case file, the checklist and this note, and nothing else.
