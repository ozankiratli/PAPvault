# Working on PAPvault

PAPvault is a web platform for viewing PAP therapy data (CPAP, APAP, BiPAP) interactively, where **the data never leaves the user's machine**. It revives an abandoned R/Shiny prototype, which sits untracked in `CPAP_old/`. It is a single page in HTML, CSS and JavaScript, served from GitHub Pages and possibly also offered as one file that runs offline (Z, 2026-09-18). A **CPAP day** runs from 6:00 on its date to 6:00 on the next calendar day, and is not a calendar day. Every day the page shows or selects is a CPAP day. That holds for every machine, whatever the machine does itself. Z, 2026-09-19: *"The day decision is final, not just for ResMed."* The cut was at noon from 2026-09-18 until later on 2026-09-19, when Z moved it to 6 in the morning so that a nap starting after 6 belongs to the day it happens on rather than to the night before. Z's words on both are in `.claude/development-notes/the-day-boundary.md`.

PAPvault is not a replacement for OSCAR, the open-source desktop program for the same data. Z, 2026-09-19: *"Again. The aim is not to replace OSCAR. We can even direct people to use it for long term storage. This is to skip that requirement."* PAPvault is for a person who wants to look at their data without installing anything.

**PAPvault reads ResMed machines, and for now only those**: the S9, and the AirSense and AirCurve 10 and 11. Z, 2026-09-19: *"Then, we will support only ResMed for now. I will try to put my hands on some other data personally, until then we will have it as development note."*

Why those and not the rest:
- **ResMed writes EDF,** a published standard, so its files say what they hold. The R `edf` package gives that standard an implementation nobody here wrote.
- **An AirSense 10 card has an independent check** in Z's R prototype.
- **Every other machine's format is known only through other projects' reverse engineering,** and a search for readers independent of OSCAR found one for BMC and one for Yuwell, and none for the rest (`dev/READING-LOG.md`, R-016). A reader built from one project's description and checked against that same project has been checked against itself.

Even inside ResMed, only the AirSense 10 has a card to check against. The S9 and the 11 series are read the same way, and until Z has one of those cards that is an expectation rather than a tested fact. **Their field names come from OSCAR, and PAPvault says so where a reader of PAPvault will see it** (Z, 2026-09-19): in `SOURCES.md` and in the user documentation, not only in these notes.

**How a machine joins the list.** Z, 2026-09-19: *"as people report issues, send me even fake data for different machines I'll be adding them."* So a machine arrives through its users: a report, and data Z can test with, real or made up. What the machine then needs before it is supported is in `.claude/development-notes/machine-survey.md`, and the reads already named for it are parked in `dev/READING-LOG.md`.

**How PAPvault reads a card follows Z's `prepare_data()`**, in `CPAP_old/data_prep.R`. Z, 2026-09-19: *"For ResMed, we will use the time implementation that I built. For the others, we will use a similar implementation. I really think the way I implemented the data prep is good. It can be improved but it is the implementation we will use."* Under that design:
- a sample's time is its file's start time plus the sample's offset in the file;
- an event starts at its file's start time plus its onset, and ends its duration later;
- each signal file gives a recording start at its own start and a recording stop at its own end.

Improving that design is Z's decision, and another project doing it differently is no argument for a change.

PAPvault is also a showcase. Z calls the method **human-in-the-steering-wheel** development, as opposed to human-in-the-loop: the human drives, rather than approving what the agent drives. Z, 2026-09-18: *"I want the reviewer to look at this and say, 'yeah AI agents can be used responsibly, when developing a health related app.'"* So the record of how PAPvault is built is part of what it delivers. Write every rule, note and commit message for a reviewer who arrives skeptical and checks.

## The promise is the product

Z, 2026-09-18: *"build a web platform that people can view their data interactively without uploading their data to internet."*

Z, 2026-09-18: *"We won't have any telemetry allowed on this website, it is a trust issue, so no analytics no collection of any data."*

