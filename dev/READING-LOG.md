# Reading log

Every source PAPvault is built from is read the same way. Z, 2026-09-19: *"When you need to read something for a specific purpose we need to name it, record it, clear it, and do it."* The rule, and what counts as a source, are in `CLAUDE.md` under *What we take from other projects*.

This file is where the second and third steps happen:
- An entry is written **before** anything in it is opened.
- **Z writes the *Cleared* line.** The agent never writes it.
- After the read, the agent adds a *Done* line saying what was found and where it went.

Nothing in an entry is rewritten afterwards; an entry only gains lines. The entry ID is what a fact in `formats/` cites.

```
## R-<number>: <source, in a few words>

- **Named:** <date>
- **Task:** <what the read is for>
- **Source:** <file or section>, at <commit, or URL and the date it was read>
- **Facts sought:** <how the data is stored: which facts, for which file>
- **Not read:** <what stays closed>
- **Cleared:** <written by Z>
- **Done:** <date; what was found, and where it went>
```

## R-000: reads made before this rule

- **Named:** 2026-09-19, after the fact
- **Task:** none. These reads were made before the rule existed, and none was cleared. Nothing learned from them is used. A fact from them can be used only after a read of its own through this log.
- **Source:** several sources:
  - the survey of machines, whose sources are in `.claude/development-notes/machine-survey.md` and `SOURCES.md`;
  - OSCAR's update check, in `.claude/development-notes/product-brief.md`;
  - the attempt of 2026-09-19 on the ResMed generator, which covers OSCAR's ResMed reader and EDF parser, the R `edf` package's code, the EDF and EDF+ specifications, and `CPAP_old/data_prep.R`, in `.claude/development-notes/other-projects.md`.
- **Facts sought:** none named
- **Not read:** nothing was held back

## R-001: the EDF specification

- **Named:** 2026-09-19
- **Task:** synthetic data for group 1: ResMed S9, and AirSense and AirCurve 10 and 11. This is step 1 of *How synthetic data is made*, collecting how the card stores its data for `formats/resmed.md`.
- **Source:** the EDF specification, https://www.edfplus.info/specs/edf.html, as it reads on the day of the read
- **Facts sought:** how an EDF file is laid out:
  - the header record's fields, with their widths and encoding;
  - the data records, and the order of the signals within them;
  - how a sample is stored;
  - how a digital value maps to a physical one;
  - how the record duration and the number of samples per record give the interval between samples.
- **Not read:** the rest of edfplus.info, and the 1992 article the page cites
- **Cleared:**
- **Done:** 2026-09-19.
  - **What the read went ahead on:** Z's words in conversation, *"OK. 1-4 cleared let's complete this first."* The *Cleared* line above is Z's to write.
  - **What was read:** the page as fetched at 19:35 UTC, SHA-256 `00dea77fbca74942b5b3a453926f0bb472f3d34ebb0b6485273f69c0ed465590`, the same bytes as the copy fetched earlier that day under R-000.
  - **What was found:**
    - the header record's fields and widths;
    - ASCII, left-justified and padded with spaces;
    - data records holding each signal in header order, as 2-byte two's complement integers;
    - the four extreme values that fix each signal's calibration;
    - the interval between samples, which follows from the record duration and the number of samples per record.
  - **Where it went:** into `formats/resmed.md`.

## R-002: the EDF+ specification, sections 2.1 and 2.2

- **Named:** 2026-09-19
- **Task:** the same as R-001
- **Source:** the EDF+ specification, https://www.edfplus.info/specs/edfplus.html, sections 2.1 (2.1.1 to 2.1.3) and 2.2 (2.2.1 to 2.2.4), as they read on the day of the read
- **Facts sought:**
  - how EDF+ marks a file as continuous or interrupted;
  - what EDF+ requires of the header fields: the patient and recording fields, the start date, the characters allowed, the number format, the byte order;
  - how events are stored: the annotation signal, the time-stamped annotation lists, and their separator bytes;
  - how each data record's start time is kept;
  - what a file holding only annotations must contain.
- **Not read:** sections 1, 2.3 and 3, and the page of standard texts that section 2.1.3 points to
- **Cleared:**
- **Done:** 2026-09-19.
  - **What the read went ahead on:** the same words of Z's as R-001.
  - **What was read:** the page as fetched at 19:35 UTC, SHA-256 `f7b3bba32efe9643ede03a6cf49477bf3a351a62120be2ca50f9d9a4fa53f6ea`, the same bytes as the earlier copy.
  - **What was found:**
    - the `EDF+C` and `EDF+D` marks;
    - the rules for header characters, dates, numbers and byte order (little-endian);
    - the anonymous forms of the patient and recording fields;
    - the start time as local time, with no zone;
    - the annotation signal and its time-stamped lists, with separator bytes 20, 21 and 0;
    - how a record's start time is kept;
    - a record duration of 0 for a file with no ordinary signals.
  - **Where it went:** into `formats/resmed.md`.
- **Slip:** the command meant to stop at section 2.3 missed its heading. It printed the first paragraphs of section 2.3, *"Analysis results in EDF+"*, up to the rule for naming a file of derived results. Section 2.3 is listed above as not read. Nothing from it is used, and nothing in it bears on this task. Z has been told.

