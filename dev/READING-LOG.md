# Reading log

Every source PAPvault is built from is read the same way. Z, 2026-09-19: *"When you need to read something for a specific purpose we need to name it, record it, clear it, and do it."* The rule, and what counts as a source, are in `CLAUDE.md` under *What we take from other projects*.

This file is where the second and third steps happen:
- An entry is written **before** anything in it is opened.
- **Z writes the *Cleared* line.** The agent never writes it.
- After the read, the agent adds a *Done* line saying what was found and where it went.

Nothing in an entry is rewritten afterwards; an entry only gains lines. The entry ID is what a fact in `dev/formats/` cites.

**`formats/` moved to `dev/formats/` on 2026-09-20.** Entries written before then cite the old path and are left as they were written, since an entry is never rewritten. The file says where it came from.

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
  - Vienot, Brettel and Mollon 1999, *Color Research and Application* 24(4):243-252, doi 10.1002/(SICI)1520-6378(199908)24:4<243::AID-COL5>3.0.CO;2-3, as written. Those lookups were bibliographic only: no article was opened and nothing from any of them is in PAPvault beyond the citation itself. **The Vienot, Brettel and Mollon method is, however, a source PAPvault now relies on** -- it is how every claim in this session about color blindness was measured -- and it is added to `SOURCES.md` accordingly. Z has the account above and rules on whether it needed an entry of its own beforehand.

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

## R-021: PoolSeqFlow's release and publishing workflow

- **Named:** 2026-09-20
- **Task:** how PAPvault publishes. Z, 2026-09-20: *"Since this is going to be published by GitHub Pages. I want to make sure that it is only published when a new version is published on GitHub. The website should not update with every push"*, then: *"We should use the system I have for PoolSeqFlow."* PAPvault has no CI at all today, so this is the first workflow it would carry.
- **Source:** the PoolSeqFlow checkout at `/home/tholian/Nextcloud/GitHub/PoolSeqFlow`, and only these:
  - `dev/scripts/` -- especially `prep-version.sh`, `bump-version.sh`, and `verify-archive.sh`;
  - `.github/workflows/` -- the workflow files, whichever exist;
  - whatever file holds its version, and the script or step that reads it;
  - the part of its `CLAUDE.md` or its development notes that states the release rules, if there is one. Its SHA-256 or commit is recorded for each file at the read, since it is a separate checkout.
- **Facts sought:**
  - what event publishes the site, and what is deliberately excluded;
  - what the workflow checks before it publishes, and which of those fail the run rather than warn;
  - how the version is held, and how a tag and that version are kept from disagreeing;
  - what permissions the workflow takes, and which actions it uses and how they are pinned;
  - the order of steps in a release, as Z performs it.
