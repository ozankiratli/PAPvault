# The survey of machines

**Written 2026-09-19, against the tree at `f7dd53f`**, with `SOURCES.md` and the *What we take from other projects* section of `CLAUDE.md` written but not yet committed. Nothing here had been built into PAPvault.

Z asked for it before any format notes: *"how about we try to find the different formats and how the data is collected in different machines before we move on to format notes. I think it is kind of the work we would need to do."*

## How it was done

Four research agents ran at once, on Sonnet, as Z set: ResMed; Philips Respironics; Fisher & Paykel, DeVilbiss and Loewenstein/Weinmann; and everything else, with what the vendors' apps let a user export. Each used web search and web fetch only, was forbidden to open any local file, and marked every claim confirmed, reported or uncertain with a source. Their reports were then checked by the agent against a shallow clone of OSCAR's current source, `gitlab.com/CrimsonNape/OSCAR-code` at commit `64c5e90a26f91fb15868bcfcccde0c1e1522ac86` (2026-07-13). Every line number below is at that commit. What could not be checked against a primary source is marked *reported*: it rests on the survey alone.

Every source is listed in `SOURCES.md`. What PAPvault takes from them is knowledge, never code; the rule is in `CLAUDE.md`.

## What the check found wrong

The reports were mostly right. These were not, and they are the reason a report is checked before it is used.

- **The brief pointed at a frozen repository.** OSCAR's code moved from `gitlab.com/pholy/OSCAR-code`, last changed 2024-10-04, to `gitlab.com/CrimsonNape/OSCAR-code`. The agent's brief named the old one; the three agents still running were redirected, and each re-checked its OSCAR citations against the new one. The old tree also lacks the BMC, Yuwell and vREM readers.
- **Two projects cited for ResMed do not exist.** `dynacylabs/cpap-py` and `StagPoint/cpap-lib` return *Not Found* from GitHub; the agent had seen them only in search results. Neither is in `SOURCES.md`.
- **Two agents read a sampling interval as a sampling rate.** OSCAR's waveform `rate` is the milliseconds between samples: `event.cpp` line 54 times sample *i* at `m_first + i * m_rate`, though `event.h` line 185 comments the field as *"Waveform sample rate"*. So BMC's waveforms are 25 samples a second (`bmc_loader.cpp` lines 243 to 245, `1000/25.0`), not the 40 reported; and vREM's flow is 25 a second and its pressure one a second (`vrem_loader.cpp` lines 509 and 510, `40` and `1000`), not the 40 and 1,000 reported, which one report had called anomalous.
- **An F&P checksum is described two ways in one file.** `icon_loader.cpp` line 530 comments the header's last byte as an *"8 bit additive sum checksum"*; line 557 computes it by XOR from zero, and line 749, in another reader in the same file, by an additive sum from `0xff`. A mismatch is only logged. The report repeated the comment.
- **The prisma noon boundary is not in OSCAR.** `prisma_loader.cpp` has no noon logic. The claim that the machine files a night under the date it began, by a noon-to-noon rule, comes only from the README of `oscar-js`, which has no license, so it stands as reported.

## The machines

| Family | Where the data is | Format | Public knowledge of it |
|---|---|---|---|
| ResMed S9, AirSense and AirCurve 10 and 11 | SD card: `DATALOG/<YYYYMMDD>/`, `STR.edf`, `Identification.*` | EDF; events as EDF+ annotations | the EDF standard; OSCAR; `edf-importer`; Z's R prototype for the AirSense 10 |
| ResMed AirMini | no card; encrypted Bluetooth to its app | none on a card | *reported*: `airsupply` |
| Philips System One, DreamStation 1, DreamStation Go | SD card: `P-SERIES/<serial>/` | proprietary chunks | OSCAR; a CPAPtalk thread |
| Philips DreamStation 2 | SD card | the same chunks, encrypted | OSCAR only |
| Fisher & Paykel ICON | SD card: `FPHCARE/ICON/<serial>/` | proprietary (`SUM`, `DET`, `FLW` `.FPH` files) | OSCAR |
| Fisher & Paykel SleepStyle | the same, plus `REALTIME/HRD*.edf` | proprietary, and EDF for the waveforms | OSCAR |
| DeVilbiss IntelliPAP 1 and 2 | SD card: `SL/` or `DV6/` | proprietary; version 2's files wrap around | OSCAR |
| Loewenstein prisma SMART and SOFT | SD card: `<serial>/<date>/<session>/` | JSON, XML, and a variant of EDF | OSCAR; `oscar-js`, for facts only |
| Weinmann SOMNObalance and SOMNOsoft | SD card: `WM_DATA.TDF` | one proprietary file | OSCAR, whose reader says of itself that it *"needs significant work"* |
| BMC and React Health Luna, RESmart | SD card: `*.USR` with `.idx` and `.000` files | proprietary, little-endian | OSCAR |
| Resvent iBreeze, Hoffrichter Point and Trend | SD card: `THERAPY/RECORD/<month>/<day>` | proprietary, with key=value settings | OSCAR; the Resvent Data Puller |
| Yuwell BreathCare | SD card: `.BYS` files in four layouts | proprietary | OSCAR; `djmed`, for facts only |
| vTitan vREM | an app's export folder, `VREM*` with `PI.txt` and `DI.txt` | proprietary | OSCAR |
| Apex (Wellell), Breas Z1 and Z2, Transcend, Sefam | *reported*: SD card | unknown | none found anywhere |

