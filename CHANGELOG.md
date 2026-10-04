# Changelog

All notable changes to PAPvault will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

**How to read the version.** What a version number promises here is about what you see and what is read: what the page displays and what each figure means, which files on a card are opened and which are never touched, and the fact that nothing leaves your computer.

- The third number (x.x.**c**): something fixed that was wrong or awkward, something new that changes no figure, or something rearranged.
- The second number (x.**b**.x): a figure now means something different, or the page reads a card differently. Read why before trusting a comparison with what you saw in the last version.
- The first number (**a**.x.x): full revamp of analysis, UI, or both.
- **Between 0.0.1 and 1.0.0**, the numbers are also about stability and baseline features. Each step of the second number says a milestone in both has been reached. 

A version moves when something changes, never on a schedule.

---

## [0.1.0] - 2026-10-04

**PAPvault is achieving stability.** This version provides stable use for RESMED machines and establishes the baseline for basic features. 

### Added

- **How long an event lasted.** Point at a mark in the events strip of a single night, and it shows what the device called it and how long it ran: `OA, 6s`, `CSR, 10m`. A mark the device gave no duration of its own says its name alone.
- **The manual links.** Where one section mentions another, following the link opens it.

### Changed

- **The manual on a phone is full screen rather than a panel.** It fills the screen, its list of sections sits behind a **Contents** button and opens over the text, and the page you came from shows faintly through so it is clear you have not left it. It also keeps one size instead of growing and shrinking with whichever section is open.
- **Previous day and Next day moved above the month**, where they are reached first.

### Behind it

- **The release schedule is stremlined.** The manual verification list is reorganized, steps that can be automated are automated. 

### Known limits

Unchanged from 0.0.2. Only the AirSense 10 has been checked against a real card. Oximetry is off, because ResMed records it only with an oximeter of its own module and no compatible one was found to test against. On Firefox, a phone waits before it can start, and the manual says what to do about it. And no check in this repository has ever seen a real card: the suite runs the reader against synthetic cards whose answers are known by construction, and both were written here.

### Commits

- (1644e11) event times are displayed on the plots
- (cfacb45) previous and next day buttons moved above month year
- (a17c469) release cycle is reworked, and streamlined
- (1438c98) Manual render fixes
- (a7615cd) Manual styling
- (80c5ab3) Releasing improvements

---

## [0.0.2] - 2026-09-27

**Mostly about getting your data on screen, and keeping it there.** A night is drawn from a reduction of itself rather than a point per sample, so the plots answer to a wheel and to fingers; a card is opened many files at a time instead of one after another, which is the difference between minutes and moments on a phone; and the calendar stops turning every second click into a range. One thing changed about how a night is divided, and it is first below.

### Changed -- worth reading before comparing with what you saw last week

- **A short break no longer moves the rest of the night into the next day.** A session that begins within an hour of the end of the one before it takes that session's day, however far past 6 in the morning it begins, and that carries on down a chain of short breaks. A session beginning at noon or later always takes the day the 6 o'clock boundary gives it. So a few minutes out of the mask before 6 no longer files the rest of the night under tomorrow.
- **A period is averaged, and you choose over what.** Day, week, month or year, with each point the mean of the nights in it. A night with no recording is left out of its group rather than counted as zero, and the sessions bar counts sessions rather than averaging them.
- **Recordings are recognized by their names, not by the folder they sit in.** The whole card works, and so does one night's folder inside `DATALOG`, or a folder you copied a few days into.

### Added

