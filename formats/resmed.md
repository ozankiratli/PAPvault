# ResMed: how the night data is stored

**Kept current; its history is in git.** This file covers the ResMed S9, the AirSense and AirCurve 10, and the AirSense and AirCurve 11. It says how their night data is stored, as far as the cleared reads in `dev/READING-LOG.md` establish it.
- Every fact cites the entry it came from, and where in that source it sits.
- What no cleared source establishes is either listed under *Open* or marked as the generator's choice.

The synthetic data generator is written from this file and nothing else. PAPvault's reader is written from it later.

The **AirSense 10** is described through the EDF specifications (R-001, R-002) and Z's prototype (R-003, R-004).

For the S9 and the 11 series, another tool's reader (R-006) adds three things: the folder and file names, two more kinds of file, and the labels each signal can carry. It does not say which series writes what; see *Across the series*. OSCAR is the only source for those facts, so it cannot also be their check. Only a real S9 or 11-series card can be.

## What is read, and what never is

Only night data is read, and nothing identifying is touched (`CLAUDE.md`, *It reads the night, and nothing that identifies*):
- **Never opened on a ResMed card:** `STR.edf`, `Identification.*`, `SETTINGS/`, `Journal.dat` and the `.crc` files.
- **Never decoded:** the patient and recording fields of every EDF header.

## Where the night files are

- **The `DATALOG` folder.** The person chooses the card's root folder, and the night files sit in a folder named `DATALOG` directly inside it. (R-004, `app.R` lines 137 to 140)
- **One folder per day.** Each folder inside `DATALOG` holds one day's files, and the prototype offers each as a day under its own name. (R-004, lines 141 to 145 and 153)
- **Folder names are dates.** A day folder's name is eight characters, a date written `yyyyMMdd`. (R-006, `resmed_loader.cpp` lines 1037 and 1038)
- **Which files count.** A day's files are the files in its folder whose names contain `edf`. (R-004, line 154)
- **File names.** A file's name begins with the date and time, `yyyyMMdd_HHmmss`, as its first two parts separated by underscores (R-006, lines 1112 and 1113). Its kind is the last underscore-separated part, before the extension (R-006, line 2332). So a name reads `yyyyMMdd_HHmmss_KIND.edf`. The `.edf` ending is consistent with R-004's `edf` pattern; neither source states it outright.
- **Five kinds of file.** The prototype tells them apart by the kind's three letters appearing in the path: `EVE`, `CSL`, `BRP`, `PLD` and `SAD`. (R-003, `data_prep.R` lines 6, 24, 41, 77 and 118)
- **Two more kinds, from another tool's reader.**
  - `SA2` is read as `SAD` is.
  - `AEV` is recognized as a kind of its own, and nothing in the cleared lines says what it holds.
  - Neither source says which series writes either one. (R-006, lines 2333 to 2345)
- **`EVE` and `CSL` hold only annotations.** Two sources agree on this: R-003, which reads only events from them, and R-006, line 2358.
- **Any number of each kind per day.** The prototype reads every file of each kind in a day's folder. (R-003, lines 8, 26, 44, 80 and 121)

## Every file is EDF

### The header (R-001)

The header is 256 bytes, followed by 256 bytes for each signal. It is ASCII, each field left-justified and padded with spaces. The byte offsets below follow from the widths the specification gives.

| Bytes | Field | Notes |
|---|---|---|
| 0 to 7 | version | `0` |
| 8 to 87 | patient identification | **identifying: skipped, never decoded** |
| 88 to 167 | recording identification | **identifying: skipped, never decoded** |
| 168 to 175 | start date | `dd.mm.yy` |
| 176 to 183 | start time | `hh.mm.ss` |
| 184 to 191 | header length in bytes | 256 + 256 x the number of signals |
| 192 to 235 | reserved | in EDF+, begins `EDF+C` or `EDF+D` (R-002, 2.1.1) |
| 236 to 243 | number of data records | |
| 244 to 251 | duration of a data record, in seconds | |
| 252 to 255 | number of signals | |

After those 256 bytes, each field below appears once for every signal, in signal order. All the labels come first, then all the transducer types, and so on.

| Width per signal | Field |
|---|---|
| 16 | label |
| 80 | transducer type |
| 8 | physical dimension (the unit) |
| 8 | physical minimum |
| 8 | physical maximum |
| 8 | digital minimum |
| 8 | digital maximum |
| 80 | prefiltering |
| 8 | number of samples in each data record |
| 32 | reserved |

