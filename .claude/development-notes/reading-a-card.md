# Reading a card

**Written 2026-09-19, against the tree at `e4fad7e`,** with everything described here uncommitted. This is the first code that opens a file a person hands the page. No plot existed yet.

## What was built

**`src/edf.js`** parses EDF and EDF+: bytes in, structure out, nothing touching the page. It was written from `formats/resmed.md`, which cites the specification for every fact in it, in a session that had never held another project's reader. **`src/card.js`** reads a chosen folder as a card: which files hold a night, what session each belongs to, and which CPAP day that session began in. **`src/app.js`** wires the folder dialog to them and reports what was found.

`build.py` now inlines six things -- two stylesheets and four scripts -- each as its own element with its own hash, so the policy names the library separately from the page's own code, and the scripts go in the order they depend on each other in.

## The decisions inside it

**Only the header is read to find a session.** A waveform file is nearly three megabytes; when a scan is only asking when a recording began, it reads the first 256 bytes to learn how many signals there are, then the header those signals need, and stops. `parseHeader` takes the file's real length separately from the buffer it is given, so every check still runs against the whole file.

**The folder a file sits in decides nothing.** A session is the set of files whose names carry the same date and time, and its start comes from their headers. This is what `CLAUDE.md` asks for, and it is what lets the `five-days` case file a session under the previous day's folder and still land in the right place.

**The end of a session comes from the signal files only.** A signal file's header gives the recording's start and its record count gives its stop, which is `prepare_data()`'s design. An event file declares a record duration of zero, so it says nothing about when the recording ended and is not asked.

**Nothing identifying is decoded.** Bytes 8 to 167 of every header are the patient and recording fields. No offset in `edf.js` falls in that range. The synthetic cards put a marker string in both fields, and the checks below assert that string appears nowhere in what the reader returns.

**A file that does not add up is named, not read past.** Every declared size, count and offset is checked against the file's real length before it is used, and a failure throws with a sentence saying what disagreed with what. The page prints those sentences beside the file's path and reads the rest of the card.

**An interrupted file is refused rather than mis-timed.** In an `EDF+D` file the records are not contiguous, so a sample's offset in the file is not its offset in time. The header exposes that, and a signal file marked `EDF+D` is reported instead of being timed wrongly.

**Labels.** Each plot has a list of labels a file may give its signal. The dotted forms are the ones synthetic cards carry and the checks exercise; the short and translated forms come from OSCAR's table, cited in `formats/resmed.md`, and no card here has carried one. `formats/resmed.md` also names four leak labels written in characters it does not spell out, so those are not in the list: that is a gap, not an omission, and guessing them would be inventing a fact.

## The bug the synthetic data caught

The first version of the parser returned one extra event per file, `Recording starts`, which shifted every other event by one position. Fifty-one of the 665 checks failed on it.

EDF+ puts a time-keeping list first in every data record: its onset is that record's start, and in a file with no ordinary signals a non-empty text in that same list names what begins the record rather than an event at a time. The generator writes exactly that, and `answer.json` rightly does not list it among the night's events. The parser was reading it as one. It now takes no event from the first list of any record, and returns those onsets separately, which is also what an `EDF+D` file would need.

This is the case for deriving a case's answer from how it was built rather than from what the code produced. An expectation read off the reader's own output would have enshrined the extra event.

## What was checked

These are the agent's checks, not Z's verification.

**The parser against the answers.** Every file of both synthetic cards, compared with `answer.json`: header start times, signal units, sampling intervals, sample counts, the first, hundredth and last physical value of every signal, and every event's text, duration and absolute start. 665 checks, no mismatches. It can fail: it is what caught the bug above.

**The card layer against the answers.** Both cards read as the page reads them, then every session loaded: session count, each session's start and end, its CPAP day, which kinds of file it has, every signal with the time of its first and last sample, every event, and the day-by-day grouping. 822 checks, no mismatches.

That check was then shown to be able to fail, by running it against three deliberately broken copies of `card.js`:

| What was broken | What the check said |
|---|---|
| the day's cut moved to 23:00 | 10 mismatches |
| a session's end never extended past its first file | 7 mismatches |
| a sample's time advanced at twice its interval | 89 mismatches |

**Files that do not add up.** The `lies` cases in `dev/synthetic/resmed-cases.md` have no generator yet, so eight malformed files were made in the agent's scratch directory by editing bytes of a synthetic one. Each was refused with a sentence naming what was wrong -- a truncated file, a header length disagreeing with its signal count, a flat physical range, an inverted digital range, a samples-per-record that would need 96 gigabytes, and an annotation list running past its record -- and each in under ten milliseconds, so nothing was allocated without bound. A file with bytes outside ASCII in a label was read, with the bad byte becoming a replacement character, which means the signal is reported as not found rather than guessed at. A file whose event text is markup returned that text as a string, unchanged.

**The page, driven through its own file input.** A probe copy of the built page, carrying all 63 files of the `five-days` card, handed to `#folder-input` and dispatched as a real `change` event. It reported 29 night files of 63, 6 sessions on 5 days, from 2026-03-10 10:30 PM to 2026-03-15 6:30 AM; opened the calendar on March 2026 with the 14th selected; put dots on exactly the 10th through the 14th; and summarized the 14th as one session, 7 hours 30 minutes, 11:00 PM to 6:30 AM. All of that matches `answer.json`. The browser logged no policy violation and no exception, and the status area held no element but paragraphs.

**How long it takes.** 3 milliseconds to read 29 headers; 23 milliseconds to load every signal of every session in that card without the waveform, and 133 with it. The probe page reported 7,302 milliseconds, which is **not** a real cost: under `--virtual-time-budget` the clock advances by each pending timer, and the probe polled every 50 milliseconds while waiting. The whole headless run, browser launch included, takes 1.55 seconds of wall clock.

## What is not checked

- **No real card.** That is Z's, and it is the only thing that can say whether a real AirSense 10 spells its labels the way the synthetic ones do.
- **The alternate labels.** The short and translated forms are in the code and no test data carries them. `other-labels` in `dev/synthetic/resmed-cases.md` is the case that would.
- **The malformed files are not in the repository.** They were made by editing bytes in a scratch directory, so nobody else can re-run that check. Generating the `lies` cases properly would fix it.
- **The checks themselves are not in the repository.** They are two Node scripts in the agent's scratch directory. `CLAUDE.md` says there is no automated suite and that Z tests every change, so whether they belong in `dev/` is Z's call. What they do is compare the reader with `answer.json`, which is the same thing `dev/synthetic/check_resmed.R` does from the R side.
