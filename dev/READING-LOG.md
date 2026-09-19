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