- **Not read:** everything else in that checkout. Nothing about Nextflow, nothing about that project's own science, no data of any kind, and none of its agent memory. **This is Z's own project, and the harness applies to it exactly as it does to any other**: PAPvault's `CLAUDE.md` says every source that is not a tracked file of this repository is named, recorded, cleared and done, and that is what this entry is for.
- **What this read may and may not produce:** facts about how a release is gated and what is checked. A workflow file copied across would be taking another project's code, which the rule forbids whoever wrote it; PAPvault's workflow is written here, from what this entry records.
- **Already written before this was named, and standing as a draft only:** `.github/workflows/publish.yml` and `dev/RELEASING.md`, drafted from GitHub's own documented behaviour and from PAPvault's `CLAUDE.md`, with nothing from PoolSeqFlow in them. If Z clears this read they are rewritten against what it finds; if Z declines, they stand or go on their own merits.
- **Cleared:** 2026-09-20
- **Corrected by Z, 2026-09-20, before the read, and the two sentences above are left standing as what was written:** the agent misstated the rule twice, saying that the no-copying rule "applies to it exactly as it does to any other" project and that a workflow carried across "would be taking another project's code, which the rule forbids whoever wrote it". Both are wrong. Z: *"The rule is about respecting others' intellectual properties."* It is not about the integrity of PAPvault's source, and it does not reach Z's own work. Z: *"Reading code from OSCAR and using it as the ultimate source is like getting someone's blueprints, making a photocopy and building a structure based on that. Copying or reading a workflow from my own repository is like using my own hammer to put a nail on the wall."* Z's architectures, workflows and scripts are Z's intellectual property and PAPvault uses them. Z adds that this is the same reason PAPvault stops at ResMed: *"That's where my contribution stops."*
- **What does still apply:** the harness. Z kept it and cleared this entry rather than waiving it, so the read is named, recorded, cleared and done like any other read outside this repository. What comes over is adapted rather than copied whole, because PAPvault is a different kind of program and that project is far larger -- not because a rule forbids it.
- **Not an exception:** Z, 2026-09-20: *"definitely don't say 'let's add an exception', because it is not about adding an exception. An exception needs to be added for a rule that exists. This one actually does not because it is already my work."*
- **Done:** 2026-09-20, at PoolSeqFlow commit `d4c40285e6473a82337f3d932fb1cbf8a384729a`.
  - **What was read**, each with the first sixteen hex digits of its SHA-256: `.github/workflows/release.yml` `d57848dce4678b9f`, `.github/workflows/ci.yml` `3701e24e9c3d85fd`, `.github/workflows/docs.yml` `8a8433ebedbca1e0`, `dev/scripts/bump-version.sh` `e24f8f85b52af452`, `dev/scripts/changelog-section.sh` `b978e8cae97a0019`, the header and step structure of `dev/scripts/prep-version.sh` `dbe39076b0840d53`, the head of `CHANGELOG.md`, and `dev/release-notes-tail.md`. `verify-archive.sh` was listed in this entry and **not read**: PAPvault ships one HTML file rather than a curated tarball, so it had nothing to answer.
  - **What publishes, and what does not.** A release publishes on `push: tags: ['v*']`, never on a push to a branch. `workflow_dispatch` runs the same job as a rehearsal: everything builds and is checked, and the publishing step alone is gated on `github.ref_type == 'tag'`, so a run before the tag exists proves the release would work. The site is a separate workflow there, deploying from `main` on paths, because the documentation is not the released artifact; in PAPvault the page **is** the artifact, so the two collapse into one.
  - **How the version is kept from drifting.** One place is the authority, and every other copy of the number is checked against it in both the release workflow and the pull-request checks; the run fails if any two disagree. On a tag, `${GITHUB_REF_NAME#v}` must equal the declared version. The point is stated in a comment as a reason rather than a rule: nothing in the tool forces the copies to move together, so a check does.
  - **The changelog is a release gate.** The workflow extracts the section for the version being released and fails if it is absent or empty, **using the same script that writes the release body**, so the gate cannot pass something the body step would then fail on. The extractor matches the heading as a literal string, not a regular expression, because `## [3.0.1]` as a pattern also matches `## [3.0.10]`; and the version reaches `awk` through `ENVIRON` rather than `-v`, which would process escape sequences in the value. It exits non-zero with nothing on stdout when there is no section.
  - **The release body** is that section followed by a standing tail kept in `dev/release-notes-tail.md`, with `@VERSION@` and `@NAME@` substituted. The tail is a file rather than YAML or a heredoc because it is markdown full of backticks and fenced blocks, which both mangle.
  - **`bump-version.sh` does not commit, tag or push; it prints those commands.** It takes the new version, refuses a version that is unchanged or already has a section, collects every commit since the last tag with `git log --no-merges --reverse --pretty='- (%h) %s'`, and prepends a `## [x.y.z] - <date>` section holding them under a `### Commits` heading, followed by `---`. It adds the matching Markdown reference-link definition at the foot, taking the base URL from the newest existing definition so it follows the repository. It rewrites each place the version lives and then greps to confirm each rewrite took. Its own comment says release notes are added **above** the `### Commits` heading, never over it, so the commit list stays as the record of what landed.
  - **The changelog format** is Keep a Changelog with Semantic Versioning, and it opens by stating what the project's public API actually is, so a version number is not a judgment call. Each section leads with a plain-language line saying what upgrading costs.
  - **How Pages is deployed:** `actions/configure-pages` (which fails early and clearly when Pages is not enabled), then `actions/upload-pages-artifact`, then `actions/deploy-pages` in a second job with the `github-pages` environment; `permissions: contents: read, pages: write, id-token: write`; `concurrency: group: pages, cancel-in-progress: false`; and the one-time repository setting Source -> GitHub Actions, which is noted at the top of the file. A pull request builds but does not deploy.
  - **Action versions in use there:** `actions/checkout@v7`, `actions/setup-python@v5`, `actions/configure-pages@v6`, `actions/upload-pages-artifact@v5`, `actions/deploy-pages@v5`, and `softprops/action-gh-release@v3`. The agent's draft had named older ones from its own recollection: `checkout@v4`, `upload-pages-artifact@v3`, `deploy-pages@v4`. **That is the read earning its place** -- three version numbers that would have been wrong.
  - **What was left behind as not applicable:** `prep-version.sh` prepares and proves conda environments, which PAPvault has none of; the curated `git archive` tarball and its `export-ignore` rules, since PAPvault ships one file; and the analysis-version gate. Its principle -- prepare, prove, then record what was proven, and print the next commands rather than running them -- is what carried over.
  - **Where it went:** `.github/workflows/publish.yml`, `dev/scripts/bump-version.sh`, `dev/scripts/changelog-section.sh`, `dev/release-notes-tail.md`, `CHANGELOG.md` and `dev/RELEASING.md` in this repository, all written here for one HTML file and one `VERSION` file. Nothing was copied across.