## R-003: Z's prototype, `data_prep.R`

- **Named:** 2026-09-19
- **Task:** the same as R-001
- **Source:** `CPAP_old/data_prep.R`, the whole file, 155 lines. It is not tracked by git, so its SHA-256 is recorded at the read.
- **Facts sought:**
  - which kinds of session file a day's data comes from, and how each kind is recognized by its name;
  - the names of the signals read from each kind, and what those names say about sampling;
  - which fields of an event are used;
  - how each sample and each event is given its time. This is the design PAPvault follows.
- **Not read:** every other file in `CPAP_old/`. `CPAP_old/AirSense10/` and `CPAP_old/Archive/` are real data and are never opened.
- **Cleared:**
- **Done:** 2026-09-19.
  - **What the read went ahead on:** the same words of Z's as R-001.
  - **What was read:** the whole file, SHA-256 `d81139b9f8a2acf9a0f4da729950cc95c4a6ca0b1c1cd54be297aaaf9d5af373`.
  - **What was found:**
    - five kinds of file, each told apart by its three letters appearing in the path;
    - the signal names read from each;
    - the events' annotation, onset and duration, with empty annotations dropped;
    - each sample timed at its file's start plus its offset, and each event at the file's start plus its onset;
    - a recording start and stop taken from each signal file's header.
  - **Where it went:** into `formats/resmed.md`.

## R-004: Z's prototype, `app.R`

- **Named:** 2026-09-19
- **Task:** the same as R-001
- **Source:** `CPAP_old/app.R`, the whole file, 374 lines. Its SHA-256 is recorded at the read.
- **Facts sought:**
  - how the prototype finds a day's files on a card: the folders and file names it expects;
  - how it applies the CPAP day;
  - which event names it handles;
  - any units it gives the signals.
- **Not read:** every other file in `CPAP_old/`, and never the real data. A path or date in the file that comes from a real card is not carried into this log, the notes or `formats/`.
- **Cleared:**
- **Narrowed:** 2026-09-19, before any read. Z ruled that EDF describes itself, so units and event names come from the files themselves. The facts sought are now only these two: the folders and file names the prototype expects, and how it applies the CPAP day.
- **Done:** 2026-09-19.
  - **What the read went ahead on:** the same words of Z's as R-001.
  - **What was read:** the whole file, SHA-256 `3916cc6ab6b09e72f7338d6a8655de769468ec75fd3a4af5ac068a7cc9f6c07a`.
  - **What was found:**
    - the night data sits in a `DATALOG` folder at the root of the chosen folder;
    - each folder inside `DATALOG` is offered as one day, under its own name;
    - a day's files are those in that folder whose names contain `edf`;
    - the prototype does not work out days itself: each folder counts as one day.
  - **What was not taken:** the file gives its plots unit labels. Units were narrowed out of this read, so none was taken. The file holds no path or date from a real card.
  - **Where it went:** into `formats/resmed.md`.

## R-005: Z's prototype, `plotting.R`

- **Named:** 2026-09-19
- **Task:** the same as R-001
- **Source:** `CPAP_old/plotting.R`, the whole file, 93 lines. Its SHA-256 is recorded at the read.
- **Facts sought:** event names and signal units. It is read only if R-004 leaves them open.
- **Not read:** the same as R-004
- **Cleared:**
- **Withdrawn:** 2026-09-19, before any read. EDF files carry their own units and event text, so this read has nothing left to find.

## R-006: how another tool reads the three ResMed series

- **Named:** 2026-09-19
- **Task:** synthetic data for group 1. This is the limited-scope look Z allowed, to learn whether and how the S9, 10 and 11 series differ, for `formats/resmed.md`.
- **Source:** OSCAR, `gitlab.com/CrimsonNape/OSCAR-code` at `64c5e90a`, `oscar/SleepLib/loader_plugins/resmed_loader.cpp`, these parts only:
  - lines 300 to 320;
  - lines 1030 to 1125;
  - lines 2325 to 2365;
  - lines 3960 to 4010.

  These ranges are where the reading made before the rule (R-000) found these things. They only bound this read; nothing from that earlier reading is used.
- **Facts sought:** for each of the S9, 10 and 11 series:
  - the folder tree and the names of the night files;
  - which kinds of night file it writes;
  - what labels it gives the signals `prepare_data()` reads (R-003);
  - where the series differ in any of these.