These are the requirements the rest of the design answers to, and they are two different things:

- **No network request the application makes may carry user data, or anything derived from it.**
- **The site collects nothing about the people who use it.** No analytics, no telemetry, no error reporting, no usage counts. The reason is trust, so "anonymized" and "aggregated" are not exceptions.

Both are invariants, and an invariant held by care is not held, so the page enforces them itself (the first point under *How to know a change works*). Until it does, **any network request the application makes is a finding to raise with Z, not a detail to settle in passing** -- a fetched font, a CDN script, a request to any host that is not the one serving the page. Even with nothing attached, a request to a third party tells it that someone is using PAPvault, and deciding whether that is acceptable is Z's call.

The page governs only what the page sends. The host is GitHub Pages, and GitHub's documentation says every visitor's IP address *"is logged and stored for security purposes"* (read 2026-09-18). The page cannot prevent that, so PAPvault is described as collecting nothing itself, never as nothing being collected at all.

## It displays; it does not conclude

Z, 2026-09-18: *"We will not make any conclusions beyond what the PAP machine declares. Again it is a matter of principle. It will just display the data."*

PAPvault shows what the device recorded and what the device itself declares, and adds no judgment of its own. However helpful it looks, that rules out a severity band or a "normal range", a good or bad color on a value, a goal line, a trend verdict, a score, and any advice. Where the device declares something -- an event, a flag, a figure of its own -- PAPvault shows it as the device's.

What the device declares is what its night data on the card holds. A manufacturer's app or cloud portal, such as ResMed's myAir, is not a source, and how it behaves is no concern of PAPvault's (Z, 2026-09-19).

## It reads the night, and nothing that identifies

Z, 2026-09-19:

> I don't know why STR.edf matters. It is not night data. We should not be reading anything that is not data from the night. Same goes for journal.dat. We're building something that is supposed to be "not nosy".

> PAPvault should never touch anything identifying.

> This is where we're trying to diverge from OSCAR

- **Only night data is read.** A file that does not hold the recording of a night is not opened.
  - On a ResMed card that rules out `STR.edf`, `Identification.*`, `SETTINGS/`, `Journal.dat` and the `.crc` files.
  - On other machines it rules out their settings and configuration files.
  - Summaries are computed from night data alone.
- **Nothing identifying is touched.** A field that names or numbers the person or the machine is skipped, and never decoded, shown or kept. That covers EDF's patient and recording fields, and any serial number. A folder named by a serial number is passed through, and its name is never shown or kept.
- **Here PAPvault diverges from OSCAR by design.** That another tool reads a file is no reason for PAPvault to read it.

## How a card is read, and what is shown

Z set this on 2026-09-19:

> User selects data folder -> Selects date or date range -> pipeline reads the data from one day before the date to one day after the date (it will be +1 cpap day or +2 calendar days) Then calculates the dates with what I already have and subsets it to the relevant days.

- **The reading runs in that order,** and nothing about the machine's own filing is assumed. A file's name and header say when its session started, so which folder the machine filed it under never decides anything.
- **A session belongs to the CPAP day it began in,** whole. Its samples and events go with it, including any that fall after the next 6:00. So no session is split, none is counted twice, and a day's summary can cover a little more than the day.
- **What is shown depends on how much is chosen** (Z, 2026-09-19): one day shows that day's detail, with the detailed plots; any longer period shows summary figures and summary plots only.
- **What is read follows what is shown.** A period longer than a day needs no waveform file, and no waveform file is opened for it. Reading a year of nights takes time, and the page says so rather than appearing stuck.
- **An event keeps the words the device wrote.** Z, 2026-09-19: *"The apnea labels are in "annotation" column when the eve file is read. I agree with keeping them as they are."* PAPvault never maps one machine's labels onto another's, and never groups them into kinds of its own. A grouping would be PAPvault deciding that two devices mean the same thing.

## Real device data never enters the agent's context

