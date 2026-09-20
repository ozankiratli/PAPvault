# Changelog

All notable changes to PAPvault will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

**What a version number promises here is about what you see and what is read.** The public surface is what the page displays and what each figure means, which files on a card are opened and which are never touched, and the fact that nothing leaves your computer. A third number is something fixed that was merely wrong or awkward. A second means a figure now means something different, or the page reads a card differently, and it is worth reading why before trusting a comparison with what you saw last week. A first means it is a different tool. A version moves when something changes, never on a schedule.

---

## [0.0.1] - 2026-09-20

**The first version that runs.** It reads a ResMed card in the browser, shows one night in detail or a period in summary, and sends nothing anywhere. Treat every figure as untested against anything but one AirSense 10 card and two synthetic ones.

### Added

- **Reads a ResMed card in the browser.** Pick the card's folder; PAPvault opens only the night files under `DATALOG` and never the machine's settings, summaries or identification.
- **A night in detail.** Flow, pressure, leak rate, respiratory rate, flow limitation, snore, tidal volume and minute ventilation, on one time axis, with the cursor and the zoom shared across every plot and the device's own events marked on all of them.
- **A period in summary.** Hours used, sessions, events per hour, and the pressure and leak figures, one point or bar per night.
- **A session is a stretch of flow.** Two stretches are one session when the flow is cut for no more than five seconds. Files a machine writes when it is not recording a night carry no flow, and are never counted as nights.
- **Days run from 6 in the morning to 6 the next morning**, and a session belongs whole to the day it began in.
- **Event names are the machine's own words**, never renamed, never grouped, and colored with Okabe and Ito's Color Universal Design palette so that the colors stay apart for the common kinds of color blindness.
- **A manual in the page**, which says what every figure means and what is never read.

### Known limits

- **Only the AirSense 10 has been checked against a real card.** The S9 and the 11 series are read the same way, but their signal names come from OSCAR and nobody here has tested them.
- **Oximetry is turned off.** ResMed records it only on the AirSense 10 and a compatible oximeter is hard to find, so there is no card to test it against and no oximetry file is opened.
- **There is no automated test suite.** Every release is checked by hand against `dev/CHECKLIST.md`, and what was checked is written into `dev/VERIFICATION.md`.

### Commits

- (a201834) Initial commit
- (4db9efc) Rules to use AI agent are established
- (8019e52) Security rules added
- (5f75ba2) Checklist and verification
- (690129c) Empty page built
- (f7dd53f) Initial design done
- (cece505) development work is done, survey completed
- (7df5971) Initial format research for ResMed machines completed
- (7be94b8) Document picker, manual, readme
- (e4fad7e) synthetic data generation
- (6309c32) v0.0.1 work is complete

---

[0.0.1]: https://github.com/ozankiratli/PAPvault/releases/tag/v0.0.1
