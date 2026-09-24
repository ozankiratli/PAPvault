# Platform traps

**This file is kept current.** It is appended to as traps are found, with a date on each entry, since a trap does not expire. It is one of the two exceptions to the dating rule in `README.md`.

Each entry is something that produced a wrong result once, with the symptom it showed and what to do instead.

## A zsh variable holding a command runs as one word

*Found 2026-09-18.* The shell here is zsh, which does not split an unquoted variable into words the way bash does. `C="chromium --headless ..."; $C --screenshot=...` looked for a program named by the whole string, and exited 127, command not found.

Use a shell function (`shot() { chromium --headless ... "$@"; }`) or an array, or write the steps as a bash script and run it with `bash`.

## The Edit and Write tools rewrite `\u` escapes

*Found 2026-09-19.* Writing a JavaScript escape such as `"\u263E"` in an Edit tool's replacement text put the character itself in the file, not the six ASCII characters of the escape. Writing `"\\u263E"` instead put two backslashes in the file, which JavaScript reads as a literal backslash followed by `u263E`, so the page would have shown the escape as text.

Neither form yields a single backslash. What worked was a one-line `sed` on that line, announced beforehand (`sed -i '25s/\\\\u/\\u/g' src/app.js`), followed by `od -c` on the line to see the bytes. After writing any escape, check the bytes; `grep -nP '[^\x00-\x7F]'` catches the first failure and not the second.

The Write tool does the same. When this file was created, its own first example above arrived as the moon character, and was put back with a `sed` that matched the character by its UTF-8 bytes (`sed -i '15s/\xe2\x98\xbe/\\u263E/'`).

## Headless Chromium ignores `--lang` for dates and times

*Found 2026-09-19.* Started with `--lang=de-DE`, headless Chromium on Linux still reported `navigator.language` as `en-US` and formatted times in 12-hour form, so a check of the page's locale default came back 12-hour for German and British English alike, and could not have failed. The locale `Intl` uses comes from the environment: start it with `LANG=de_DE.UTF-8` (and set `LANG` explicitly for any run whose output depends on the locale). Before trusting such a run, print `Intl.DateTimeFormat().resolvedOptions()` from inside the page.

## A probe page is a copy of the build it was made from

*Found 2026-09-19.* Probe pages are made by copying `dist/index.html` and adding scripts, so they hold the page as it was built at that moment. A screenshot of one made before the last `python3 build.py` showed the old text buttons after the icons had replaced them. Regenerate every probe page after each build, and check that it holds something only the new build has before looking at what it shows.

## Canvas text is not drawn in the color you asked for

*Found 2026-09-20.* A probe that reads a canvas looked for pixels whose color was exactly the color the page had filled its text with. It found the numerals `4`, `3` and `2` and reported that the `1` on the fourth bar was missing, when a screenshot of the same page showed it plainly. Chromium draws text with subpixel antialiasing, which gives each of the three channels its own coverage, so a thin glyph can have no pixel at the exact color asked for. A wider numeral has at least one fully covered pixel and matches; a `1` at eleven pixels may have none.

A filled rectangle does not have this problem: its interior is the exact color, and only its edges vary, and then only in alpha.

So match text by nearness rather than by equality -- the probe here takes any drawn pixel within 80 of the text color on every channel, which is far from the only other thing drawn in that area, the gridlines. Before trusting a pixel check that reports something missing, screenshot the same page and look.

## A headless screenshot comes back blank after a programmatic scroll

*Found 2026-09-20.* A probe scrolled the page with `window.scrollTo(0, 900)` and then the run was screenshotted to see the sticky bar over the plots. Every such capture was the page background and nothing else, at two virtual time budgets and from two different probe pages, while a `--dump-dom` run of the same page reported the scroll had happened and the layout was right. A capture taken without scrolling, of the same page, came out correctly.

Do not read a blank capture as a blank page. Measure the rendered geometry from inside the page instead -- `getBoundingClientRect()` for where something sits, `document.elementFromPoint` and `elementsFromPoint` for what is drawn on top of what -- or make the window taller than the content so that nothing has to scroll.

