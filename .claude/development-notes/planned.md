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

## Making the page work on a phone

**Raised by Z on 2026-09-25**, from trying the page on an Android phone over the local network. Three things came out of it, and Z set the terms:

> Browser is half of the problem, but we need to work within the browsers' limitations.

> You are dismissing that it is not in our code! [...] If browser is working for most every website and failing to work with ours, it is not "browser's fault". Maybe we can circumvent the issues with our code.

So the question is mechanistic, in Z's words: **what processes run, one after the other, between one moment and the next.** Two intervals were named, and there is a third item and a fourth.

### What is known to happen, and where it is written

This is the sequence as the code has it, with what is verified here separated from what is not.

**From pressing Read Data to the browser's upload prompt.** The page's part is two lines: `folderPick`'s click handler calls `folderInput.click()` and then puts up the waiting box (`src/app.js`). Everything after that is the browser's, and it ends when `change` fires. What the browser must do in between is not verified here: a `webkitdirectory` input hands the page a complete `FileList`, and Firefox's prompt names a file count, which means the count exists before the prompt does. **Whether the browser enumerates lazily or eagerly, and what an Android file costs to enumerate, is a fact from outside this repository and needs a `dev/READING-LOG.md` entry before it is looked up.** What is ours in this interval is the *choice of input*: `webkitdirectory` asks for a whole tree, and what the tree holds is what the reader picked.

**From approving the upload to "Reading the recordings: 0 of n".** All of this is ours, and it is four steps:

1. `change` fires. The handler puts up the box saying "Looking through the folder.", then awaits `painted()` -- one animation frame and one turn of the event loop, so the words are on screen before the work starts.
2. `Array.prototype.map.call(folderInput.files, ...)` walks **every** file the browser handed over, reading `webkitRelativePath` from each. A card's non-night files are still walked here.
3. `PAPvaultCard.read()` calls `nightFiles()`, which classifies those paths as strings: it takes the `DATALOG/<day>/` shape, and it takes each file's **stamp from the file name**. No file is opened.
4. The loop's first `onProgress(0, entries.length)` sets the words the reader sees.

**And then the loop itself, which is where the file opens are.** `headerOf()` reads each night file **twice** -- `slice(0, 256)` to learn how long the header is, then `slice(0, need)` for the header. The hundred-night card holds 653 files, of which 324 are night files, so that is **648 reads before a single plot**. A three-year card is roughly 3,600 night files, so about **7,200 reads**. After that the events pass opens the event files again.

Measured on this machine, in Chromium, with the files held in memory: change to "Looking through" 25 ms, to "0 of 324" 14 ms, all 324 headers 377 ms, plots on screen 234 ms -- **650 ms in total**. That number is a floor and nothing else: these files were built in memory, and a phone's come through the system's document provider, where every open is a round trip. **The same measurement has to be taken on the phone before anything is concluded from it.**

### 1. The waiting

**What to find out**, in the order it would settle things:

- On the phone, the two intervals separately: picker to prompt, and prompt to "0 of n". Z has measured that the total grows with the size of the folder.
- Whether the second interval scales with the number of **night** files or with **all** files, which says whether step 2 above or the header loop is the cost.
- What the header loop costs per file there. It is 648 reads for a hundred nights, and halving it is a code change, not a browser one.

**What is already available to change, whatever the measurement says.** `headerOf` reads twice where one speculative read would usually do. The events pass opens files a second time. Neither is a browser limitation.

### 2. Choosing a range before reading

**Z, 2026-09-25:** *"Before the upload starts can we let user choose a range of dates to upload instead of the whole SD card. That can really speed things up."* Z agreed this is the right approach.

**Why it can work here.** `nightFiles()` already takes each file's stamp from its name, `20251120_222500_PLD.edf`, without opening anything. So the page can know which days a card covers, and how many files each day holds, **before it opens a single file**. A range then decides which files are opened at all.

**What it cannot do.** It cannot shorten the first interval. By the time the page can read a name, the browser has already enumerated the folder and built the list. Anything that shortens that interval has to reduce what the reader picks, not what the page reads.

**What it must not do.** `CLAUDE.md` is explicit that nothing about the machine's own filing decides anything, and that a session's times come from the file's name and header. Using the name to decide **which files to open** keeps that rule; using it to decide **when a session happened** breaks it. The margin the reading design already states -- a day either side of the range -- has to be part of the filter, or the day boundary and the break rule lose the neighbors they need.

### 2a. What was decided on 2026-09-26, after measuring

**A file selection was built and then removed.** With night files recognized by name rather than by the folder above them, a plain `<input multiple>` worked: six files with no path at all were read as a night. It came out again the same day. A picker's multi-select does not cross folders, so "choose the days you want" would have been one folder's files at a time, which is the folder pick with more steps. Z: *"this is not going to work [...] This is where we need to be honest."*

**What a reader is asked to do instead:**

- **A folder, at whatever level they like.** The whole card, or one night's folder inside `DATALOG`. That works now, and it is what makes a single night on a phone cost a second instead of minutes.
- **For a longer period on a phone, copy the days wanted into a folder of their own** and open that. It is an honest instruction rather than a mechanism that cannot exist, and it is in `docs/manual.md` and in the folder dialog.
- **On Chrome, the listing route**, which Z settled the same day: `showDirectoryPicker` is offered on Chrome for Android, listing 600 names took 526 ms on Z's phone, and a file is made only for a day that is asked for.

**Why nothing better exists for Firefox.** A page has four doors: a file input, a file input with `webkitdirectory`, drag-and-drop entries, and the File System Access API. On Firefox for Android the first two are the only ones open -- `showDirectoryPicker` is not offered in a secure context, and `webkitEntries` came back empty -- and both enumerate eagerly, at about 33 ms a file, before the page hears anything. A native application does none of this: it talks to the platform's own file APIs, keeps an index between launches and works in the background. That is a different kind of program, not a better page.

### 2b. An Android application, through F-Droid

**Decided by Z on 2026-09-26, for the future**, as the answer to what a page cannot do on a phone: walk a card lazily, remember what it has already read, and work on an archive of years without an upfront wait.

It is listed here so the decision is not lost, and nothing about it is designed yet. Two things about it are already clear from this project's rules rather than from any design: **F-Droid builds from source**, which suits a project whose whole claim is that every line can be read and rebuilt; and whatever it becomes, **the data still never leaves the device**, which is the promise the web page exists to keep.

### 3. The plots do not respond to touch

**Z, 2026-09-25:** *"I also finally loaded a dataset on the phone and the interactivity of the plots is not working at all."*

**Verified here, and it is complete.** `src/plots.js` binds `wheel`, `mousedown`, `mousemove`, `mouseup` and `dblclick`, and nothing else. There is no `touchstart`, no pointer event, and `src/style.css` has no `touch-action` anywhere. uPlot's own drag selection is bound to the mouse as well. So on a touch screen **nothing** is wired: no zoom, no pan, no double-tap to go back, and a drag on a plot scrolls the page.

What that turns into is a design conversation with Z, because a phone has fewer gestures than a trackpad and they collide with the page's own scrolling. The measured trackpad work in `gestures-on-a-plot.md` is the precedent for how to decide it: build the smallest version, put it in front of Z, and let Z judge by feel.

### 4. Firefox on Android

Z: *"Firefox browsers on Android are not usable. Don't blame the browser we need to find solutions."* So this is not a note saying which browser is at fault; it is the requirement that what we build works there. Every item above is judged on the phone, in both browsers, and a fix that works only in Chrome is not a fix.
