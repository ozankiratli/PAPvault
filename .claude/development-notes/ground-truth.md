# The R prototype as ground truth

**Written 2026-09-18, against the tree at `a201834`.** The prototype it describes is not in the tree: it sits in `CPAP_old/`, which git ignores. Nothing had yet been built to compare against it.

Z, 2026-09-18: *"For now, let's not touch the data. The scripts I have read the data correctly. We will use that as ground truth."*

## What the ground truth is

The reference is `prepare_data(dayFiles)` in `CPAP_old/data_prep.R`, the one function the Shiny app, `CPAP_old/app.R`, sources and calls. It has two layers, and they are worth keeping apart.

**The decoding is the R `edf` package**, version 1.0.0 ([github.com/bwrc/edf](https://github.com/bwrc/edf), published 2016-04-22, MIT), installed in the user library for R 4.4. `read.edf()` returns a file's global header, its signals by name, each with a time column, and its EDF+ annotations.

**The interpretation is `prepare_data()`.** It picks files by the type code in their names, joins each file's signals on the time column, turns each time offset into a clock time by adding it to the start time in the file's header, drops empty annotations, and adds a "Recording starts" and a "Recording stops" marker for each signal file. It is handed every `edf` file in one `DATALOG/<folder>`, so which night a recording belongs to is decided by the folder the device wrote it into, not by the prototype.

`grep -n 'source(\|prepare_data' CPAP_old/app.R` shows the wiring. `CPAP_old/plotting.R` is not sourced by the app, so the daily summaries in it are not part of the ground truth.

## What it covers

| File type | What `prepare_data()` reads |
|---|---|
| `BRP` | `Flow_40ms`, `Press_40ms` |
| `PLD` | `MaskPress_2s`, `Press_2s`, `EprPress_2s`, `Leak_2s`, `RespRate_2s`, `TidVol_2s`, `MinVent_2s`, `Snore_2s`, `FlowLim_2s` |
| `SAD` | `Pulse_1s`, `SpO2_1s` |
| `EVE` | annotations: text, onset, duration |
| `CSL` | annotations: text, onset, duration |

Signals are picked by name, so a signal in one of those files that is not named above is not read. `grep -o 'signal\$[A-Za-z0-9_]*' CPAP_old/data_prep.R` lists the names.

**Nothing else on a card is covered**: not `STR.edf`, not `SETTINGS/`, not the `Identification` files, not `Journal.dat`. Z, the same day: *"The files I left out are mostly not needed as we can recover all the data from the files I chose."* So the per-session files are the source, and what the device also records elsewhere is recomputed from them rather than read back. Anything PAPvault does read from the other files has no ground truth on this date and needs a different one -- a published specification, an open-source reader, or a synthetic case whose answer is known by construction.

## Other devices

The prototype was written against a ResMed AirSense 10, the only device the project has real data from, and it is ground truth for that device and no other. Z, 2026-09-18: *"We will have to do searches for other machines, and then we will have to have a data standardization step."*

So support for another device starts with research into its format, from published specifications and open-source readers, and every device is then read into one standardized form that the rest of PAPvault works from. For those devices there is no real data to compare against. Their reference is what the research finds, and synthetic data built to match it, generated with Z's help.

## What agreement can show, and what it cannot

The new reader and `edf` are independent decoders, so where they agree that is strong evidence the bytes were decoded right: the header fields, the values, the number of samples, the annotation text and timing.

Agreement cannot show anything both sides decide the same way. **Time is the clearest case.** An EDF header carries a start date and a start time and no time zone, so putting a recording on a clock is an interpretation, whichever reader makes it. If the new reader makes the same choice as `prepare_data()`, the two agree whether or not the choice is right -- across a daylight-saving change, for example.

## Where it runs

Only where the real data is: on Z's machine, run by Z, or by a script Z has approved whose output is a verdict and never a value. Nothing it produces enters the repository.

So a comparison against it is one of Z's own checks, recorded in Z's words like any other. What can be shared, and re-run by anyone, is the synthetic data, where what a case should show is derived from how it was built.

## Added later on 2026-09-18, against `4db9efc`

The per-day summaries brought `STR.edf` back into scope. The device declares its own per-day figures, and on the AirSense 10 they are in that file; the question was whether the summary view shows those, or recomputes them from the session files. Z: *"Let's have both side by side during development, my experience was they matched but we will see. It's been a while, so I might be misremembering."*

So during development `STR.edf` is read, and each figure the device declares is shown next to the same figure recomputed from the session files. The prototype is ground truth for neither side, since `prepare_data()` does not read `STR.edf`. The two sides are independent of each other, though: one is the device's own arithmetic, the other is PAPvault's over what the device recorded. Where they agree, that is evidence for both; where they differ, the difference is the finding.
