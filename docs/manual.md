# Using PAPvault

## Getting started

PAPvault shows what your PAP machine wrote to its SD card. It runs in your browser, and your data stays on your own computer or SD card.

1. Put the card in your computer, or use a copy of it.
2. Open **Open Folder** in the top bar, then choose the card's folder or drag it onto the box.
3. Pick a day in the calendar. Click a second day for a range.

Nothing is uploaded, because there is nowhere to upload it to. PAPvault opens the folder and reads it here, in your browser.

Reading the data inside the files is not built yet. Today the page lists what it found in the folder and opens none of it.

## Who PAPvault is for

PAPvault is for anyone who wants to look at their own therapy data without handing it to anyone, and without installing anything. Put the card in, open the folder, see your night. That is the whole idea.

It is deliberately not comprehensive. It shows what your machine recorded, for the nights you pick, and it stops there. It keeps nothing between visits, it has no account, and it makes no judgment about what the numbers mean.

If you want more, install [OSCAR](https://www.sleepfiles.com/OSCAR/). It reads more machines, keeps years of data, and analyzes them far more deeply than a page like this can. It runs on your own computer and it respects your privacy, which is why this manual points you to it rather than around it. PAPvault is not trying to compete with OSCAR: it is the quick look you take when installing software is not what you want today.

## Days and sessions

A day here runs from noon to noon, and is named by the date it began. A night that starts on the 18th and ends on the 19th is the 18th.

A session is one stretch with the mask on. Each session belongs whole to the day it began in, so a nap that runs past noon still counts in the day it started.

Choosing one day shows that day in detail. Choosing a longer period shows summaries.

Every time shown is the time your machine recorded. Machines keep their own clock and store no time zone, so a time is whatever the machine thought it was.

## What it never touches

- **Nothing leaves this page.** There is nowhere to send it: the page's security policy forbids every outbound connection, and the browser enforces that rather than trusting us.
- **Nothing is collected.** No analytics, no counts, no error reports.
- **Only the night's recording is read.** Files that hold something else, such as the machine's summaries, its settings or its identification file, are never opened.
- **Nothing identifying is touched.** The files carry fields naming the person and the machine. PAPvault steps over them, and never shows or keeps them.
- **Your browser's own dialog may use the word "upload".** That is the browser's wording for letting a page open a folder, and it is why PAPvault never uses the word itself. Nothing is sent anywhere.
- **The host still sees you.** GitHub Pages logs the address of every visitor, and no page can prevent that. Download the single file and open it offline if you would rather not be seen at all.

## Machines it reads

ResMed machines: the S9, and the AirSense and AirCurve 10 and 11.

Only the AirSense 10 has been checked against a real card. The others are read the same way, but their field names were taken from OSCAR's source and nobody here has tested them on a machine. If a signal is missing, PAPvault says so rather than guessing.

Another machine can be added once there is data to test with. A report, and a copy of a card, real or made up, is how that starts.

PAPvault does not replace OSCAR, the desktop program for the same data. For keeping years of data and studying them deeply, OSCAR is the better tool. PAPvault is for looking at a night without installing anything.

## Where the facts come from

- The **EDF and EDF+ specifications**, published standards, for how the files themselves are laid out.
- My own **R prototype**, which read an AirSense 10 card in 2024, for which files are read and how each sample and event is given its time.
- **OSCAR's source**, for the names ResMed gives its signals and for how files and folders are named.

Every source is listed in `SOURCES.md` in the repository. Every read of one is recorded in `dev/READING-LOG.md`, before it was made, with what was taken from it and what was left alone.

# How it was built

## History

> I want a reviewer to look at this and say that yes, AI agents can be used responsibly when what you are building is about someone's health.

I wrote the first version of this in early 2024, in R, by putting my own SD card in a reader and looking at what was on it. That work is where the understanding of these files comes from: which files a night is in, what the signals are called, how a sample gets its time. It ran as a small application on my own machine, and then I left it alone.

In September 2026 I picked it up again as a web page, so that it needs nothing installed. That is where an AI agent came in, and it came in after the format was understood rather than before. The design decisions, and every test against real data, are mine.

This page is built on three things: the published EDF standard, my own 2024 code, and OSCAR's source for the names ResMed gives its signals.

## The rules

The agent works under written rules, kept in `CLAUDE.md` in the repository. They are public for the same reason this page is.

- **No real data reaches the agent.** Reading a file into its context would send that file to a company's servers. A tool whose whole promise is that your data stays with you cannot be built by sending mine elsewhere, so everything the agent works against is generated.
- **Knowledge, never code.** Nothing from another project is copied or translated into this one. What may be taken is where the night's data sits and what it holds, never how another program reads it.
- **Every outside read is named, recorded, cleared and done,** in that order. The agent writes down what it wants to open and what it is looking for, I clear it, and only then does it read. That record is `dev/READING-LOG.md`, and each entry was written before the read, not after.
- **The agent never commits and never publishes.** I review the work as it lands, commit what I have read, and push it myself.
- **There is no automated test suite.** I test every change myself, on real data, on my own machine. `dev/CHECKLIST.md` says what is checked and what counts as a failure, and `dev/VERIFICATION.md` is what I found when I checked.
- **The page displays; it does not conclude.** No scores, no bands, no advice.

## When it went wrong

Twice so far, and both are written down in the repository.

**The one that mattered.** To build test data the agent needed details the standard does not fix, such as what ResMed calls each signal. It went to OSCAR's source and read the reader itself. I had already warned about leaning on OSCAR, and I stopped it. The problem was not only that another project's code was open: OSCAR was quietly becoming the authority on how my tool should behave. We rewrote the rule that day, and the agent's own account of why it happened is in `.claude/development-notes/other-projects.md`.

**The smaller one.** While surveying which machines exist, agents reported a sampling interval as though it were a rate. Checking their claims against the source caught it; a number wrong by a factor of forty would otherwise have gone into the notes. Since then an agent's report is treated as a draft, never as a finding.

Both are published because a record that shows only the parts that went well is evidence of nothing.

## What carries elsewhere

This is a small project, but the arrangement is not specific to it.

- **Write the read down before making it.** Written afterwards it is a summary. Written first, it is a decision, and anyone can check it was kept.
- **Keep reading and writing apart.** Code is written from notes, in a session that never had the other project's code in front of it.
- **Cite a fact to a commit,** not to a project. Projects move; a commit does not.
- **One source cannot be both a fact and the check on it.** Where a single project is all there is, this manual says so, and that machine is not claimed as supported.
- **With health data, ask what you can avoid reading.** Not being nosy turned out to be a design rule rather than a slogan: it decides which files are opened at all, and which fields are stepped over.
- **Responsibility does not move.** An agent wrote much of this code and much of this text. I read it, corrected it and published it, so it is mine.

## Checking it yourself

- The page is one file. Read its source in your browser.
- Rebuild it from the repository with `python3 build.py`, and compare the checksum it prints with the published one.
- `dev/CHECKLIST.md` is what gets checked before a release. `dev/VERIFICATION.md` is what I found when checking.
- Open your browser's network panel and use the page. Nothing should appear in it.
