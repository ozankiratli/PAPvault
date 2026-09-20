# PAPvault

A single web page for looking at your own PAP therapy data. Your data stays on your computer: the page reads the SD card's folder in your browser, and there is nowhere for it to send anything.

**It is being built.** Today the page opens a folder, reads the night recordings on the card, and draws them: a figure per night for whatever period you pick, and, for a single night, a stack of aligned plots with one cursor line across all of them and zoom shared between them.

## What it promises

- **Nothing leaves the page.** A Content-Security-Policy in the page itself forbids every outbound connection, so the browser enforces it rather than trusting the code.
- **Nothing is collected.** No analytics, no counts, no error reporting.
- **Only the night's recording is read.** Summary files, settings and identification files are never opened.
- **Nothing identifying is touched.** The fields that name a person or a machine are stepped over, never shown and never kept.
- **It displays; it does not conclude.** No scores, no bands, no advice.

## Which machines

ResMed: the S9, and the AirSense and AirCurve 10 and 11. Only the AirSense 10 has been checked against a real card; the rest are read the same way, with field names taken from OSCAR's source and untested on a machine.

Another machine is added when there is a card, or data from one, to test against. Everything already gathered about the other manufacturers is kept in `dev/READING-LOG.md` and `.claude/development-notes/machine-survey.md`.

**PAPvault does not replace [OSCAR](https://www.sleepfiles.com/OSCAR/).** For keeping years of data and analyzing them deeply, install OSCAR: it reads far more machines, and it respects your privacy. PAPvault is the quick look you take when you do not want to install anything.

## Running it

```
python3 build.py      # writes dist/index.html and prints its SHA-256
```

The build uses only the Python standard library. It inlines the stylesheet and the script, renders `docs/manual.md` into the page's manual, and fills in the security policy with the hashes of what it inlined. The result is one file: open `dist/index.html` in a browser, from a server or straight from disk.

## How it is built, and why that is public

PAPvault is written with an AI agent under written rules, and the record of that is part of what this repository publishes:

- **`CLAUDE.md`** -- the rules the agent works under, including that no real device data ever reaches it.
- **`dev/READING-LOG.md`** -- every outside source the project has read, written down before it was opened, cleared by the maintainer, with what was taken and what was not.
- **`SOURCES.md`** -- every source of knowledge, and what came from it.
- **`formats/`** -- how each machine stores its data, each fact citing the read it came from.
- **`.claude/development-notes/`** -- how the project got here, including `other-projects.md`, which records the time the agent read another project's reader and was stopped.
- **`dev/CHECKLIST.md`** and **`dev/VERIFICATION.md`** -- what is checked before a release, and what the maintainer found when checking. There is no automated test suite: every change is tested by hand.

The manual in the page carries a shorter version of the same account, for people who will never open this repository.

## License

Free software under the [GNU General Public License, version 3](https://www.gnu.org/licenses/gpl-3.0.html).

(c) 2026 [Ozan L. Z. Kiratli, PhD](https://ozankiratli.github.io/) | Bioinformatician