Checked against OSCAR's source, by family:

- **ResMed:** the AirSense 11 recognized by model number 39000 and up (`resmed_loader.cpp` line 1266); the `DATALOG` folder (line 300); the five kinds of session file, with EVE and CSL read as annotations only (lines 2333 to 2358); `STR.edf` read with or without a `.gz` suffix (line 463), and 103 distinct summary labels looked up in it.
- **Philips:** the `P-SERIES` folder matched in any case (`prs1_loader.cpp` line 592); `PROP.BIN` or `properties.txt` per machine (lines 625 and 823); the 15-byte chunk header, its fields little-endian (`prs1_parser.cpp` lines 1014 to 1031); flow at five samples a second and oximetry at one (`prs1_loader.cpp` lines 2391 and 2396); the DreamStation 2's encryption handled by a class of its own (line 267), with AES-256 (line 400). The `last.txt` file one report named is not read by OSCAR; it comes from the CPAPtalk thread.
- **Fisher & Paykel:** the `FPHCARE` folder (`icon_loader.cpp` lines 29 to 80); `SUM`, `DET` and `FLW` files told apart by name (lines 310 to 315); flow at 50 samples a second (lines 643 to 648), in a file the machine *"Overwrites ... not appends to"* (line 647); timestamps packed into 32 bits and shifted back 54 seconds (lines 444 and 472); SleepStyle's marker and its `REALTIME/HRD` files (`sleepstyle_loader.cpp` lines 137 and 275 to 282).
- **DeVilbiss:** the DV54 needing the SmartLink attachment (`intellipap_loader.cpp` line 3); the `SL` and `DV6` folders (lines 53, 54 and 75); the wrap-around record pointer (lines 1126 to 1175); times counted from 2002-01-01 (line 287).
- **Loewenstein and Weinmann:** the prisma SOFT and SMART device IDs, `0x91` and `0x92` (`prisma_loader.cpp` lines 508 and 509); `config.pscfg`, `config.pcfg` and `therapy.pdat` (lines 36 to 38); `WM_DATA.TDF` (`weinmann_loader.cpp` line 59), a hard-coded serial number (line 142), and the reader's own verdict on itself (line 194).
- **BMC:** the `.USR`, `.idx` and `.000` files (`bmcDataParsing.cpp` lines 467, 471 and 622), read little-endian (line 656).
- **Resvent:** the `THERAPY` folder tree, and Hoffrichter's Point and Trend machines read the same way (`resvent_loader.cpp` lines 25 to 42); times stored eight hours off, which OSCAR adds back (line 194).
- **Yuwell:** the BreathCare generations and models (`yuwell_loader.cpp` lines 11 to 25), and the `.BYS` files (lines 42 to 74).
- **vREM:** the `VREM` folder with `PI.txt` and `DI.txt` (`vrem_loader.cpp` lines 83 to 93).

Not checked, and so *reported*: the Philips family and version table; every claim about the vendors' apps and portals; how the AirSense 11 writes to its card; the prisma card's layout below the serial folder and its EDF variant, both from `oscar-js`; the Yuwell file sizes; and anything about the four families at the foot of the table.

## Days

Only ResMed is known to divide its own data at noon. OSCAR files a ResMed timestamp before noon under the previous day (`resmed_loader.cpp` line 1117), and anchors each `STR.edf` summary day at noon (line 1394); a ResMed card's `DATALOG` folders are named by the date each night began. For prisma a noon-to-noon rule is reported, from `oscar-js` alone. For the rest, each session carries its own start time and the day is the reader's to assign, which for PAPvault is the CPAP day: noon to noon, named by the date it begins.

Most machines record the time on their own clock, with no time zone: ResMed, Fisher & Paykel and DeVilbiss, as OSCAR reads them. Resvent is the exception found, storing times eight hours off, which a reader has to add back.

