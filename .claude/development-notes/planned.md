# Planned

**This file is kept current.** It holds work Z has decided on but that has not been built, so that a decision made in conversation is not lost between sessions. An item leaves this file when it is built, and what it becomes is written up in a note of its own.

It is a third exception to the dating rule in `README.md`, which still says there are two. **That sentence needs correcting, and so does the list in `CLAUDE.md`** -- raised with Z rather than changed unasked.

Nothing here is a commitment to build. An item is what Z asked for, in Z's words where there are any, with whatever is already known about what it would cost.

## A tutorial page

**Decided by Z on 2026-09-24, for after 0.0.2.** It grew out of asking where to keep synthetic data so someone could try the page without a card of their own, and it replaced two smaller ideas: a downloadable sample card, and a *Load Test Data* button on the main page.

Z, on what it is:

> If we are going to build a tutorial page it is after 0.0.2. [...] the page should say TUTORIAL at the top and when it ends it should go back to the original landing page. Tutorial should not allow data upload or anything.

> No tutorial shows where to click, how to navigate. to load data. And how to see what the system shows.

So what it teaches is **how to use the page**: where to click, how to move around, how a person loads their own data afterwards, and what the page puts on screen. That last clause is the line to hold. `CLAUDE.md` says PAPvault displays and does not conclude, and a tutorial drifts toward interpretation in one sentence. It explains what the page *shows*, never what a number means about anybody's health, and where a figure's meaning needs saying it points at `docs/manual.md`, which is authoritative. Two documents explaining the same figure drift apart; that has already happened twice in one day with check counts and with a logo.

**What is settled**

- It is a separate page, not a button on the main one. A card baked into `index.html` is paid for by everyone, including the person who came to open their own data and the person downloading the offline file.
- It says **TUTORIAL** at the top, so nobody mistakes the synthetic data for a recording.
- It **takes no data**. No folder picker, no file input, nothing to upload. It shows how loading works without doing it.
- It ends by returning to the ordinary landing page.

**What is known about building it**

- The page cannot fetch the card. The Content-Security-Policy is `default-src 'none'` and the browser enforces it, so the data has to be inside the page as text. That is not a limitation to work around; it is the promise.
- The way in already exists. `showChoice(items)` in `src/app.js` takes a plain list of `{file, path}`, and it is the only door into the reader. The folder picker builds that list from `folderInput.files`; the tutorial would build the same list from bytes already in the page. The page probes in `dev/tests/page/` have done exactly this fourteen times a run since 2026-09-20.
- The prose can go through the machinery the manual already uses. `render_manual()` in `build.py` turns a small Markdown subset into navigation and panes, so a `docs/tutorial.md` needs no new renderer. **Prose in a reviewable Markdown file, not choreography in JavaScript**: a stepped tour with callout positioning, step state, focus handling and responsive behaviour is a feature in its own right, in a page whose selling point is that every line of it is readable.
- Weight, measured 2026-09-24. Flow costs about **360 KB an hour** and every other signal together about **32 KB an hour**. The `realistic` card is 12.8 MB raw and 6.5 MB gzipped; `long-range`, whose signals are smooth, is 11.8 MB raw and **0.1 MB** gzipped. So a card built for the job -- one night with flow, a handful without -- is a megabyte or two, and `long-range` already proves a card can leave the waveform out entirely.

**Open**

- Which card, and how many nights. Z, on the existing one: *"your realistic data does not look that realistic LOL."*
- Every synthetic file carries `SYNTHETIC-DO-NOT-DISPLAY-7Q4Z` in its patient and recording fields, so that a check can fail if it ever reaches the screen. In a card handed to the public that reads as a test token rather than as a card that was made up on purpose.
- Only Chromium is on the machine these checks run on, so nothing about the tutorial has been tried in Firefox or Safari.