- **Not read:** the rest of that file, and every other file of OSCAR. Nothing is taken about how OSCAR divides days, handles events, or treats files that are not night data.
- **Cleared:** 2026-09-19
- **Done:** 2026-09-19.
  - **What was read:** the four ranges and nothing else, from a clone checked to be at `64c5e90a26f91fb15868bcfcccde0c1e1522ac86`, with the file's SHA-256 `ce75ee041a4c39cf63eb2149d76fa397d43b4b94ea4f93022f8df5f462441377`.
  - **What was found:**
    - the `DATALOG` folder, at the root of the card (lines 300 and 312 to 315);
    - inside it, folders with eight-character names read as `yyyyMMdd` (lines 1037 and 1038);
    - file names whose first two underscore-separated parts are the date and time, `yyyyMMdd_HHmmss` (lines 1112 and 1113);
    - the kind of file as the last underscore-separated part, before the extension (line 2332). The kinds are `EVE`, `BRP`, `PLD`, `SAD`, `SA2`, `CSL` and `AEV`, with `SA2` read as `SAD` is read (lines 2333 to 2345).
    - `EVE` and `CSL` described as holding only annotations (line 2358);
    - a table of signal labels, which a comment says combines the S9, AirSense 10 and AirSense 11 variants and those of devices set to other languages (lines 3960 and 3961). For each signal `prepare_data()` reads, the table lists both a short or translated form and a form with the interval appended, such as `Flow.40ms` (lines 3971 to 4003).
    - **Where the series differ:** the ranges read do not say which series writes which label form, `SA2` or `AEV`. Nothing in them treats the folder tree differently by series.
  - **What was seen but not taken:**
    - the check for `STR.edf` and the `Identification` prefix (lines 301, 302 and 317 to 320), since those files are not night data;
    - a comment and code on dividing days at noon (lines 1115 to 1119), since days were excluded from this read;
    - year-named folders, which a comment places in OSCAR's own backup rather than on the card (line 1031);
    - the event names, the labels of signals the prototype does not read, and the summary and settings labels (lines 3973 to 3999 in part, and 4004 to 4010).
  - **Where it went:** into `formats/resmed.md`.

## R-007: Loewenstein prisma SMART and SOFT

- **Named:** 2026-09-19
- **Task:** synthetic data for group 2, for `formats/prisma.md`
- **Source:**
  - OSCAR at `64c5e90a`: `oscar/SleepLib/loader_plugins/prisma_loader.cpp` and `prisma_loader.h`, whole;
  - `github.com/ZacSadan/oscar-js`, its README only. It has no license, so it is read for facts only, and nothing of it is reproduced.
- **Facts sought:**
  - the folder tree below the serial-number folder;
  - which files hold night data and which hold settings;
  - how each night file is laid out, per model, including how its EDF variant departs from the standard;
  - where the identifying fields sit, so they can be skipped.
- **Not read:** every other file of either project, including oscar-js's code. Nothing is taken about days, summaries, settings, or any decision the reader makes.
- **Cleared:**
- **Second source (R-016):** `axt/prisma-smart-utils`, MIT. Where its knowledge came from is not stated, so its independence is unproven. `hms-cpapdash-parser` also reads prisma but names OSCAR-compatible metrics. Reading either is named separately.
- **Parked:** 2026-09-19. Z supports ResMed only for now, until a card of another machine can be tested. This entry stays unread and uncleared until then.

## R-008: Fisher & Paykel SleepStyle

- **Named:** 2026-09-19
- **Task:** synthetic data for group 2, for `formats/sleepstyle.md`
- **Source:** OSCAR at `64c5e90a`, `oscar/SleepLib/loader_plugins/`: `sleepstyle_loader.cpp`, `sleepstyle_loader.h`, `sleepstyle_EDFinfo.cpp` and `sleepstyle_EDFinfo.h`, whole
- **Facts sought:**
  - the folder tree;
  - which files hold night data;
  - for the EDF files, only their folder and names, since EDF describes itself;
  - for the other night files, how each is laid out, per model;
  - where the identifying fields sit.
- **Not read:** every other file. Nothing is taken about days, summaries or decisions.
- **Cleared:**
- **Second source (R-016):** none found for SleepStyle.
- **Parked:** 2026-09-19, with R-007.

## R-009: Fisher & Paykel ICON

- **Named:** 2026-09-19
- **Task:** synthetic data for group 3, for `formats/icon.md`
- **Source:** OSCAR at `64c5e90a`, `oscar/SleepLib/loader_plugins/icon_loader.cpp` and `icon_loader.h`, whole
- **Facts sought:**
  - the folder tree;
  - which files hold night data;
  - how each night file is laid out: its header, its records, how time is stored, and what each field holds and in what unit;
  - where the identifying fields sit.
- **Not read:** every other file. Nothing is taken about days, summaries, checksums or decisions.
- **Cleared:**
- **Second source (R-016):** `jieter/fph-parser` reads `SUM` and `DET` files, but takes its format description from the SleepyHead wiki, OSCAR's predecessor. It is not independent.
- **Parked:** 2026-09-19, with R-007.

## R-010: Philips System One, DreamStation 1 and DreamStation Go

- **Named:** 2026-09-19
- **Task:** synthetic data for group 3, for `formats/philips.md`
- **Source:** OSCAR at `64c5e90a`, `oscar/SleepLib/loader_plugins/`: `prs1_loader.cpp`, `prs1_loader.h`, and the files named `prs1_parser*`, whole
- **Facts sought:**
  - the folder tree;
  - which files hold night data;
  - the chunk layout, and how it varies by model family and version;
  - how waveforms and events are stored, and what each field holds and in what unit;
  - where the identifying fields sit.
- **Not read:** every other file. The DreamStation 2's encryption is not read, since that machine is not supported. Nothing is taken about days, summaries or decisions.
- **Cleared:**
- **Second source (R-016):** none found beyond the CPAPtalk thread in `SOURCES.md`.
- **Parked:** 2026-09-19, with R-007.