## R-022: the AirSense 10's own documentation, for what the machine does

- **Named:** 2026-09-22
- **Task:** a realistic five-night card, for people to download and try the website with before they plug in their own. Z, 2026-09-22, on what it is for: *"Provide a test data for potential users to test the website before using it. They will be able to download it and use it on the website to test it."* Everything generated so far is deliberately unrealistic, on Z's instruction of 2026-09-19 that generated data need not look real. A card strangers will open is a different thing: it is published, so what it shows has to be defensible, and the only alternative to a source is the agent's recollection, which `CLAUDE.md` forbids for what a device value means.
- **Source:** ResMed's own published documentation for the AirSense 10 AutoSet -- the clinical or clinician's guide, and the user guide if the clinical one does not carry the figures. From ResMed's document library on `resmed.com`. **The exact URL, document title, revision and the date read go on the Done line**, since the library is versioned and a link goes stale.
- **Facts sought:** what the machine itself does, so a generated night is a night that machine could have written.
  - the therapy pressure range it delivers, and the step it moves in;
  - EPR: what it is, its levels, and whether it lowers pressure on exhale only;
  - in AutoSet mode, whether pressure responds to events, by how much, how quickly, and how it returns;
  - what the device calls the events it records, if the guide names them at all;
  - what its leak figure is -- its unit, and whether it is total or unintentional leak -- and any figure the guide declares about it;
  - whether the guide states a sampling interval for anything, which would replace a generator's choice in `dev/formats/resmed.md`.
- **Not read:** anything clinical -- no indication, no titration advice, no interpretation of a number, nothing about what a reading means for a person. No cloud or myAir section: Z settled on 2026-09-19 that a manufacturer's portal is not a source. No troubleshooting, no parts, no warranty.
- **What this read may and may not produce:** figures about the device, cited, for `dev/synthetic/realistic-night.md`. It produces nothing PAPvault displays, concludes or advises, and no threshold PAPvault applies to a reading -- the page has none of its own and this cannot give it one.
- **Cleared:** 2026-09-22
- **Limited by Z with that clearance, 2026-09-22:** *"No reading into other CPAP readers like OSCAR etc. The scope is important here."* So this read reaches the manufacturer's own document and nothing that is another program for this data: not its source, not its documentation, not a page or a thread that reproduces either. A search result that turns out to be one of those is not opened, and opening one by accident is a slip, stopped and recorded here as one.

## R-023: what an apnea and a hypopnea look like in a flow trace