- **The plots answer to a phone.** Pinch to zoom anywhere on a plot, drag with one finger to slide the window with the reading line following it, tap to place that line, tap twice for the whole night. Dragging up and down still scrolls the page.
- **And to a trackpad and a wheel.** A two-finger swipe slides a zoomed window, a pinch or Ctrl and the wheel zooms about the pointer, Ctrl and a drag slides, and a double-click goes back to the whole night.
- **A calendar that reads one night at a time.** Every click shows that night. A range is asked for with **Choose Range**, which stays on until you press it again, and what is selected is written along the top of the page. **Previous day** and **Next day** step between the nights your card holds, and the month name opens a month picker.
- **Choose which plots you see**, and which event names the per-hour plot draws.
- **A layout for every width.** Three columns become two, the calendar moves into a dialog the top bar opens, the cards stack, and on a phone the bar's buttons gather into a menu.
- **A faster way in, where the browser offers one.** Chromium browsers can hand a page a listing of a folder; PAPvault then reads the names first and opens only the recordings, so nothing else on the card is ever turned into a file. The manual's new section says what each browser does and why.
- **A sample night that looks like therapy**, for trying the page without a card of your own.

### Fixed

- **An event was marked one duration late.** The stamp a machine writes on an apnea is the moment it ended, and PAPvault drew the shading forward from that stamp instead of back to where the event began. It now reaches back its own duration, so an event sits where it happened.
- **Long nights and long periods are usable.** No more points are drawn than the plot has pixels to draw them in, and zooming still reaches every sample behind them.
- **The first and last bar of a weekly, monthly or yearly chart** are drawn the width of the others rather than cut down the middle.
- **A leak of zero is no longer counted as leaking**, so the time above zero is the time the machine recorded a leak.
- **The event rows keep the card's own order on every night of it**, rather than following whichever names that night happens to hold.
- **Opening a card is much faster**, above all on a phone: each file is opened once instead of twice, and headers and event files are read many at a time.

### Known limits

- **Only the AirSense 10 has been checked against a real card.** Unchanged from 0.0.1: the S9 and the 11 series are read the same way, and their signal names come from OSCAR.
- **On Firefox, a phone waits before it can start.** Firefox has to prepare a file for everything on the card before the page hears anything, and that grows with how many files the card holds -- minutes, for years of nights. The manual says what to do about it: open one night's folder, or copy the days you want into a folder of their own.
- **Oximetry is still turned off**, and no oximetry file is opened.
- **No check here has ever seen a real card.** The suite runs the reader against synthetic cards whose answers are known by construction, and both were written in this repository. Every release is also gone through by hand against `dev/CHECKLIST.md`, on a real card, and what was checked is in `dev/VERIFICATION.md`.

### Commits

- (b019f69) Workflow automatically publishes now
- (b787957) Update RELEASING
- (4eff79a) Audit completed
- (c5ccbb0) Test suite updates
- (8256881) UI improvements
- (a1d61ab) UI improvements
- (0957202) somewhat realistic night synthetic data added
- (5821364) UI Improvements, session-day rule has changed
- (6533a0c) ctrl+click+drag added
- (d9d9bfd) UI improvements, weekly, monthly, yearly views
- (62210f9) UI improvement, more responsive UI by decreasing the number of points drawn
- (4a0273a) UI improvements, weekly plots x axis
- (65fe575) Increased plot responsiveness by decreasing the amount of points drawn on the screen at a time
- (bf48999) logo work, UI improvements
- (7e8ad1d) Calendar selection protocol is reworked
- (7d9bae3) Mobile interface
- (64faab5) Mobile improvements, file reading sequence
- (1ce56b7) touch controls are added

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
- **No check here has ever seen a real card.** The checks in `dev/tests/` run the reader against synthetic cards whose answers are known by construction, and both the reader and the generator were written in this repository. Every release is also gone through by hand against `dev/CHECKLIST.md`, on a real card, and what was checked is written into `dev/VERIFICATION.md`.

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
- (a3bcda8) Workflows added, versioning prep
- (c8f1786) tests added
- (f9c5679) minor bug fixes about builds

---

[0.1.0]: https://github.com/ozankiratli/PAPvault/releases/tag/v0.1.0
[0.0.2]: https://github.com/ozankiratli/PAPvault/releases/tag/v0.0.2
[0.0.1]: https://github.com/ozankiratli/PAPvault/releases/tag/v0.0.1