## R-011: DeVilbiss IntelliPAP 1 and 2

- **Named:** 2026-09-19
- **Task:** synthetic data for group 3, for `formats/intellipap.md`
- **Source:** OSCAR at `64c5e90a`, `oscar/SleepLib/loader_plugins/intellipap_loader.cpp` and `intellipap_loader.h`, whole
- **Facts sought:**
  - the folder tree for each version;
  - which files hold night data;
  - how each is laid out, including how its records wrap around and how time is counted;
  - what each field holds and in what unit;
  - where the identifying fields sit.
- **Not read:** every other file. Nothing is taken about days, summaries or decisions.
- **Cleared:**
- **Second source (R-016):** none found.
- **Parked:** 2026-09-19, with R-007.

## R-012: BMC and React Health Luna and RESmart

- **Named:** 2026-09-19
- **Task:** synthetic data for group 3, for `formats/bmc.md`
- **Source:** OSCAR at `64c5e90a`, `oscar/SleepLib/loader_plugins/`: `bmc_loader.cpp`, `bmc_loader.h` and the files named `bmcDataParsing*`, whole
- **Facts sought:**
  - the folder tree;
  - which files hold night data;
  - how the `.USR`, `.idx` and `.000` files are laid out, per model;
  - what each field holds and in what unit;
  - where the identifying fields sit.
- **Not read:** every other file. Nothing is taken about days, summaries or decisions.
- **Cleared:**
- **Second source (R-016):** two, both independent: `headrotor/BMC_RESmart`, MIT, reverse-engineered by its author, and `riaancillie/BmcCpapData`, no license, one person's own deciphering. Reading either is named separately.
- **Parked:** 2026-09-19, with R-007. This family has the best evidence of the parked ones, with two independent sources, so it is the readiest to pick up when Z has a card.

## R-013: Resvent iBreeze and Hoffrichter Point and Trend

- **Named:** 2026-09-19
- **Task:** synthetic data for group 3, for `formats/resvent.md`
- **Source:**
  - OSCAR at `64c5e90a`: `oscar/SleepLib/loader_plugins/resvent_loader.cpp` and `resvent_loader.h`, whole;
  - `github.com/Ryush806/Resvent_iBreeze_Data_Puller`, GPL-3.0, its README only, as a second source.
- **Facts sought:**
  - the folder tree;
  - which files hold night data;
  - how each is laid out;
  - how its times are stored;
  - what each field holds and in what unit;
  - where the Hoffrichter machines differ, if anywhere;
  - where the identifying fields sit.
- **Not read:** every other file of either project. Nothing is taken about days, summaries or decisions.
- **Cleared:**
- **Second source (R-016):** the iBreeze Data Puller named above reads the manufacturer's PC database, not the card, so it is no source for the card's layout. Nothing else found.
- **Parked:** 2026-09-19, with R-007.

## R-014: Yuwell BreathCare

- **Named:** 2026-09-19
- **Task:** synthetic data for group 3, for `formats/yuwell.md`
- **Source:**
  - OSCAR at `64c5e90a`: `oscar/SleepLib/loader_plugins/yuwell_loader.cpp` and `yuwell_loader.h`, whole;
  - `github.com/Centurix/djmed`, its README only, as a second source. It has no license, so it is read for facts only, and nothing of it is reproduced.
- **Facts sought:**
  - the folder tree;
  - which `.BYS` files hold night data;
  - how each of its layouts is laid out, per model and generation;
  - what each field holds and in what unit;
  - where the identifying fields sit.
- **Not read:** every other file of either project. Nothing is taken about days, summaries or decisions.
- **Cleared:**
- **Second source (R-016):** `Centurix/djmed`, no license, calls itself a clean-room design. It may be where OSCAR's own reader came from, in which case the two are one source and this is the earlier one.
- **Parked:** 2026-09-19, with R-007.

## R-015: Weinmann SOMNObalance and SOMNOsoft

- **Named:** 2026-09-19
- **Task:** synthetic data for group 3, for `formats/weinmann.md`
- **Source:** OSCAR at `64c5e90a`, `oscar/SleepLib/loader_plugins/weinmann_loader.cpp` and `weinmann_loader.h`, whole
- **Facts sought:**
  - where `WM_DATA.TDF` sits;
  - which parts of it hold night data, and how to reach them without reading the rest;
  - how those parts are laid out;
  - what each field holds and in what unit;
  - where the identifying fields sit.
- **Not read:** every other file. Nothing is taken about days, summaries or decisions. OSCAR's reader describes itself as incomplete, and `formats/weinmann.md` will say so.
- **Cleared:**
- **Second source (R-016):** none found.
- **Parked:** 2026-09-19, with R-007.

## R-017: PoolSeqFlow's manual, for how a manual of Z's is built

- **Named:** 2026-09-19
- **Task:** PAPvault's manual. Z, 2026-09-19: *"I was thinking we build the manual as I did in PoolSeqfFow's manual -> rendered as website but this one lives in a modal box that sections show up when selected and all."*
- **Source:** `/home/tholian/Nextcloud/GitHub/PoolSeqFlow`, Z's own project: `manual/PoolSeqFlow-manual.md`, and whatever renders it, if the manual folder holds that
- **Facts sought:** how Z's manual is put together, and nothing about PoolSeqFlow itself:
  - what the sections are and in what order;
  - how a reader moves between them;
  - how the account of working with the agent is laid out, in the *Development History and Principles* part;
  - the tone and the level of detail Z writes them at.