**The agent's context is not local.** Reading a file sends its contents to Anthropic's servers. A project whose whole promise is that health data stays on its owner's machine cannot be built by sending anyone's health data somewhere else, so the rule the application keeps, the development keeps too.

Real data is anything from a device's SD card or an export of one, and anything computed from it: `CPAP_old/AirSense10/`, `CPAP_old/Archive/`, and any path Z names. File names and sizes are not the problem; the contents are. The headers carry identifiers and the signals are the therapy record.

- **Never read it into the conversation.** No `Read`, `cat`, `head`, `strings` or `hexdump`, and no `grep` or script whose output prints its contents.
- **A local script over real data needs Z's go-ahead first**, and its output carries neither an identifier nor a per-night value. Signal labels, sampling rates, record counts and durations are structure; a pressure, a leak rate or an event count is the record.
- **The ground truth for reading a real card is the R prototype**, `prepare_data()` in `CPAP_old/data_prep.R` (Z, 2026-09-18). A comparison against it runs on Z's machine, and what reaches the conversation is a verdict, never a value. It reaches only the files that function reads; the rest of a card has no ground truth yet.
- **Format knowledge comes from published specifications**, and from other projects only on the terms under *What we take from other projects*. Every source is cited. It never comes from inspecting a real card.
- **Data for development and checking is synthetic.** A committed generator builds it, with Z's help, and nothing in it is derived from real data. Generators live in `dev/synthetic/`, one Python standard-library script per format family, and write to `dev/synthetic/out/`, which git ignores.
- **Nothing derived from real data goes into the repository, a development note, a commit message, a published artifact or a screenshot** unless Z has approved that item by name.
- `CPAP_old/` stays gitignored, and nothing under it is ever staged. `.gitignore` also ignores every EDF file and the folders and files of a ResMed card, wherever they appear, synthetic output included; nothing it ignores is ever added with `git add -f`.

## Security

Z, 2026-09-18: *"we should be careful with JS. It should be completely open source. We also need to work on the security. I mean JS injection attacks would be terrible."*

- **A file is untrusted input.** Anyone can craft a card, or share one. Text read from a file -- a header field, an event annotation -- reaches the page only as text, never as markup, and nothing read from a file is ever run as code. `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`, `eval` and `new Function` appear nowhere in the source; grep for them, and the check is that it finds nothing.
- **The parser trusts no number a file declares.** Every size, count and offset in a header is checked against the real size of the file before it is used. A file that does not add up is reported, never read past its end.
- **The Content-Security-Policy is the second wall.** It is a `<meta>` tag, because GitHub Pages cannot set response headers. Scripts and styles run only if their hash is in the policy, and the build computes the hashes from the files it inlines. No inline event handlers, no `eval`, and no outbound connection of any kind. An injection that got past the first rule would still not run, and could send nothing. Any change to the policy is raised with Z by name. Alongside it, `<meta name="referrer" content="no-referrer">`.
- **The page refuses to run inside a frame.** A `<meta>` policy cannot forbid framing, so the page checks for itself.
- **Nothing may need a header GitHub Pages cannot send.** Cross-origin isolation above all: no `SharedArrayBuffer`, no threaded WebAssembly, and no service worker to add headers back, which would also break the offline file. A feature that would need one is raised with Z, not worked around.
- **Every line of JavaScript is open source and readable.** Libraries are few, each approved by Z by name, stored in the repository unminified and pinned to a version, under a license compatible with GPL-3.0. Nothing is loaded from a CDN or any other host. Approved so far: uPlot 1.6.32, MIT, for the plots (Z, 2026-09-19).
- **The build is one short script on the Python standard library.** No package manager, so no dependency tree stands behind what ships. It inlines everything into one self-contained HTML file, and that file is both what the site serves and the offline download. The same input gives the same bytes, and each release publishes the file's checksum, so anyone can rebuild it and compare.
- **Only Z publishes.** Z is the sole maintainer, with two-factor authentication on the account, and the agent never pushes (Z, 2026-09-18).