- **Named:** 2026-09-22
- **Task:** as R-022. The generated night has to show, in the flow, the event its annotation names: an apnea annotation over flow that stops, a hypopnea over flow that halves. Today the annotation and the flow beneath it have nothing to do with each other, so anyone who knows this data sees a sine wave under an apnea.
- **Source:** the scoring rules for these events, in signal terms, from an open-access peer-reviewed source that states them. The AASM manual is the authority and is not freely readable, so what is read is an open-access article or chapter that reproduces the definitions. **Found through a PubMed or Europe PMC search, and only open-access full text is opened; the full citation, its DOI and the date read go on the Done line.**
- **Facts sought:** five things, and nothing else.
  - the flow reduction and the duration that define an apnea;
  - the flow reduction and the duration that define a hypopnea, and whether it requires an oxygen desaturation and of how much;
  - how long after an event a desaturation appears, if the source states it;
  - what distinguishes an obstructive event from a central one in the flow trace, for shaping only;
  - what flow limitation looks like in the inspiratory part of a breath.
- **Not read:** everything about people. No prevalence, no risk, no outcome, no treatment, no severity banding, and no threshold that turns a count into a judgment -- `CLAUDE.md`'s *It displays; it does not conclude* stands, and a source that would let the page grade a night is out of scope by design. No patient data of any kind.
- **What this read may and may not produce:** the shape of an event in a generated signal, cited. It may not produce anything the page says about an event, and PAPvault still shows the words the device wrote and adds nothing.
- **Cleared:** 2026-09-22
- **Limited by Z with that clearance, 2026-09-22:** *"No reading into other CPAP readers like OSCAR etc. The scope is important here."* So this read reaches peer-reviewed literature and nothing that is another program for this data: not its source, not its documentation, not a page or a thread that reproduces either. A search result that turns out to be one of those is not opened, and opening one by accident is a slip, stopped and recorded here as one.

## R-024: what ordinary breathing looks like in numbers

- **Named:** 2026-09-22
- **Task:** as R-022. Between the events, the flow has to be breathing: a rate, a volume, an inspiration shorter than its expiration, and a curve with its peak in the right place. The derived channels are then arithmetic over that flow -- breaths counted for the rate, inspiratory flow integrated for the tidal volume, their product for minute ventilation -- so if the breath is wrong, four signals are wrong together and consistently, which is the hardest kind of wrong to notice.
- **Source:** an open-access physiology reference for adult resting and sleeping respiration -- NCBI Bookshelf or an open-access review. **The citation and the date read go on the Done line.**
- **Facts sought:**
  - respiratory rate for an adult at rest, and asleep if the source separates them;
  - tidal volume at rest;
  - the ratio of inspiratory to expiratory time;
  - the shape of one breath's flow-time curve: where the peak falls in each half, and how the two halves compare;
  - peak inspiratory flow in a resting adult, in L/min;
  - resting oxygen saturation and pulse, for the oximetry channels the card carries even though the page has them turned off.
- **Not read:** anything about disease, measurement in patients, or what a value outside these ranges means.
- **What this read may and may not produce:** the numbers a breath is drawn from, cited and marked as a range the generator picks within. Nothing here reaches the page.
- **Cleared:** 2026-09-22
- **Limited by Z with that clearance, 2026-09-22:** *"No reading into other CPAP readers like OSCAR etc. The scope is important here."* So this read reaches a physiology reference and nothing that is another program for this data: not its source, not its documentation, not a page or a thread that reproduces either. A search result that turns out to be one of those is not opened, and opening one by accident is a slip, stopped and recorded here as one.

### R-022, answered in part before the read

- **2026-09-22, from Z:** the words an `EVE` file holds are `Arousal`, `Apnea`, `Central Apnea`, `Hypopnea` and `Obstructive Apnea`. That was one of the facts this entry sought, and it is no longer sought from ResMed's documentation; it is recorded in `dev/formats/resmed.md` as Z's. The rest of the entry stands as written.
- **2026-09-22, corrected by Z the same day:** the list above is two words short. Z: *"I was wrong. They are true events: Cheyne-Stokes Respirations. We keep them."* So an `EVE` file also holds `CSR Start` and `CSR End`, and PAPvault treats them as it treats every other word a file carries -- nothing filters them, nothing pairs them into one, and no code changed when they were added. The line above stands as it was written. `dev/formats/resmed.md` carries the full list of seven and `docs/manual.md` explains to a reader why two rows of equal length appear in the event chart.