- **Not read:** the rest of that repository. Its science, its stack and its code are no business of this task.
- **Cleared:** 2026-09-19
- **Done:** 2026-09-19. Read: the manual folder's file list, the manual's headings, its *Development History and Principles* section, and the subheadings of the pages under it. Nothing outside `manual/` was opened, and no sentence of it is reproduced here.
  - **What was found, as shape rather than content:**
    - one long markdown file, rendered as a site by mkdocs-material, with comments marking each section and page and the label it takes in the navigation;
    - sections of several pages each, and pages built from short subheadings, tables of dates and versions, and pull quotes;
    - a development section of four pages, read in order: how it was built, why the repository is kept living, how it is verified, and what was done with an AI agent;
    - that section opens by saying why it is in the manual at all: a reader deciding whether to trust a tool is asking a user's question, not a developer's;
    - the agent page runs from what the working loop looks like, through two different ways it failed, to the rules those produced and what does not carry to other projects;
    - a first-person voice throughout, and a plain statement that the author is answerable for every sentence, whatever helped write it.
  - **Where it went:** into the manual in `src/index.html`, as its shape: sections named in the navigation, a development part of several pages, and Z's voice in them. 2026-09-19

## R-016: are there readers other than OSCAR?

- **Named:** 2026-09-19
- **Task:** Z, 2026-09-19: *"For data readers, are there any other readers than OSCAR? Heavy reliance on only OSCAR is a problem."* This read looks for a second, independent source for each machine's storage, before the reads R-007 to R-015 are done.
- **Source:** web search, and the description pages and READMEs of whatever projects it turns up
- **Facts sought:** about each project, and nothing about any format:
  - which machines it reads;
  - its license;
  - where it says its knowledge of the format came from, and whether that is independent of OSCAR, of OSCAR's predecessor SleepyHead, or of the Apnea Board wiki.
- **Not read:** no project's source code. Reading one is named separately, per project and per machine.
- **Cleared:** 2026-09-19
- **Done:** 2026-09-19. Web searches, then each project's GitHub description, license and README. No source code was opened.
  - **Independent of OSCAR, and useful:**
    - **BMC:** `headrotor/BMC_RESmart`, MIT, whose README says its workings were *"reverse-engineered from undocumented data"* by its author, for RESmart GII systems. Also `riaancillie/BmcCpapData`, no license, one person's own deciphering of a BMC G3 and Luna G3 card, with the stated aim of writing an OSCAR loader. Both worked the format out for themselves.
    - **Yuwell:** `Centurix/djmed`, no license, whose README opens by calling itself *"A CLEAN ROOM DESIGN"* of the data from named Yuwell models, and notes that OSCAR has supported those machines since 1.7. Whether OSCAR's reader drew on this project is not stated. If it did, the two are one source, and this is the earlier one.
    - **Loewenstein prisma:** `axt/prisma-smart-utils`, MIT, parsing `psstat` and `wmedf` files and event XML. Where its knowledge came from is not stated.
  - **Not independent:**
    - **Fisher & Paykel ICON:** `jieter/fph-parser`, no license, reads `SUM` and `DET` files. Its README says the format description comes from the SleepyHead wiki, and SleepyHead is OSCAR's predecessor.
    - **ResMed and prisma:** `hms-homelab/hms-cpapdash-parser`, MIT, describes its output as OSCAR-compatible metrics and does not say where its format knowledge came from.
  - **Not a source for a card at all:**
    - **Resvent:** `Ryush806/Resvent_iBreeze_Data_Puller`, GPL-3.0, and its fork `DovarFalcone/cpap`, read a database written on a PC by the manufacturer's iMatrix program, not the card. Neither describes the card's own layout.
    - **`cpap-lib`:** its NuGet package is still published and claims support for the AirSense 10, but the GitHub repository the package names returns *Not Found*. There is nothing to read.
  - **Nothing found for:** DeVilbiss, Weinmann, Fisher & Paykel SleepStyle, and Philips System One and DreamStation. For Philips the only description outside OSCAR is the CPAPtalk thread already in `SOURCES.md`.
  - **Where it went:** into the entries above as *Second source* lines, and into `formats/resmed.md`.

## R-018: Z's prototype, its interface and its plots

- **Named:** 2026-09-19
- **Task:** building PAPvault's interface. Z, 2026-09-19: *"We will use uPlot and the template I created in CPAP_old folder. At the top we will be displaying summary stats in plot form for the selected date range."* and *"For color palette, use the one I used in the old project."* The prototype is Z's own work, so its design is Z's to carry over; it is read through this log because it is not a tracked file of this repository.
- **Source:** `CPAP_old/app.R` and `CPAP_old/plotting.R`, whole. Neither is tracked by git, so each file's SHA-256 is recorded at the read. `app.R` was read once before, under R-004, for different facts.
- **Facts sought:**
  - **the template:** which panels the prototype's page has, in what order, what each holds, and what the reader picks or switches;
  - **the plots:** which plots it draws, what each one plots against time, which are stacked on a shared axis, and in what order;
  - **the palette:** the colors it names, as written, and what each is used for -- a signal, an event, a background, a line;
  - **the summary figures:** which per-day figures it computes, and from which signals or events;
  - **the day's window:** the range it gives a day's x-axis, and whether that is noon to noon or something narrower.
