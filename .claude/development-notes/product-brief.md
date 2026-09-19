# The product brief

**Written 2026-09-18, against the tree at `4db9efc`.** Nothing had been built. This is the brief as Z first gave it, and what was settled about it later the same day.

Z, 2026-09-18: *"This is going to be a single page view modern design website with dark mode. It will be built as github pages. Top right corner should have a calendar to pick the date or date range to select. Same goes for time range select. Time range selection should be allowed only for a day. When a range is selected it will display summary data. We will not make any conclusions beyond what the PAP machine declares. Again it is a matter of principle. It will just display the data."*

## What it fixes

- One page, in a modern design, with a dark mode.
- Served from GitHub Pages: static files, and no server of PAPvault's own. Whatever a visitor sees is computed in their browser, which is also what the promise in `CLAUDE.md` requires.
- A calendar in the top right corner selects a single date or a range of dates.
- A time range can be selected too, but only within a single day.
- A range of dates shows summary data.
- It displays and does not conclude. The rule is in `CLAUDE.md`, under *It displays; it does not conclude*.

## What a day is

Z: *"A CPAP day is from 12pm to next 12pm. 06/18/21 means from 12:00pm 06/18/21 to 11:59am 06/19/21."*

So a day in PAPvault is the device's day, noon to noon, under the date on which it starts. A night falls inside one day, and a time range selected within a day can cross midnight: 21:00 to 08:00 on the day dated the 18th is one selection.

## Summaries

A summary figure the device declares itself is shown next to the same figure recomputed from the session files, for as long as development lasts. Z: *"Let's have both side by side during development, my experience was they matched but we will see."* Why that is a useful check, and which file the declared figures come from, is in `ground-truth.md`.

## The stack

Z: *"The stack is HTML, CSS, and JavaScript. However, we should be careful with JS. It should be completely open source. We also need to work on the security. I mean JS injection attacks would be terrible. We might also offer the users a static page that they can use on their machines offline. I like the taxtriage html where you can display results. Needs a build, but it's not too hard."*