### R-022, done

- **Done:** 2026-09-22. **What was read:** *Clinical guide, English -- AirSense 10 AutoSet, AutoSet for Her, Elite, CPAP*, ResMed, document number `378519/6 2020-10`, 44 pages, fetched from `https://www.resmed.com.au/hubfs/airsense-10-autoset-afh-elite-cpap-clinical-guide-apac-eng.pdf`, SHA-256 `ec3e739f125a5866be87d3ee7d1f9a70f6450e8de465307de53e5a3ac673546e`, text extracted with `pdftotext -layout`. Only these sections were read: *Therapy information* (AutoSet mode, CPAP mode, Reporting), *Comfort features* (Expiratory Pressure Relief, AutoSet Response), the *Settings menu* tables, *Sleep Report screen parameters*, *Data storage*, and *Displayed values* in the technical specifications. A second guide, for the AirSense 10 "Plus" range, was fetched at the same time (`https://ap.resmed.com/hubfs/...AirSense10_ClinicalGuide_EN.pdf`, SHA-256 `36839d65d3406d9a53f71093fa4a64e22a4081217ae6b8f348125372fa30b284`) and **was not read** beyond its table of contents; the four-model guide covers the AirSense 10 and the Plus range is a different product.
- **What was found, for `dev/synthetic/realistic-night.md`:**
  - **How the machine moves pressure.** AutoSet "adjusts treatment pressure as a function of three parameters: inspiratory flow limitation, snore, and apnoea", breath by breath. An obstructive apnea makes it raise pressure; on a central apnea "the device responds appropriately by not increasing pressure". `Response` is settable `Standard / Soft`. No rate of rise in cm H2O per minute is stated anywhere in the guide.
  - **What a normal breath looks like, in the device's own words:** "the inspiratory flow measured by the device as a function of time shows a typically rounded curve for each breath", and as the airway begins to collapse "the shape of the inspiratory flow-time curve changes".
  - **EPR** reduces delivered mask pressure during exhalation only, at levels `1 / 2 / 3 cm H2O`, `Full Time` or `Ramp Only`, and "the delivered pressure will not drop below a minimum pressure of 4 cm H2O regardless of the settings". Mask pressure is displayed over `4-20 cm H2O` at `0.1 cm H2O` resolution; ramp start pressure moves in `0.2 cm H2O` increments.
  - **The device's own event rules**, from *Sleep Report screen parameters*: "An apnoea is when the respiratory flow decreases by more than 75% for at least 10 sec. A hypopnoea is when the respiratory flow decreases to 50% for at least 10 sec." These are the rules that wrote the events on a card, and they are **not** the AASM rules of R-023.
  - **Cheyne-Stokes, in numbers**: "a periodic waxing and waning of respiration. The waxing periods (hyperpneas, typically 40 seconds in length) ... while the waning periods (hypopnoeas or apnoeas, typically 20 seconds in length) cause blood oxygen desaturations." And: "The AirSense 10 device reports **the time during therapy in which it detected** breathing patterns indicative of CSR." That is what a `CSR Start` and a `CSR End` bracket.
  - **Central apnea detection adds a signature to the pressure trace:** when an apnea is detected, "small oscillations in pressure [1 cm H2O (1 hPa) peak-to-peak at 4 Hz] are added to the current device pressure". At 25 Hz that is representable in `Press.40ms`.
  - **RERA** is "periods of increasing respiratory effort which are terminated by an arousal. Increasing respiratory effort will be seen as airflow limitation."
  - **Leak**, from *Displayed values*: range `0-120 L/min`, display resolution `1 L/min`; accuracy "+/-12 L/min or 20% of reading, whichever is greater, 0 to 60 L/min". Flow accuracy is quoted "at 0 to 150 L/min positive flow".
  - **A figure the device declares about leak**, in its own Sleep Report: mask seal is "Good -- if the 70th percentile leak is less than 24 L/min". **Recorded as the device's and not adopted.** PAPvault applies no threshold of its own and this does not give it one.