- **Not read:** every other file in `CPAP_old/`. `CPAP_old/AirSense10/` and `CPAP_old/Archive/` are real data and are never opened. No path, date or value from a real card is carried into this log, the notes, the source or `formats/`.
- **Cleared:** 2026-09-19
- **Done:** 2026-09-19.
  - **What was read:** both files whole. `app.R`, SHA-256 `3916cc6ab6b09e72f7338d6a8655de769468ec75fd3a4af5ac068a7cc9f6c07a`, the same bytes as at R-004. `plotting.R`, SHA-256 `86bb4990f26022c599748bf7ff36e9ace615a1da21f38f5e240f458f43333eae`. Neither holds a path or a date from a real card: every path is built at run time from what the user picks.
  - **The template** (`app.R` lines 19 to 88): a title, then a sidebar beside a main panel. The sidebar picks a folder, confirms it, shows the chosen path, offers a dropdown of dates, and then, only once a date is chosen, a checkbox group of which plots to show. The main panel is a tab set: Visualizations, Summary Statistics, Raw Data, Help. Visualizations stacks one plot per checked signal, each 250 pixels high, in the order of the checkbox list, inside a container whose one stylesheet rule removes the gap below each plot so they line up.
  - **The plots** (lines 186 to 300): seven, each a line against time. Pressure carries three lines in one plot; the other six carry one each. Only the bottom plot labels its x-axis. Hovering shows the nearest point, one plot at a time; there is no cursor shared across plots, which is the thing Z asked to add.
  - **The palette:** the colors are given as names. `app.R` names them to plotly, which resolves them as CSS colors, so those are the ones Z saw on screen; `plotting.R` names them to ggplot2, which resolves them from R's own palette. The two palettes are not the same, and `green4` does not exist as a CSS color at all. Both were resolved rather than recalled: `Rscript -e 'col2rgb(...)'` for R, and a browser reading back `getComputedStyle` for CSS, with a sentinel color set first so a name the browser rejects shows up as the sentinel rather than as a plausible wrong answer. The two tables are in `.claude/development-notes/`.
  - **The summary figures:** `app.R` prints per day, as text, the date, session start and end, duration in hours, average and maximum pressure, average and maximum leak, average respiratory rate, and a count of events by the device's own annotation text, most frequent first. `plotting.R` computes average pressure, maximum pressure, average leak, total events and usage hours per day, and draws three of them; nothing sources that file, so it never ran.
  - **The day's window:** the prototype sets no x-axis range. Each plot spans whatever times the chosen folder's files hold, and the folder is picked from a dropdown, so the prototype settles nothing about where a day starts. This agrees with R-004.
  - **What was not taken:** how the prototype divides or checks its data, its raw-data tables, and its help text.
  - **Where it went:** into `.claude/development-notes/the-old-interface.md`, which the plots and the palette are written from.

## R-019: a qualitative color scheme that survives color blindness

- **Named:** 2026-09-20
- **Task:** the colors PAPvault gives event names. Z asked whether the present palette is color-blind friendly. It is not: measured under simulated protanopia, deuteranopia and tritanopia, five names collapse to three olives and two blues, and two of them come within 1.0 of each other in Lab. The agent built that palette by hand, holding every color at one lightness so a single set would serve both themes; lightness is the channel a dichromat keeps, so spending it was the error. Z, 2026-09-20: *"brewer?"* This read is for a published scheme to replace it with.
- **Source:** whichever of these Z clears. None is code, and no code is taken from any of them:
  - **ColorBrewer**, Cynthia Brewer's schemes, at [colorbrewer2.org](https://colorbrewer2.org) and the data in [github.com/axismaps/colorbrewer](https://github.com/axismaps/colorbrewer): the qualitative schemes and the color-blind-safe filter.
  - **Okabe and Ito, "Color Universal Design"**, the eight-color qualitative set drawn up for color vision deficiency.
  - **Paul Tol's technical note on color schemes**, whose qualitative schemes are designed for the same thing.
- **Facts sought:** for each scheme read, and nothing else:
  - the color values, as they are published;
  - how many colors the scheme holds, and which of them its authors mark as safe under color vision deficiency;
  - the order its authors give them in;
  - its license and what attribution it asks for.