The TaxTriage report ([github.com/jhuapl-bio/taxtriage](https://github.com/jhuapl-bio/taxtriage)) is a single self-contained HTML file that opens offline in a browser, with its interactivity computed in the page. That is the shape the offline page would take.

## What GitHub Pages brings with it

GitHub's documentation, read on 2026-09-18 (*About GitHub Pages*, under "Data collection"): *"When a GitHub Pages site is visited, the visitor's IP address is logged and stored for security purposes, regardless of whether the visitor has signed into GitHub or not."*

So PAPvault's own code can collect nothing and the host still records that a visit happened. The page cannot change that. What it can do is describe itself accurately: PAPvault collects nothing itself, and its host logs visits.

Z asked whether another host would be better. The agent's answer was that every host sees the request for the page, so changing hosts changes whose logs and not whether there are logs. GitHub Pages also serves the repository as it is, so every deployed version traces to a public commit. Its real cost is that it cannot set response headers, which `security.md` deals with. Z: *"That's why I thought GitHub pages was the right call. It stays."*

## Added 2026-09-19, against `690129c`

Z, after seeing the empty page: *"Let's build it first and then we will decide how to deploy. For the light mode, dark mode let's switch to glyphs, or glyph + "Light/Dark". For the UI. I'm thinking of a card design. Top card is the summary stats, for the period people choose (a day or multiple days as long as people want). On the right side of that card a monthly calendar view. User chooses what they want to display there. Below that the plots etc. As I was building them but all aligned together and hovering in the x-axis shows a tracking line on all plots so the user can see what was happening in other plots too. The time can be subsettable using plotly's select feature, but we should limit it to x-axis otherwise it becomes kind of stupid. lol."*

That changed the brief in three places:

- **The calendar moved into the page.** It sits on the right of the top card, which shows the summary for whatever period is chosen, one day or any number of them.
- **The time range is selected on the plots**, by dragging along the x-axis only, not with a picker of its own.
- **The plots are aligned on one time axis**, and hovering shows a tracking line across all of them at once.

The deploy is decided after the page is built. And before the format notes, Z asked for a survey of the other machines: *"how about we try to find the different formats and how the data is collected in different machines before we move on to format notes."*

Later the same day, after seeing the cards: *"In the top bar let's add 2 buttons that will open modals. 1) Select Folder, 2) Manual (we'll deal with the manual later). In the narrow view (under 650 px), let's move the calendar to the top available through a button and a modal box. Let's make the calendar more responsive, clicking Month opens a modal with year at the top and months that can be selected instead. Default the day to the browser's day. We need to define a CPAPday separately from calendar day."*

- **The top bar opens dialogs**: Select Folder, and a Manual whose content comes later.
- **Below 650 pixels the calendar leaves the card** and opens from a button in the top bar.
- **The month name opens a month picker**, with the year at its top.
- **A CPAP day is its own thing**, not a calendar day: 12:00 on its date to 12:00 the next day, as defined above under *What a day is*. The page opens on the CPAP day that contains the moment it is opened, so before noon that is the day named by yesterday's date.

Then, on the calendar's hint: *""Each day runs from 12:00 to 12:00 the next day." (is unclear also we'll use American prose, we can build this project's version of americanize.py under folder dev/ if needed) We should let the user choose 12h/24h. We might want to add a settings button with just the glyph, to open a modal, so we can give the user the choice to display everything in the way they want, we can slowly develop settings. I think let's change all the buttons to only glyphs and the text shows up only on hover."*

- **Interface text is American prose**: "noon to noon", not "12:00 to 12:00".
- **Time is shown in 12-hour or 24-hour form**, the reader's choice, from a Settings dialog that is to grow one choice at a time.
- **Buttons are glyphs**, and their names appear on hover.

And on the charting library: *"We should settle the library with data. Build scratch page but 2 plots each and with a line on x-axis to track the mouse so the user can follow multiple plots at the same time."* What the comparison found is in `page-layout.md`.

## Added later on 2026-09-19, against `f7dd53f`

After the survey of other machines, Z set PAPvault's place beside OSCAR: *"We should not take OSCAR's work. We won't support DreamStation 2 yet. We can work on it if I get my hands on the machine at some point. The same goes for Transcend. [...] Again. The aim is not to replace OSCAR. We can even direct people to use it for long term storage. This is to skip that requirement."*

- **PAPvault is for looking at data without installing anything.** OSCAR remains the tool for keeping it long term, and PAPvault may say so.
- **The Philips DreamStation 2 and the Transcend machines are not supported** until Z can test on one. The DreamStation 2 encrypts its card, and what is public about reading it is OSCAR's own work; nothing public describes the Transcend's card at all.
- **What PAPvault takes from other projects** is knowledge and never code; the rule is in `CLAUDE.md`, and every source is listed in `SOURCES.md`.

Z also asked whether OSCAR sends anything anywhere. The agent read OSCAR's source at commit `64c5e90a` (2026-07-13) of `gitlab.com/CrimsonNape/OSCAR-code`. The only network code in it is an update check in `oscar/checkupdates.cpp`: a plain-HTTP request for the fixed address `http://apneaboard.net/OSCAR/versions.xml` (line 69), with nothing attached. It is on by default and runs at most every 14 days (`oscar/SleepLib/appsettings.cpp`, lines 68 and 69); a test build forces it on and caps the interval at 7 days (`oscar/main.cpp`, lines 687 to 692); it can be switched off in the preferences, and removed from a build with `NO_CHECKUPDATES`, which `oscar/oscar.pro` leaves commented out at line 46. Like any request it tells the server an address and that someone is running OSCAR, but it carries no therapy data. Z: *"OK that's what I thought so it is safe to refer people to OSCAR for a better system."*

The survey had turned up a ResMed support article on myAir and patients who sleep through noon, as a possible official source for the CPAP day. Z ruled it out, and myAir with it: *"SD card stores the data. That's the source we rely on, not ResMed's buggy systems. MyAir related issues are no concern to our purposes."* The CPAP day rests on Z's definition and on the card, whose `DATALOG` folders are named by the date each night began.

## Added later on 2026-09-19, against `cece505`

Z made the CPAP day final for every machine: *"The day decision is final, not just for ResMed. We will treat the days as from noon to noon."* Whatever a machine does itself, PAPvault's days run from noon to noon, named by the date they begin. Z gave the ruling after stopping the agent reading OSCAR's reader. That account is in `other-projects.md`.

Later that day Z ruled that PAPvault reads only night data:

> I don't know why STR.edf matters. It is not night data. We should not be reading anything that is not data from the night. Same goes for journal.dat. We're building something that is supposed to be "not nosy".

Then:

> PAPvault should never touch anything identifying.

And, while the agent was recording those two:

> This is where we're trying to diverge from OSCAR

Z then set how a card is read and what is shown, in `CLAUDE.md` under *How a card is read, and what is shown*. The agent had raised one question for it: a session that crosses noon could be cut at noon, or given whole to the day it began in. The agent recommended cutting; Z chose the other: *"Give the whole session to the day it began in, which keeps a session whole but lets a day's summary include time outside it." OK This is definitely a better way to do it.* It also settles the open question of which folder the machine files a session under, because the pipeline works from the times in the files and never from the folder.

This reverses the side-by-side decision recorded under *Summaries* above. The device's own daily figures were to come from `STR.edf`, and that file is no longer read. So summaries are computed from night data alone, and nothing sits beside them. The rule is in `CLAUDE.md` under *It reads the night, and nothing that identifies*.