- **Two findings that reach past this entry, and are raised rather than acted on:**
  1. **The guide independently confirms the sampling intervals this project took from another project.** Its *Data storage* section states "High resolution flow and pressure data ... (25 Hz - every 40 ms)", and its detailed-data table gives `1/2 Hz (2 sec)` for flow limitation, leak, minute ventilation, pressure and snore, and `1 Hz (1 sec)` for pulse rate and SpO2. `dev/formats/resmed.md` says under *Open* that OSCAR is the only source for the label spellings and so cannot be their own check. That is still true of the **spellings**, but the **intervals those spellings encode** -- `40ms`, `2s`, `1s` -- now have a source that is not OSCAR and not Z's prototype. The same table lists apnea/hypopnea events, CSR and RERA as `aperiodic`, which is consistent with them being annotations rather than sampled signals.
  2. **A unit disagreement inside the same document, which is Z's to settle.** The detailed-data table names the stored signal **`Leak (L/sec)`**, while *Displayed values* gives the leak range as **`0-120 L/min`**. `dev/synthetic/resmed.py` writes `Leak.2s` in `L/min` over `0-120`, which the guide supports for the displayed value and contradicts for the stored one. PAPvault itself reads the unit out of each file's header and is right either way, but a card generated for other people to open asserts a unit, and asserting the wrong one would teach a reader something false. **Not guessed.** Only a real card's header says which it is.
- **What was not read:** the indications, contraindications and adverse effects; all titration and clinical advice; setup, cleaning, reprocessing, troubleshooting, device messages, warnings, parts and warranty; anything about AirView, ResScan or remote monitoring beyond the one table naming what is stored and how often.

### R-023, done