## What we take from other projects

Z, 2026-09-19: *"We should not use code directly from OSCAR. I think it would be wrong. I don't think it is wrong to use the knowledge. We will display all the source of knowledge we collected in SOURCES.md."*

Later that day, the agent was reading OSCAR's reader to build a synthetic data generator, and Z stopped it: *"There is already a lot of backlash against using AI agents because they plagiarize and it becomes stolen work. I want to make a showcase of responsible AI use."* The attempt, and how Z stopped it, are in `.claude/development-notes/other-projects.md`. Then Z set the rule:

> *"What we need to collect is how the data is stored. When you need to read something for a specific purpose we need to name it, record it, clear it, and do it."*
>
> *"We can read OSCAR's reader for only the purposes of data generation. We need to record what the task was. The issue with the previous attempt was that I saw that OSCAR was becoming the authoritative tool to make decisions about this tool I'm building."*

None of what follows is relaxed for convenience, for speed, or because a fact seems small.

- **What is collected is where the night data is, and what a standard does not already say** (Z, 2026-09-19).
  - EDF describes itself. So for an EDF file, the only thing taken from another project is the folder tree: where the night files are, and how they are named.
  - For a format that is not a standard, what each file holds is taken as well, per model.
  - What PAPvault reads is settled by Z's `prepare_data()`, never by another project. How another project divides the data, checks it or shows it is never taken.
- **Where models may differ, how other tools read them is looked at with limited scope.** For the three ResMed series (S9, 10 and 11), a harnessed read may show how another tool reads each one. Its only purpose is to learn whether the series differ, and how. Z, 2026-09-19: *"This is where we can look (with limited scope) how other people are reading the data (OSCAR, or another tool) for all 3 machines to understand if there is a difference between them and what the difference is. My code settles what we are reading."*
- **Every read is named, recorded, cleared and done, in that order.** This applies to every source that is not a tracked file of this repository: a specification, Z's prototype, another project's code or documentation, a manufacturer's document, a forum. It binds any agent the agent starts, and that agent's brief carries the entry.
  1. *Name*: the task the read serves, the source (its file or section, at a commit or a URL), and the facts it is for.
  2. *Record*: an entry in `dev/READING-LOG.md`, written before anything is opened.
  3. *Clear*: Z writes the entry's *Cleared* line. The agent never writes it.
  4. *Do*: read only what was cleared, for the facts named, then add to the entry what was found.
- **Another project's reader is always harnessed.** It is read only to build synthetic data, and only through those four steps. What comes out of it is how the data is stored, and that goes into `dev/formats/` and nowhere else.
- **No other project is an authority on PAPvault.** Z decides how PAPvault divides days, how it times what it reads, and what it shows or leaves out, following Z's `prepare_data()`. That another project does something differently is not an argument.
- **A published specification is the source wherever one exists.**
- **A gap goes to Z, not to the nearest source.** When the sources already cleared leave a fact open, the agent stops and names the gap. Z decides where the fact comes from, or that it is left out.
- **Facts cross over in writing.** A fact goes into `dev/formats/<family>.md`, citing its log entry and quoting no code, and code is written from that file. The code is written in a new session, one whose context has never held another project's reader for that family. A compacted session is not a new one. **Only Z waives this, for one named piece of work, and the waiver and its reasons are recorded** where the work can be found: the ResMed generator was written under such a waiver (Z, 2026-09-19, in `.claude/development-notes/other-projects.md`).
- **A slip is stopped and recorded.** A slip is a read that skipped a step or went beyond what was cleared. The agent stops it, tells Z exactly what was read, and records it in the log. Nothing learned from it is used until Z has ruled on it.
- **No code from OSCAR or any other project goes into PAPvault**, whether copied or translated into JavaScript line by line. Every line is written here, from what is known about the format. The libraries approved under *Security* are the one exception: other people's code, carried whole, under their own licenses, and credited.
- **This rule is about other people's intellectual property, and Z's own work is not covered by it.** Z, 2026-09-20: *"Reading code from OSCAR and using it as the ultimate source is like getting someone's blueprints, making a photocopy and building a structure based on that. Copying or reading a workflow from my own repository is like using my own hammer to put a nail on the wall."* Architectures, workflows, scripts and prototypes Z wrote before are Z's to reuse here, adapted to what PAPvault needs. This is why PAPvault stops at ResMed: *"That's where my contribution stops."* Reading a source outside this repository is still named, recorded, cleared and done, Z's own checkouts included -- that is how a read is kept to its purpose and written down, and it is a separate matter from whose work it is. **Nothing here is an exception to the rule above; the rule never reached Z's own work in the first place.**
- **Every source is listed in `SOURCES.md`** at the repository root, with what was learned from it. The log entry for a read gives the repository, file and commit it was read at, so anyone can check it.
- **A project with no license is read for facts only**, and none of its text is reproduced.
- **Where one project is the only source for a fact, it cannot also be the check on it.** A reader built from OSCAR's description of a format and then compared with OSCAR has been compared with itself. The notes say where that is the case.