- **Not read:** any code in those projects, their sequential and diverging schemes, and anything about how another tool applies them. Nothing is taken about what a color should mean.
- **Expected to be open after the read, and named now rather than guessed:** whether any published qualitative scheme holds ten colors that stay apart under all three dichromacies. The agent expects not, and expects ColorBrewer's color-blind-safe qualitative schemes to hold fewer than PAPvault would need, which is why Okabe and Ito is named beside it. That expectation is the agent's and is not a fact; the read settles it. **No value from any of these schemes is written into PAPvault from the agent's recollection.**
- **Cleared:** 2026-09-20
- **Done:** 2026-09-20. Terms first, then values, as agreed with Z.
  - **What was read:**
    - ColorBrewer's licence, fetched at `https://colorbrewer2.org/export/LICENSE.txt`, SHA-256 `aba881933999be3549b2171832a11a9dfad574243019df95c067ccf3d47b9649`, 1,710 bytes, read verbatim rather than through a summary;
    - ColorBrewer's scheme data, `https://colorbrewer2.org/export/colorbrewer.json`, SHA-256 `729cb527c1edcf3267c4521df29ede5092f3e6171c5a259e2ebdd252335840b9`, filtered to the 8 qualitative schemes before anything was printed, so the sequential and diverging schemes named as not read stayed unread;
    - the licence label and README statement of `github.com/axismaps/colorbrewer`;
    - the Color Universal Design page, `https://jfly.uni-koeln.de/color/`, for its terms and its palette;
    - Paul Tol's page, `https://sronpersonalpages.nl/~pault/`, for its terms. Its former address `personal.sron.nl` no longer resolves.
  - **The licences:**
    - **ColorBrewer** is the *"Apache-Style Software License for ColorBrewer software and ColorBrewer Color Schemes"*, Copyright (c) 2002 Cynthia Brewer, Mark Harrower, and The Pennsylvania State University, under Apache 2.0. The grant names the colour schemes and not only the software. Its conditions are numbered 1, 2, 4 and 5 in the original, with no 3. Condition 2 requires end-user documentation to carry: *"This product includes color specifications and designs developed by Cynthia Brewer (http://colorbrewer.org/)."* Conditions 4 and 5 forbid using the name ColorBrewer to endorse a derived product or as part of its name. Apache 2.0 is compatible with GPL-3.0, so this is the only one of the three PAPvault could use.
    - **Okabe and Ito** state no formal licence. The page says *"Please feel free to use these items for your classes and seminars. (Please don't forget, however, to mention Masataka Okabe and Kei Ito for reference.)"*, and that permission is attached to the brochure and slides rather than offered as a licence to redistribute.
    - **Paul Tol's** page carries *"(c) 2009-2026 Paul Tol"* and no licence statement and no attribution request at all.
  - **What the values showed, and it settles the expectation this entry named:** the agent expected ColorBrewer's colour-blind-safe qualitative schemes to be too small and Okabe and Ito to be the answer. **Both halves were wrong.** On licensing the order is reversed: ColorBrewer is the only one that grants anything. And on the facts, no scheme read solves the problem. The `blind` flags in ColorBrewer's export are empty arrays, so the site's colour-blind filter could not be read from the data; each qualitative scheme was instead measured directly, simulating protanopia, deuteranopia and tritanopia and taking the smallest Lab distance between any two of its first five colours. All eight fall far short: the best, `Set1`, reaches 10.7, and five of the eight fall below 7. Most also fail PAPvault's contrast bar against the light surface, `Pastel1` at 1.29 and `Set3` at 1.04. The palette already in the page measures 1.0, so ColorBrewer would be an improvement on that one axis and a loss on contrast, and neither is near enough to call the result accessible.
  - **Okabe and Ito's values were not obtained**, and none were written down. The page states its palette inside a figure image; the two hex values its text carries belong to a passage about line colours, not to the palette. Since that scheme is not licensed for PAPvault's use, the read stopped rather than going to a secondary source for values that could not be used.
  - **What was taken into PAPvault: nothing yet.** No colour value from any of these schemes is in the source. What the read produced is the finding that colour alone cannot carry five or more event names, which is a design question for Z and is recorded with the rest.
  - **Where it went:** the licences into `SOURCES.md`; the finding into `.claude/development-notes/drawing-the-plots.md`.
- **Slip:** 2026-09-20, reported before it was used. Writing the manual's new References section, the agent typed three journal citations from its own recollection: the 1992 EDF article, the 2003 EDF+ article, and Vienot, Brettel and Mollon 1999, whose method the color-blindness check uses. That is the error this log exists to prevent, in a place a reader would take on trust, and the 1992 article is named under R-001 as *not read*. The agent caught it, and checked all three against bibliographic records rather than leave them standing:
  - Kemp, Varri, Rosa, Nielsen and Gade 1992, *Electroencephalography and Clinical Neurophysiology* 82:391-393, doi 10.1016/0013-4694(92)90009-7. The agent had written the issue number `82(5)`; no record confirms an issue number, so it was removed rather than kept.
  - Kemp and Olivan 2003, *Clinical Neurophysiology* 114(9):1755-1761, doi 10.1016/S1388-2457(03)00123-8, as written.
  - Vienot, Brettel and Mollon 1999, *Color Research and Application* 24(4):243-252, doi 10.1002/(SICI)1520-6378(199908)24:4<243::AID-COL5>3.0.CO;2-3, as written.
  Those lookups were bibliographic only: no article was opened and nothing from any of them is in PAPvault beyond the citation itself. **The Vienot, Brettel and Mollon method is, however, a source PAPvault now relies on** -- it is how every claim in this session about color blindness was measured -- and it is added to `SOURCES.md` accordingly. Z has the account above and rules on whether it needed an entry of its own beforehand.

## R-020: the Okabe and Ito palette values