- **Done:** 2026-09-22. **What was read:** the PubMed record of Berry, R. B., Budhiraja, R., Gottlieb, D. J., et al., **"Rules for scoring respiratory events in sleep: update of the 2007 AASM Manual for the Scoring of Sleep and Associated Events. Deliberations of the Sleep Apnea Definitions Task Force of the American Academy of Sleep Medicine"**, *Journal of Clinical Sleep Medicine* 8(5):597-619, 2012, PMID 23066376, PMC3459210, [doi 10.5664/jcsm.2172](https://doi.org/10.5664/jcsm.2172).
- **The full text was not opened, and is not open access.** PubMed Central reports `(c) 2012 American Academy of Sleep Medicine` with no license and `is_open_access: false`, and the full-text request returned nothing. **Every fact below is from the abstract**, which is the freely distributed record of the article. The entry said open-access full text only; the abstract is what was available and it is what was used, and that is stated here rather than left to be assumed.
- **What was found:**
  - **Apnea, adults:** "a drop in the peak signal excursion by >= 90% of pre-event baseline using an oronasal thermal sensor (diagnostic study), **PAP device flow (titration study)**, or an alternative apnea sensor, for >= 10 seconds".
  - **Hypopnea, adults:** "the peak signal excursions drop by >= 30% of pre-event baseline using nasal pressure (diagnostic study), **PAP device flow (titration study)**, or an alternative sensor, for >= 10 seconds in association with either >= 3% arterial oxygen desaturation or an arousal".
  - **Cheyne-Stokes breathing, adults:** "episodes of >= 3 consecutive central apneas and/or central hypopneas separated by a crescendo and decrescendo change in breathing amplitude with a cycle length of at least 40 seconds (typically 45 to 90 seconds)", and "five or more central apneas and/or central hypopneas per hour associated with the crescendo/decrescendo breathing pattern recorded over a minimum of 2 hours of monitoring".
  - **The flow signal a PAP machine records is the sensor these rules are written against**, not a substitute for one: "The PAP device flow signal is the recommended sensor for the detection of apnea, hypopnea, and respiratory effort related arousals (RERAs) during PAP titration studies."
  - **Obstructive against central is a question of effort, not of flow shape.** The rule quoted for a central apnea turns on "an absence of inspiratory effort throughout the event". Effort is not in the flow signal, and a ResMed card carries no effort channel, so **a generated flow cannot and should not show the difference**; the annotation is what differs. R-022 says how the machine tells them apart instead -- it adds a 4 Hz pressure oscillation and watches the airway's response.
- **What was not found, and is a gap rather than a guess:** what inspiratory flattening looks like as a shape, in numbers. The abstract mentions filter settings "to facilitate visualization of inspiratory flattening" and defines nothing. One candidate paper, PMID 19349649, has no PMC record, so it was not opened. R-022 supplies the device's own qualitative statement -- a normal breath is "a typically rounded curve" and flow limitation is that curve's shape changing -- and that is all this project has.
- **Which rule the generator follows, named here so it is not decided quietly:** the events on a card were written by the machine under **the machine's** rules (R-022: more than 75% for at least 10 seconds; to 50% for at least 10 seconds), not under the AASM's. The AASM rules are the general standard and are recorded for context.

### R-024, done

- **Done:** 2026-09-22, and it came back mostly empty.
- **Attempted and not read:** StatPearls on the NCBI Bookshelf, `Physiology, Tidal Volume` (NBK482502) and `Physiology, Respiratory Rate` (NBK537306). Both refuse automated requests: `curl` and the agent's fetch tool each received a reCAPTCHA interstitial, 21,357 and 21,359 bytes, carrying no article text. **Nothing was taken from them**, and in particular nothing was taken from a search engine's summary of them, which is not a source.
- **What was found:** Pinkham, M., Burgess, R., Mundel, T., and Tatkov, S., **"Nasal high flow reduces minute ventilation during sleep through a decrease of carbon dioxide rebreathing"**, *Journal of Applied Physiology* 126(4):863-869, 2019, PMID 30730818, [doi 10.1152/japplphysiol.01063.2018](https://doi.org/10.1152/japplphysiol.01063.2018). In nine healthy males **during sleep**, measured with calibrated respiratory inductance plethysmography, baseline **tidal volume was 415 mL, SD 114**. The paper also states that nasal high flow "reduces the tidal volume but does not affect the respiratory rate during sleep", giving no rate.
- **Still open after this read**, and going to Z rather than to the nearest source: **respiratory rate** for a sleeping adult; the **ratio of inspiratory to expiratory time**, or the duty cycle; **peak inspiratory flow**; and **resting oxygen saturation and pulse**. Searches for each returned either nothing or papers about other questions, and the one usable shape fact came from the manufacturer instead -- R-022's "typically rounded curve".
- **What this means for the generator:** a breath can be drawn from a tidal volume that is sourced and a shape that is the generator's own, with the rate and the timing marked in `dev/synthetic/realistic-night.md` as the generator's choices, which `CLAUDE.md` already requires for any value no source gives. A reader must not depend on them. Z decides whether to supply the four numbers, to accept choices, or to have the case say less.

### R-024, the gap it left, closed by Z

- **2026-09-22, from Z**, which is where a gap goes when the sources cleared for it come back empty: respiratory rate is *"generally between 10-20 in normal times"*; the ratio of inspiratory to expiratory time is *"1"*; flow runs *"between +-0.25 to +-0.5"*, read as liters per second and flagged as such in `dev/synthetic/realistic-night.md` in case that reading is wrong. **The two oximetry figures are not needed at all**: Z, *"No oximeter data is needed. I told you before, we MUST treat oxymeter as an undeveloped feature."* The sample card will carry no `SAD` file.
- **And the unit question R-022 raised is settled without needing a real card.** Z: *"It does not matter. We should convert our leak signal to L/min -> it is more readable. That's what people can understand. 60 x L/s simple math."* So the page converts a leak recorded per second into liters per minute and says so in `docs/manual.md`. Which unit a file holds is still read from that file's own header.