## How synthetic data is made

Z agreed this workflow on 2026-09-19. Each format family goes through these steps in order:

1. **Name** the storage facts the family's night data needs, and a source for each. Nothing identifying is named. A specification comes first, then Z or Z's prototype, then a named file of another project. A gap goes to Z.
2. **Record, clear and read** each source through `dev/READING-LOG.md`, as set out under *What we take from other projects*.
3. **Describe** the storage in `dev/formats/<family>.md`.
   - Each fact cites its log entry and says where it came from: a specification, Z, or a single other project.
   - A value no source gives, such as a calibration range, is marked as the generator's choice. A reader must not depend on it.
   - Z reviews the file before any code is written.
4. **Agree the cases with Z**, also before any code: what each synthetic card exercises and what it must show. A case whose answer depends on something Z has not decided is marked undecided, not guessed. **The data need not look realistic.** Z, 2026-09-19: *"The generated data does not have to be realistic. I'll test with real data. On my end."* So a case is built to exercise something and to carry an answer known by construction, and a signal may be any shape that makes its answer easy to check.
5. **Generate** from the format file and the cases alone, in a new session.
   - One Python standard-library script per family, in `dev/synthetic/`. It is seeded and writes the same bytes on every run.
   - Each case goes to `dev/synthetic/out/<family>/<case>/`: the card, and an `answer.json` derived from how the card was built.
   - Times in the answer follow the design under *How PAPvault reads a card*.
   - One change at a time.
6. **Check.** The agent:
   - runs the generator twice and compares the checksums;
   - for an EDF family, has the R `edf` package, which the prototype reads with (1.0.1, installed by Z), decode the synthetic files, then compares that with `answer.json`;
   - for ResMed, also has `prepare_data()` read the synthetic card.

   For a family with no independent decoder, the generator and the reader are written from the same format file, and the notes say so. Then Z checks, and records the check in `dev/VERIFICATION.md`.
7. **Record** the family's decisions in a development note, and propose checklist entries.

Only ResMed has a generator for now, since only ResMed is supported. A machine that Z later gets a card for goes through the same steps, one family at a time.

## Building and running it

- `python3 build.py` writes `dist/index.html` and prints its SHA-256. `dist/` is build output and is not tracked.
- **The manual is `docs/manual.md`,** and the build renders it into the page. It uses a small subset of Markdown, listed at the top of `build.py`: `#` for a group in the navigation, `##` for a section, `>` for a pull quote, `-` and `1.` for lists, and `**bold**` and `` `code` `` within a line. Everything is escaped, so the manual can never put markup into the page.
- Opening `dist/index.html` straight from disk is the offline page, and needs no server.
- **When the agent needs a server, it uses port 8765** (Z, 2026-09-18): `python3 -m http.server 8765 --bind 127.0.0.1 --directory dist`. It records the PID when it starts one, stops only that PID, and never touches a server it did not start.
- **A browser the agent starts for a check is headless, with its own temporary profile directory, and exits on its own.** It never attaches to a browser Z is using.