## `tee /dev/stderr` eats the log it is writing to

*Found 2026-09-20.* The test runner printed its build checksum with `python3 build.py | tee /dev/stderr | cut -d' ' -f1`, so the line would show in the log as well as being captured. Run in a terminal it looked right. Run as `run.sh > log.txt 2>&1` the log came back with its first four sections missing, replaced by a run of spaces, and began part way through the fifth.

`2>&1` makes stderr a duplicate of stdout, sharing one file offset. `tee /dev/stderr` does not write to that descriptor: it **opens** `/dev/stderr`, which on Linux is `/proc/self/fd/2`, and opening it gives a new file description starting at offset zero. Everything written before it is overwritten in place.

Print the line with `echo` instead, and take the field from the variable:

    said="$(python3 build.py)"
    echo "$said"
    first="${said%% *}"

The same applies to any `tee /dev/stdout` or `tee /dev/fd/N` in a script whose output is redirected to a file, which includes every CI log. **A run that passes is not evidence its log is complete** -- count the sections, or check that the first one is there.

## A Pages deploy started by a release was blocked by the environment, not by the workflow

*Found 2026-09-20.* `pages.yml` ran on `release: published`, its `build` job went green, and its `deploy` job was rejected:

> Tag "v0.0.1" is not allowed to deploy to github-pages due to environment protection rules.

That message is the whole of what was observed. The `github-pages` environment on that repository would not accept a deployment whose ref was a tag. **Whether that rule is GitHub's default or something the repository had, nobody here checked**, and the first version of this entry asserted it was the default, which was not established.

What follows from the message alone: a workflow run started by a release carries the tag as its ref, so if an environment will not accept a tag, nothing written in the YAML can make that deployment go through. PAPvault's answer was to stop deploying from a release at all and deploy from `main` instead, which is what PoolSeqFlow does and what Z asked for.

Two things made this hard to see. The run is not obviously a failure at a glance, because the job that does the work succeeded and only the last job stopped. And the symptom reported first was "the second workflow never triggered", which sends you looking at the trigger, the default branch and the token -- the three places a workflow genuinely fails to start. **When a chained workflow appears not to have run, confirm whether a run exists before reasoning about why it does not.**

## A poll counter inside a page under `--virtual-time-budget` counts virtual time, not progress

*Found 2026-09-21.* Every headless probe waited for the page with `setTimeout(step, 25)` and gave up after 1200 tries, which reads as thirty seconds of patience. It is not. Under `--virtual-time-budget` the browser advances its clock to the next pending timer as fast as it can, so those 1200 ticks are consumed almost instantly in wall-clock terms, **whether or not the real work behind them has finished**. Reading fifteen megabytes of base64 into File objects, parsing EDF and drawing canvases all take real time that virtual time does not wait for.

The symptom was a suite that failed about one run in three, on a different probe each time -- the two heaviest first -- and passed on a re-run. That is worse than a failure, because it teaches everyone to run it again rather than read it.

Two things to keep straight. The in-page counter is **not** the guard against a hang: the runner's `subprocess.run(..., timeout=...)` is, and that one is measured in wall clock. And a give-up from the counter means *slow*, not *broken*, so it must not be reported as a malformed result -- the message now says so.

The limits are 6000 polls against a 400-second virtual budget and a 600-second wall-clock timeout, which is roughly five times the headroom the marginal case needed. **A probe that polls needs its patience measured against the clock the work runs on**, and under virtual time those are two different clocks.

## A poll counter on virtual time gives up under load, 2026-09-22

Already recorded above as a trap; this is a second instance with a number attached. The range probe reported `GAVE UP No data loaded.` in one full-suite run, then passed **five times out of five** when run on its own. Nothing about the page had changed in a way that touches loading; what differs is that inside a suite run it starts moments after another headless browser, and `--virtual-time-budget` advances the clock to the next pending timer whether or not the real work behind it has finished.

So the in-page ceiling of 6000 polls, which is 150 seconds of virtual time, is a race against real work rather than a timeout. It was raised to 12000 in every probe, still well inside the 400-second virtual budget, with the 600-second wall clock left as the real guard. **Measure before adjusting one of these**: running the probe alone is what tells you whether the page is slow or broken, and it took five runs to be sure.