EDF+ adds rules for what those fields hold (R-002, 2.1.3):
- **Characters:** only bytes 32 to 126 are allowed in the header. (item 1)
- **Years:** 85 to 99 mean 1985 to 1999, and 00 to 84 mean 2000 to 2084. (item 2)
- **Number format:** no digit grouping, and a dot for the decimal point. (item 6)
- **Extremes:** the digital maximum is larger than the digital minimum, and the physical maximum differs from the physical minimum. (item 5)
- **Start time:** it is local time where the recording was made. No time zone is stored. (item 8)
- **Anonymous identification:**
  - An anonymous patient field starts `X X X X`. (item 3)
  - An anonymous recording field starts `Startdate X X X X`. (item 4)

### The data records (R-001)

- **What a record holds:** each data record holds one record duration of every signal, in header order. It holds as many samples of each signal as the header gives for it.
- **How a sample is stored:** each sample is a 2-byte two's complement integer (R-001), little-endian (R-002, 2.1.3 item 7).
- **Calibration:** the digital minimum and maximum correspond to the physical minimum and maximum, and together they fix the signal's offset and gain (R-001). From that correspondence it follows that `physical = physical minimum + (digital - digital minimum) x (physical maximum - physical minimum) / (digital maximum - digital minimum)`. The formula is derived here; the specification states only the correspondence.
- **Interval between samples:** the record duration divided by the number of samples in each record (R-001).
- **Continuous files:** in an `EDF+C` file the records are contiguous, and the recording ends (number of records x record duration) seconds after its start (R-002, 2.1.1).
- **Interrupted files:** in an `EDF+D` file each record's start is given by its time-keeping annotation (R-002, 2.2.4).
- **Start of the first record:** the header's start date and time give the second in which the first data record starts (R-002, 2.2.4).

### Events: the annotation signal (R-002, 2.2)

- **The signal:** a signal labeled `EDF Annotations` carries text instead of samples. Its number of samples counts 2-byte units, filled with bytes in order. Its digital minimum and maximum are -32768 and 32767, its physical minimum and maximum differ, and its other fields are spaces. (2.2.1)
- **The lists:** the text is a series of time-stamped annotation lists (2.2.2).
  - A list reads `+onset`, then optionally byte 21 followed by the duration, then byte 20. Then come one or more annotations, each followed by byte 20. A byte 0 closes the list.
  - The onset is in seconds from the file's start, with a leading `+` or `-`.
  - The duration has no sign.
  - Either may have a fractional part after a dot.
- **Placement within a record:** the first list starts at the first byte of the signal, and each next list follows directly. No list crosses into another record, and unused bytes are 0. (2.2.2)
- **Time keeping:** the first annotation in each record is empty, and its onset is the record's start (2.2.4). In a file with no ordinary signals, a non-empty annotation in that same list names the event that defines the record's start (2.2.4). Such a file has a record duration of 0 (2.1.2).
- **Annotation text:** it is UTF-8. Of bytes 0 to 31, only tab, line feed and carriage return are allowed. The same event always carries the same text. (2.2.3)

## What each kind holds on the AirSense 10, as the prototype reads it (R-003)

| Kind | Holds | Read by the prototype |
|---|---|---|
| `BRP` | signals | `Flow_40ms`, `Press_40ms` (lines 48 and 50) |
| `PLD` | signals | `MaskPress_2s`, `Press_2s`, `EprPress_2s`, `Leak_2s`, `RespRate_2s`, `TidVol_2s`, `MinVent_2s`, `Snore_2s`, `FlowLim_2s` (lines 85 to 101) |
| `SAD` | signals | `Pulse_1s`, `SpO2_1s` (lines 125 and 127) |
| `EVE` | events | the annotation text, onset and duration (lines 11 to 19) |
| `CSL` | events | the annotation text, onset and duration (lines 29 to 36) |

Some details of that table:
- **These names are what the prototype looks signals up by.** How each relates to the label bytes in the file is open; see *Open*.
- **The suffixes `40ms`, `2s` and `1s` are part of the names.** The interval itself comes from each header, as above.

## Across the series (R-006)

**These labels come from OSCAR, and PAPvault says so publicly** (Z, 2026-09-19), in `SOURCES.md` and in the user documentation. For the AirSense 10 they are also checked against Z's own card; for the S9 and the 11 series they are not.

A comment in OSCAR's reader says its table of labels combines the S9, AirSense 10 and AirSense 11 variants with those of devices set to other languages (lines 3960 and 3961). For each signal the prototype reads, the table lists these labels:

| The prototype's name | Labels in the table | Line |
|---|---|---|
| `Flow_40ms` (`BRP`) | `Flow`, `Flow.40ms` | 3971 |
| `Press_40ms` (`BRP`) | `Mask Pres`, `Press.40ms` | 3972 |
| `MaskPress_2s` | `Mask Pres`, `MaskPress.2s` | 3977 |
| `Press_2s` | `Therapy Pres`, `Press.2s` | 3979 |
| `EprPress_2s` | `Exp Pres`, `EprPress.2s`, `EPRPress.2s` | 3984 |
| `Leak_2s` | `Leak`, `Leak.2s`, translations: `Leck`, `Fuites`, `Fuite`, `Fuga`, `Lekk`, and four written in non-ASCII characters | 3992 |
| `RespRate_2s` | `RR`, `AF`, `FR`, `RespRate.2s` | 3993 |
| `MinVent_2s` | `MV`, `VM`, `MinVent.2s` | 3994 |
| `TidVol_2s` | `Vt`, `VC`, `TidVol.2s` | 3995 |
| `Snore_2s` | `Snore`, `Snore.2s` | 3997 |
| `FlowLim_2s` | `FFL Index`, `FlowLim.2s` | 3998 |
| `Pulse_1s` | `Pulse`, `Pulse.1s`, translations: `Puls`, `Pouls`, `Pols`, `Nabiz` | 4002 |
| `SpO2_1s` | `SpO2`, `SpO2.1s` | 4003 |

What the table establishes, and what it doesn't:
- **Two forms of label.** Every signal has a short form, sometimes translated, and a form with the interval appended after a dot. The prototype's names have the same words and intervals as the second form, with `_` in place of the dot. That is consistent with `Flow.40ms` being the AirSense 10's label, but not proof. The check will show it: if a synthetic label does not reach the name `prepare_data()` looks for, the check fails.
- **The same label in two files.** `Mask Pres` appears for both `Press_40ms` and `MaskPress_2s`, so only the kind of file tells them apart.
- **Which series writes which form is not stated** in the lines read.
- **Characters outside ASCII.** Four of the leak labels are written in non-ASCII characters, although EDF+ allows only bytes 32 to 126 in a header (R-002, 2.1.3 item 1). One of them appears to be another entry decoded with the wrong character set. Whether a device writes such bytes is not stated. A reader must not assume the header is ASCII.

## Timing, as Z's design sets it (R-003)

- **Signals:** a sample's time is its file's start time plus the sample's offset in the file. (lines 54, 107 and 131)
- **Events:** an event starts at its file's start time plus its onset, and ends its duration later. Empty annotations, the time-keeping ones, are dropped. (lines 12 to 14, and 30 to 32)
- **Recording start and stop:** each `BRP`, `PLD` and `SAD` file gives a recording start at its header's start and a recording stop at its end. (lines 60 to 71, 110 and 111, 134 and 135)
- **Combining signals:** within a file, the prototype joins its signals on their offset. (lines 53, 106 and 130)

## Days

- **The prototype:** it takes each `DATALOG` folder as one day and works out none itself. (R-004, lines 145 and 153)
- **PAPvault:** its days run from 6 in the morning to 6 the next morning, named by the date they begin, and a session belongs whole to the day it began in (Z, in `CLAUDE.md`).
- **The folder does not decide anything.** PAPvault works from the session times in the file names and headers, so whether the machine's folders follow the same rule never matters. A generated card may file a session under either day.

## The generator's choices

No source gives these, and a reader must take them from each file's header, never assume them:
- the physical and digital extremes of each signal;
- the record duration, and the number of samples per record. These are kept consistent with the name suffixes;
- the physical dimension of each signal;
- the transducer and prefiltering fields;
- whether a signal file is plain EDF or `EDF+C`;
- how a file holding only events divides into records, within the rules above;
- the event texts. The generated data need not look realistic, since Z tests realism on a real card;
- what the patient and recording fields hold: a marker string, so that a check can fail if it ever reaches the page.

## Open

1. **The AirSense 10's exact labels.** Half settled, on 2026-09-19. A synthetic card written with the dotted labels was read by the R `edf` package and then by `prepare_data()`, which found every signal it looks for: a label written `Flow.40ms` reaches the name `Flow_40ms`. So the dotted form works end to end with the prototype. Whether a real AirSense 10 card spells its labels that way is a separate question, and only Z's card answers it.
2. **Which series writes which label form, `SA2` and `AEV`,** and what `AEV` holds. Sources: Z, a further limited read, or a real card of that series.
3. **A second source for the labels.** OSCAR is the only source for everything in *Across the series*, and R-016 found no reader of ResMed cards whose knowledge is independent of it. The container is a different matter: EDF is a published standard, and the R `edf` package the checks run with is an independent implementation of it. So the file structure has an independent check and the label spellings do not.

Settled since this file was first written:
- the folder and file names, by R-006;
- which folder a night's sessions go into, which no longer matters: PAPvault works from the session times, so a generated card may file a session under either day.