## Comments: what the code does, never why we chose it

**Every comment clause is either a description of the code below it or a design decision. Descriptions stay, in one line. Decisions move to `.claude/development-notes/` and leave the source.**

The unit is the clause, not the comment. The usual failure is a comment that opens with a real description and smuggles a justification in after it. Write what the code does, stop, and check whether what you were about to add next is a decision.

**Why:** a design decision left in a comment reads to a later session as a current constraint, and gets argued from against what is actually being asked. Z, on PoolSeqFlow, 2026-08-30: *"In multiple occasions, the previous design decisions have skewed your interpretation of my asks, we had to spend way too much time on simple tasks."*

Not every "why" is a decision. The cut is whether the code becomes **inexplicable** without the line, or merely **unjustified**. A constraint that makes an otherwise pointless line explicable is what the code does, and stays. A constraint that defends one working choice over another is a decision, and goes.

Before calling a file done, grep for `on purpose | deliberately | rather than | because | would otherwise | so that | which is why`. Each hit is a candidate, not a verdict, and the grep is never made a pass/fail gate: a hard failure trains the next session to reword around the words instead of removing the decision.

| Where | What |
|---|---|
| the source | what the code below does, what it returns, a coupling or constraint invisible from here |
| the user documentation | anything that changes what a displayed number **means**, or that a person reading their own data needs. It is authoritative, and nothing in it is repeated in the source. It lives in `docs/manual.md` (Z, 2026-09-19), which the build renders into the page's Manual dialog. |
| `.claude/development-notes/` | how it got here: design churn, alternatives dropped, measurements, who decided what and when |

**No source file references the notes.** A note is dated and not updated to follow the code, so a pointer to one imports a description of the code as it used to be.

**Mid-feature is not the deadline, but the feature has one.** A comment may carry more than the code needs while a stage is open; every stage ends with a pass over the comments it added. Put that pass in the stage's checklist when the stage starts, or it is the thing that gets skipped.

**Development tooling, the synthetic data generator among it, follows the opposite rule: keep everything but abandoned ideas.** There the reasoning is the content. A measurement with no account of what it measured cannot be acted on, and a synthetic case with no record of what it was built to exercise gets deleted as arbitrary. The one thing to cut is an approach that was dropped, described as though it were still how things work.

## Development notes

`.claude/development-notes/` is the record of how PAPvault got here, one file per subject rather than per source file.

- **Every note opens with `**Written <date>, against the tree at <hash>.**`** and is never rewritten to follow the code. Appending a new, dated finding is allowed; correcting an old description to match today's code is not. Where a note and the user documentation disagree, the documentation is right and the note is history.
- **Two files are exceptions and say so at the top:** the index, `README.md`, and `platform-traps.md`, which is appended to as traps are found. Both are kept current.
- **Durable knowledge goes here, not only into the agent's memory.** Memory is private to one account and nobody can review it; a note is a reviewable artifact that travels with the checkout. The memory entry is a one-line pointer to the note.
- **A note hands its reader the command that would falsify it**, rather than asserting a count or a mechanism in prose.
- **This file and the notes are public** (Z, 2026-09-18). Write both for a reader outside the project, and never put a value from real data in either.

## How work is reviewed