## What the vendors' apps give

*Reported*, across every vendor the survey reached: apps and portals show summaries, not waveforms, and none was found to export full detail to the person using it. The card is the only complete source. Z has ruled the apps out as sources in any case: *"SD card stores the data. That's the source we rely on, not ResMed's buggy systems."*

## What could be supported

Which machines PAPvault claims to support is Z's decision. As the survey left them, they fall into groups by how their format is known, which decides how a reader of them could ever be checked.

- **Readable from a published standard, with an independent check.** ResMed S9, AirSense and AirCurve 10 and 11: EDF and EDF+ are published, and for the AirSense 10 Z's R prototype, reading through a separate EDF library, is ground truth.
- **Partly EDF.** Loewenstein prisma SMART and SOFT, and Fisher & Paykel SleepStyle's waveforms. The EDF parts can be read from the standard; the rest of each card is known from OSCAR, and for prisma also from `oscar-js`.
- **Known only through reverse engineering, unencrypted.** Philips System One, DreamStation 1 and Go; Fisher & Paykel ICON; DeVilbiss IntelliPAP; BMC and React Health; Resvent and Hoffrichter; Yuwell; Weinmann SOMNO, by OSCAR's own account incomplete. For each, OSCAR is the source and, for Yuwell and Resvent, one other project as well. A reader built from OSCAR's description and checked against synthetic data built from the same description checks only that the two agree with each other; without a real card, nothing checks that either agrees with the machine.
- **Not supported, by Z's decision:** the Philips DreamStation 2 and the Transcend machines, until Z can test on one.
- **Not possible for a reader of files:** the ResMed AirMini, which has no card, and the vREM, whose data reaches a computer only through its app.
- **Nothing public to build on:** Apex (Wellell), Breas Z1 and Z2, Sefam.

## Added later on 2026-09-19, against `cece505`

Z chose all three of the groups that can be read: *"I agree with groups 1, 2 and 3. dev/synthetic is good."* So PAPvault is to read ResMed S9, AirSense and AirCurve 10 and 11; Loewenstein prisma SMART and SOFT; Fisher & Paykel SleepStyle and ICON; Philips System One, DreamStation 1 and DreamStation Go; DeVilbiss IntelliPAP 1 and 2; BMC and React Health Luna and RESmart; Resvent iBreeze and Hoffrichter Point and Trend; Yuwell BreathCare; and Weinmann SOMNObalance and SOMNOsoft. The limit named above stands for the third group: until a real card is read, a reader of those formats has been checked only against a description.

The synthetic data is to be made by one Python standard-library script per format family under `dev/synthetic/`, committed, writing its output to `dev/synthetic/out/`, which git ignores.

## Added later on 2026-09-19, against `cece505`: ResMed only, and what the others are waiting for

Z narrowed the list to ResMed: *"Then, we will support only ResMed for now. I will try to put my hands on some other data personally, until then we will have it as development note."*

What changed between the decision above and this one, in one day:
- **Z set what may be taken from another project:** where the night files are, and, for a format that is not a standard, what each file holds. `CLAUDE.md` has the rule, and `other-projects.md` has how it came about.
- **A search for readers other than OSCAR** (`dev/READING-LOG.md`, R-016) found how thin the ground is. Only BMC and Yuwell have a reader that worked the format out independently. The Fisher & Paykel parser takes its description from OSCAR's predecessor. Nothing was found for DeVilbiss, Weinmann, SleepStyle or Philips. For Yuwell, OSCAR's own reader may descend from the independent project rather than the other way round.
- **So for most machines, one project is both the source and the only possible check.** That is the case `CLAUDE.md` already said the notes must name, and it is the reason the list is now one manufacturer long.

ResMed is different only because EDF is published and the R `edf` package is an implementation of it that nobody here wrote, and because Z has an AirSense 10 card to check against. Inside ResMed, the S9 and the 11 series still rest on OSCAR's label table alone.

**What a machine needs before it joins the list:**
1. **A card Z can test on.** That is the gate, and it is why the rest are parked.
2. **A cleared read** of how that machine stores its night data, through `dev/READING-LOG.md`. The entries are already named, R-007 to R-015, each carrying what R-016 found about its sources. Each is marked *Parked*.
3. **A format file**, `formats/<family>.md`, with each fact citing its entry.
4. **A generator and its cases**, by the steps in `CLAUDE.md` under *How synthetic data is made*.
5. **A run against the real card**, which is the only step that shows the reader agrees with the machine rather than with a description of it.

Nothing about the parked machines is deleted. The survey above, the log entries and `SOURCES.md` keep what was learned, so picking one up later starts at step 1 rather than at the beginning.