## A probe that waited for silence, when silence came first, 2026-09-22

Making the folder handler put a box on screen before it touches the file list changed nothing a reader would call behavior, and broke four probes at once. Each of them waited for the page to be ready like this:

    if (folderStatus.textContent.indexOf("Reading") === 0) { wait(); return; }

which reads as "wait until it has stopped reading" and actually means "wait until it is not saying it is reading". Those are the same thing only while the page starts reading in the same task that receives the folder. Once the handler yields once before starting, there is a moment when the folder has been handed over and nothing has been said yet, and a probe that begins in that moment finds an empty calendar. The step probe walked forty empty days and reported `LOOPED`; the range and events probes clicked at calendar cells that did not exist, got no range, and failed six checks between them with figures from the wrong day.

**The lesson is about what a readiness test is made of.** The absence of a message is not the presence of a result. Every one of them now waits for the result itself -- `document.querySelector(".calendar-day.has-data")`, a card with nights in it -- which is true only once there is something to click and false in that empty moment either side of it.

## A synthetic drag that uPlot never saw, 2026-09-23

*Found 2026-09-23.* A probe dragged across a plot with `new MouseEvent("mousemove", {clientX: ..., bubbles: true})` and the chart did not zoom. The events were reaching the element -- the page's own pan listener on the window ran, from the same dispatch -- so the dispatch was right and something downstream was dropping them.

uPlot's `mouseMove` opens with this:

    if (dragging && e != null && e.movementX == 0 && e.movementY == 0)
        return;

which is there for a Chrome bug that sends a stray mousemove after a mousedown. A constructed `MouseEvent` reports `movementX == 0` unless the init dictionary says otherwise, so **every** synthetic mousemove looked like that stray one and was dropped. Setting `movementX` to the step since the last event fixed it.

The reason this matters beyond uPlot: the check that a plain drag still zooms had been **passing on nothing**. It compared the span before and after a drag that never happened, and two unchanged numbers can be read as "nothing broke" instead of "nothing occurred". It was caught only by running the same probe against the page as it stood before the change, where the numbers should have differed and did not.

**A synthetic input event is not the input.** Anything that filters on a field a constructed event does not carry -- `movementX`, `isTrusted`, `pointerId`, `pressure` -- will silently ignore it. When a probe drives an interaction, run it once against a version where the interaction behaves differently and check the numbers actually move.

## requestAnimationFrame is starved under virtual time, 2026-09-23

*Found 2026-09-23.* Coalescing a burst of wheel events to one redraw is what `requestAnimationFrame` is for, so that is what the page used first. The probe then read the scale back 200 milliseconds later and found it unmoved, every time.

Frames were being produced -- a `requestAnimationFrame` loop counting them reported **4 for the whole probe**, against roughly eight waits of 200 milliseconds each. That is the whole of it: `--virtual-time-budget` advances the clock to the next pending *timer* as fast as it can, and frame production does not follow it. So virtual time makes timers nearly free and frames nearly absent, and the two clocks drift apart in the direction that makes a frame-scheduled callback look like it never ran. Making the probe wait on a frame instead of a timer did not rescue it either: four frames is not enough to spend one on each step, and the probe burned its budget and set no title at all.

The page ended up needing neither: the gesture that wanted coalescing -- a sideways two-finger swipe to slide the window -- was removed the same day, because making `preventDefault` conditional on the direction of each wheel event let Chrome latch the whole gesture to the page. The trap stands on its own all the same, for the next thing that wants a frame. For a chart redraw the two are equivalent -- the point is to stop redrawing ten charts per event, not to align with the compositor -- and only one of them can be driven in a check. **Where a frame and a timer would do the same job, the timer is the one this suite can see.** If a future change genuinely needs frame alignment, the honest thing is to write that the check cannot cover it rather than to keep a check that passes for the wrong reason.

The companion trap is the one above it: a probe that waits with `setTimeout` for work scheduled on a frame reads too early and reports a zero, which looks exactly like a feature that does nothing.