- **Never `git push`**, or anything else outward-facing: no `gh pr create`, no release, no remote branch. Z publishes. `git stash push` reads as a push in a command line, so say beforehand that it is local, or avoid it.
- **Never `git commit` unless asked, and a commit instruction covers only the work that existed when it was given.** Do the work, leave it uncommitted, say what changed in prose, stop. The uncommitted tree is the review surface; a diff artifact or a summary page is not a substitute.
- **Use the `Edit` tool for changes to an existing file, never a script that rewrites it.** Z reviews side by side in the IDE diff view as each edit lands, and a rewritten file gives that view nothing to show. An announced mechanical rename with `sed` is the one exception. Reaching for a script is a sign the change is too big to review in one go.
- **One change at a time.** Finish one item, say exactly what changed, what the agent checked and what is left for Z to check, then stop. Keep a list of deferred items and restate it at the end of each turn.
- **Agents only with Z's go-ahead**, on Sonnet, at most four at a time (Z, 2026-09-19). An agent's report is model output, not a finding: before anything from it is used, its load-bearing claims are checked against their primary sources, and what the check found wrong is recorded with the rest.
- **Do not overstate severity.** "Bug" is for behavior that is wrong, not behavior that is non-deterministic, unidiomatic or different from before. Describe what was measured and let Z judge; a preference is offered as a preference.

## How decisions are made

- **Fail loudly, or document -- never automate away a decision.** Where the right answer depends on something the application cannot know, it says so and stops. A computed default never removes the knob. Something done for the user as a side effect of something else is not the same as the user asking for it by name.
- **Settle a design question with data rather than argument, where data can settle it.** Build the case that would distinguish the two claims, run it, read what comes back. The data then becomes part of the repository, so anyone who disagrees can re-run it. Here that data is synthetic.
- **What a device value means -- its unit, what a flag or an event code stands for -- comes from a cited source Z has checked**, never from the agent's recollection. The agent's expensive errors are the plausible ones, and a mislabeled value is where a plausible error hides.

## How to know a change works

**Z tests every change personally, and there is no automated test suite.** Whether a change is right is Z's call, and a suite the agent writes and runs is the agent vouching for itself. A suite may come once there is enough synthetic data to build one on (Z, 2026-09-18); until then nothing here assumes one.

What a person cannot do is re-check, after every change, everything that was checked before, and an agent produces changes faster than anyone can. Three things cover that, and none of them takes the testing away from Z:

1. **The promise is enforced by the page, not by care.** The Content-Security-Policy described under *Security* makes the browser refuse any outbound connection. It is in place before the first feature that reads a file.
2. **A written checklist, run by Z before each release**, in `dev/CHECKLIST.md`: what to check, and what a failure looks like. A check with no stated failure is not a check. When a change adds behavior worth protecting, propose its checklist entry with the change.
3. **A record of every verification, in Z's words**, in `dev/VERIFICATION.md`: what was checked, on what data, at which commit. Testing that is not written down is invisible to the reviewer this project is for. **The agent never writes that Z verified something**, and never presents its own checks as Z's.

What the agent does before handing a change over:

- **Say what it checked itself, and show the output**, separately from what is left for Z to check, and name what it did not check.
- **Read the whole output of anything it runs.** In PoolSeqFlow the tail of a failure summary was read as a list of passes.
- **Two things that must agree are derived from one source, never kept in step by hand.** A pair kept in step by care drifts silently and produces a wrong result rather than a failure.
- **After any move, rename or filter, ask what was pointed at the old thing**, and grep for it. A check aimed at something that moved keeps passing over nothing.
- **Synthetic data carries its own answer.** What a case should show is derived from how it was built, and the generator is committed rather than its output. An expectation read off what the code produced is a check that cannot fail.

## House style

American English everywhere, and interface text reads as American prose: words over notation where both work, so "6 in the morning", not "06:00" (Z, 2026-09-19, who gave the rule with the example "noon to noon", not "12:00 to 12:00", from the day boundary as it then stood). ASCII only in the text we write -- `--`, `...`, `->`, straight quotes -- except data we did not author, a character that is the subject of the sentence, a glyph the application renders, and a literal whose other half a text tool cannot reach. No hard wrapping in markdown: one line per paragraph and per list item.