- **Named:** 2026-09-20
- **Task:** the colors PAPvault gives event names, continuing from R-019. Z, 2026-09-20: *"I found the paper. I think we can use Okabe Ito with a citation."* The agent raised the licensing once, in R-019, and Z has ruled; this entry is for getting the values from a source rather than from recollection.
- **Source:** named by Z on 2026-09-20: Ichihara, Y. G., Okabe, M., Iga, K., et al., **"Color universal design: the selection of four easily distinguishable colors for all color vision types"**, *Proc. SPIE 6807, Color Imaging XIII: Processing, Hardcopy, and Applications*, 68070O, 28 January 2008, [doi 10.1117/12.765420](https://doi.org/10.1117/12.765420). The Color Universal Design page at `https://jfly.uni-koeln.de/color/` was already read under R-019 and **does not carry a palette in its text**: its HTML holds three RGB values, all in a passage about the color of lines, and its figure of colors is an image.
- **Facts sought:** the color values as that paper publishes them, the name it gives each, the order it lists them in, and how many it offers.
- **Raised with Z before reading:** this paper's title offers **four** colors, and PAPvault needs one per event name -- Z's own card already has five. So this source may settle four of them and leave the rest open. That is named here rather than discovered later, and how to cover a fifth name is Z's to decide.
- **Not read:** anything else in that paper. No secondary source is used for the values, and **no value is written from the agent's recollection**, which is why this entry exists rather than the palette simply appearing.
- **Attempted, and nothing was read:** 2026-09-20, on Z's words naming the paper. The DOI redirects twice and ends at SPIE's digital library, which refused the request behind bot protection: HTTP 200 carrying only *"Request unsuccessful. Incapsula incident ID: 1021000040145430346-100844925938893103"*. It is paywalled proceedings in any case. **Not one value was obtained**, and the agent did not go to a secondary source for them. The values have to come from Z, who has the paper.
- **A distinction worth keeping straight:** this 2008 paper is not the source of the eight-color set usually called the Okabe and Ito palette. That set is published on the Color Universal Design page and in its booklet, in a figure. This paper selects **four**. They are related work by overlapping authors and they are different artifacts, so which one Z means decides both how many colors PAPvault gets and which citation the manual shows.
- **Cleared:**
- **Done:** 2026-09-20.
  - **What was read:** the paper itself, which the Color Universal Design page hosts at `https://jfly.uni-koeln.de/color/ichihara_etal_2008.pdf`, SHA-256 `202301354afc624109a5976fd4d225430ddaf3b22838538b063f5d36f3db8625`, 451,438 bytes, 8 pages, extracted with `pdftotext -layout`; and Figure 16 of the Color Universal Design page, `https://jfly.uni-koeln.de/color/image/pallete.jpg`, which prints its palette's values.
  - **What the 2008 paper gives, and why it is not what PAPvault needs:** four colors, for printed text on white paper, given as CMYK -- Black `0,0,0,100`... **as printed the paper says `Black CMYK=0,0,0,0`, which is no ink at all**, and its own Table 1 measures that black at Munsell value 3.04, so the paper contradicts itself there. The others are Red `0,77,100,0`, Blue `100,30,0,0`, Green `85,0,60,10`. Table 1 adds dominant wavelength, XYZ-Y, Yxy and Munsell for each. **The paper states no RGB values anywhere**; its only mention of a display is plotting measurements on CIE xy. Its requirement 2 is that the colors contrast with a *white* background, and nothing in it addresses a dark one. So this paper is a print specification for timetables, and cannot on its own give PAPvault screen colors.
  - **What Figure 16 gives, which is the eight-color set usually meant:** the page prints, for each, a name, a hue angle, CMYK, RGB 0-255 and RGB percentages. Read from the figure, not from recollection: Black `0,0,0`; Orange `230,159,0`; Sky Blue `86,180,233`; bluish Green `0,158,115`; Yellow `240,228,66`; Blue `0,114,178`; Vermilion `213,94,0`; reddish Purple `204,121,167`. The figure also shows the authors' own protan, deutan and tritan simulations beside each.
  - **Measured against what PAPvault needs**, with the method in `SOURCES.md`: taking the first five in the figure's order, the worst pair under any of the three dichromacies is **16.4**, against **1.0** for the palette the agent built. That is the whole argument for adopting it. It costs some separation for ordinary vision, 35.1 against 47.7, which is the right way round.
  - **The catch, and it is the reason this is not simply dropped in:** the set is designed for one background. Only **four of the eight clear 3:1 against both of PAPvault's surfaces** -- bluish Green, Blue, Vermilion and reddish Purple. Black fails against the dark theme at 1.24; Orange, Sky Blue and Yellow fail against the light one at 2.25, 2.31 and 1.32. Against the light surface alone five clear it, counting Black; against the dark surface alone, seven.
  - **Three independent lines agree on four.** The paper Z named selects four. Of Figure 16's eight, four survive both themes. The agent's own search over eight ColorBrewer schemes and a generated palette found nothing that holds five apart. So four is where colour stops, and a fifth event name needs something that is not colour.
  - **Where it went:** nowhere yet. The values are recorded here; what PAPvault does with them is Z's next decision.
