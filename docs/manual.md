# About

## What is PAPvault

PAPvault is a browser based, free and open source, privacy friendly sleep data displayer. That allows PAP users to display their data without the need for uploading or even copying the data somewhere other than they control.

- Developed by: [Ozan L. Z. Kiratli, PhD](https://ozankiratli.github.io) | Bioinformatician
- Version: {{version}}
- License: GPL 3
- [Source code](https://github.com/ozankiratli/PAPvault)


## Who PAPvault is for

PAPvault is for anyone who wants to look at their own therapy data without handing it to anyone, and without installing anything. Put the card in, open the folder, see your sleep data. That is the whole idea. 

It is deliberately not comprehensive. It shows what your machine recorded, for the nights you pick, and it stops there. It keeps nothing between visits, it has no account, and it makes no judgment about what the numbers mean.

If you want more, install [OSCAR](https://www.sleepfiles.com/OSCAR/). It reads more machines, keeps years of data, and analyzes them far more deeply than a page like this can. It runs on your own computer and it respects your privacy, which is why this manual points you to it rather than around it. PAPvault is not trying to compete with OSCAR: it is the quick look you take when installing software is not what you want today.

## What it never touches

- **Nothing leaves this page.** There is nowhere to send it: the page's security policy forbids every outbound connection, and the browser enforces that rather than trusting us.
- **Nothing is collected.** No analytics, no counts, no error reports.
- **Only the night's recording is read.** Files that hold something else, such as the machine's summaries, its settings or its identification file, are never opened.
- **Nothing identifying is touched inside the files.** They carry fields naming the person and the machine. PAPvault steps over them, and never shows or keeps them.
- **The one thing you will see is the name of the folder you picked.** After you open one, PAPvault says what it found -- *"SN-23231234567 opened: 15 files"* -- using the folder's own name, so you can tell which folder you actually opened. On many cards that name is the machine's serial number. It is never stored and never sent; it is on your screen and gone when you reload. **Worth knowing if you send someone a screenshot of that dialog**, because the name goes with it.
- **Your browser's own dialog may use the word "upload".** That is the browser's wording for letting a page open a folder, and it is why PAPvault never uses the word itself. Nothing is sent anywhere.
- **The host still sees you.** This page is served by GitHub Pages, through a content delivery network in front of it, and both see the address every visit comes from. GitHub's documentation says a visitor's address is logged and stored for security purposes. No page can prevent that. Download the single file and open it offline if you would rather not be seen at all.

## Machines it reads

ResMed machines: the S9, and the AirSense and AirCurve 10 and 11.

Only the AirSense 10 has been checked against a real card. The others are read the same way, but their field names were taken from OSCAR's source and nobody here has tested them on a machine. If a signal is missing, PAPvault says so rather than guessing.

Another machine can be added once there is data to test with. A report, and a copy of a card, real or made up, is how that starts.

PAPvault does not replace OSCAR, the desktop program for the same data. For keeping years of data and studying them deeply, OSCAR is the better tool. PAPvault is for looking at a night without installing anything.

If you want a different machine added, see **Contributing** under *Development*.

## Where the facts come from

- The **EDF and EDF+ specifications**, published standards, for how the files themselves are laid out.
- My own **R prototype**, which read an AirSense 10 card in 2024, for which files are read and how each sample and event is given its time.
- **OSCAR's source**, for the names ResMed gives its signals and for how files and folders are named.

Every source is listed in `SOURCES.md` in the repository. Every read of one is recorded in `dev/READING-LOG.md`, before it was made, with what was taken from it and what was left alone.

## References

Everything PAPvault knows, it got from somewhere. This is that list, in full, so you can check any of it yourself.

**The file format**

- Kemp, B., Varri, A., Rosa, A. C., Nielsen, K. D., and Gade, J. **A simple format for exchange of digitized polygraphic recordings.** *Electroencephalography and Clinical Neurophysiology*, 82:391-393, 1992. [doi.org/10.1016/0013-4694(92)90009-7](https://doi.org/10.1016/0013-4694%2892%2990009-7). The European Data Format, which ResMed machines write their recordings in. What PAPvault was built from is the specification published at [edfplus.info/specs/edf.html](https://www.edfplus.info/specs/edf.html).
- Kemp, B., and Olivan, J. **European data format "plus" (EDF+), an EDF alike standard format for the exchange of physiological data.** *Clinical Neurophysiology*, 114(9):1755-1761, 2003. [doi.org/10.1016/S1388-2457(03)00123-8](https://doi.org/10.1016/S1388-2457%2803%2900123-8). The extension that adds the annotations PAPvault reads events from, specified at [edfplus.info/specs/edfplus.html](https://www.edfplus.info/specs/edfplus.html).

**What the signals are called**

- **OSCAR, the Open Source CPAP Analysis Reporter.** [gitlab.com/CrimsonNape/OSCAR-code](https://gitlab.com/CrimsonNape/OSCAR-code), GPL-3.0. The names ResMed's machines give their signals, and how the files and folders on a card are named, were taken from its ResMed reader. No code of OSCAR's is in PAPvault. For the AirSense 10 those names are checked against my own card; for the S9 and the 11 series they are not, and OSCAR is their only source.
- **My own R prototype**, written in 2024 against an AirSense 10 card. Which files a night is in, and how each sample and event is given its time.

**The software this page is built from**

- **uPlot**, by Leon Sorokin. [github.com/leeoniya/uPlot](https://github.com/leeoniya/uPlot), version 1.6.32, MIT. The one library in this page, carried whole and unmodified. It draws every plot.
- **edf**, an R package by the BWRC group. [github.com/bwrc/edf](https://github.com/bwrc/edf), MIT. Not part of this page: it is the independent reader the synthetic test data is checked against, so that PAPvault's own decoding is not the only thing vouching for itself.

**Color**

- **Okabe, M., and Ito, K. Color Universal Design (CUD): how to make figures and presentations that are friendly to colorblind people.** [jfly.uni-koeln.de/color](https://jfly.uni-koeln.de/color/). The event colors on this page are their palette, taken as published in its Figure 16.
- Ichihara, Y. G., Okabe, M., Iga, K., Tanaka, Y., Musha, K., and Ito, K. **Color universal design: the selection of four easily distinguishable colors for all color vision types.** *Proc. SPIE 6807, Color Imaging XIII: Processing, Hardcopy, and Applications*, 68070O, 2008. [doi.org/10.1117/12.765420](https://doi.org/10.1117/12.765420). The work behind that palette, and the measurements the choice of colors rests on.
- **ColorBrewer**, by Cynthia Brewer and Mark Harrower, The Pennsylvania State University. [colorbrewer2.org](https://colorbrewer2.org), under an Apache-style license that covers its color schemes as well as its software. The colors of the signal plots are its `Dark2` scheme in the light theme and its `Set2` scheme in the dark one. Its license asks that this be said here, so it is said in its own words:

> This product includes color specifications and designs developed by Cynthia Brewer (http://colorbrewer.org/).

  ColorBrewer's qualitative schemes were also measured for the event colors and not used there: none of them held five categories apart under simulated color blindness.

**Color vision deficiency was simulated using**

- Vienot, F., Brettel, H., and Mollon, J. D. **Digital video colourmaps for checking the legibility of displays by dichromats.** *Color Research and Application*, 24(4):243-252, 1999. [doi.org/10.1002/(SICI)1520-6378(199908)24:4<243::AID-COL5>3.0.CO;2-3](https://doi.org/10.1002/%28SICI%291520-6378%28199908%2924%3A4%3C243%3A%3AAID-COL5%3E3.0.CO%3B2-3). Their method is how the event colors were checked for whether two of them stay apart for a reader with protanopia, deuteranopia or tritanopia. It is a check made while building this page, not something the page itself runs.

# Using PAPvault

## Getting started

PAPvault shows what your PAP machine wrote to its SD card. It runs in your browser, and your data stays on your own computer or SD card.

1. Put the card in your computer, or use a copy of it.
2. Open **Open Folder** in the top bar, then choose the card's folder or drag it onto the box.
3. Pick a day in the calendar. Click a second day for a range.

Nothing is uploaded, because there is nowhere to upload it to. PAPvault opens the folder and reads it here, in your browser.

**The window your browser opens at step 2 is the browser's own, and it will probably say "upload".** Firefox and Chrome both use that word for letting a page open a folder, and they ask you to confirm it; they use the same words whether the page sends the folder somewhere or, as here, reads it where it sits. No page can change what they say. If you would rather not see it, drag the folder onto the box instead -- that skips the browser's window entirely.

**A large folder takes a while**, and a box says so from the moment you press **Read Data** until the reading is done. Part of that wait is your browser's own: after you choose a folder it lists everything in it before PAPvault hears about it at all, and on a card holding years of nights that alone can take a noticeable moment. The box is up across the whole of it, and counts the files off once the reading starts. Nothing is being sent anywhere during any of it -- the time goes on opening and reading the files where they sit. It closes itself when the reading is done, and also if you close your browser's folder window without choosing anything.

PAPvault then tells you what it found: how many sessions are on the card, which nights they fall on, and the first and last recording. The calendar marks every day the card holds a recording for, and opens on the most recent one.

**Previous day** and **Next day**, above the calendar's grid, step between the nights your card holds rather than between calendar dates, so they never land on a night with nothing on it. They go dead at the first and last night on the card, and each step selects that one night on its own, clearing any range you had.

The arrows beside the month name, and the month picker you get by clicking the month name itself, move the calendar without touching what you have selected. So you can go looking for a night in another month, or another year, and what is on screen stays as it was until you pick a day.

Pick one day and you get that night in detail. Pick a range and you get a figure per night across it.

If a file on the card does not add up -- if it claims more data than it holds, or its numbers contradict each other -- PAPvault names that file, says what was wrong with it, and reads the rest. It never reads past the end of a file.

## Days and sessions

A day here runs from 6 in the morning to 6 the next morning, and is named by the date it began. A night that starts on the 18th and ends on the 19th is the 18th.

A session is one unbroken stretch of recording. Each session belongs whole to the day it began in, so a session still running at 6 in the morning stays with the day it started, however late it ends.

**A break of up to an hour does not start a new day.** If you take the mask off and put it back on within the hour, what follows stays on the same day as what came before, even when you put it back on after 6 in the morning. Getting up at ten to six and going back to bed at five past does not split one night across two dates. The break is measured from the moment the recording stopped to the moment the next one started, and it carries on: each session that follows a short break joins the one before it, so a night of interrupted sleep is one day's however many times it was interrupted.

**A session that starts at noon or later always belongs to the day it starts on.** That is the one limit on the rule above, and it is what stops a morning of short breaks from carrying an afternoon nap back onto the night before.

**A session is measured by the flow, and by nothing else.** Your machine does not write a night as one thing: it writes a file for each kind of thing it records, it does not stamp them all at the same second, and it writes files at other times too -- when it is unplugged and plugged back in, when it sends its data somewhere, and for reasons of its own. Counting those would turn one night into three. So PAPvault follows the flow your machine recorded, and a session is one unbroken stretch of it. Where the flow is cut for no more than **five seconds**, it is still the same session.

**Files that carry no flow are not nights.** Unplugging your machine and plugging it back in makes it write a file saying a recording started, with no recording behind it. An event file on its own is not a night, however many times that happens. Such files never make a session, never set a session's start or end, and never move a night from one day to another; they simply join the night nearest to them, and the folder box says how many there were.

**A night can still hold more than one session.** If the flow stopped for longer than five seconds and started again -- the mask came off, or the machine stopped for a reason of its own -- that is a second session. PAPvault does not decide that two separate stretches were really one night's sleep. It shows what the machine recorded and leaves the reading to you.

The cut is in the morning rather than at midnight so that a night is never split in two. It is at 6 rather than at noon so that a daytime nap belongs to the day you took it on, and not to the night before.

Choosing one day shows that day in detail. Choosing a longer period shows summaries.

Every time shown is the time your machine recorded. Machines keep their own clock and store no time zone, so a time is whatever the machine thought it was.

## The plots

**The page is three columns on a wide screen.** The summary is on the left and the calendar on the right, and both stay where they are while the plots in the middle scroll. The bar along the top stays as well, so the folder, the calendar, this manual and the light and dark themes are one click away however far down you have gone. On a narrower screen the three stack, and narrower still the calendar moves into a dialog you open from the top bar.

**The summary card describes whatever period you picked**, one night or a hundred. Pressure gives its highest, lowest, mean, median and 95th percentile; leak gives the same four, and then how long it ran above zero. **The plots below draw the mean and the 95th percentile**, not the median: over a period longer than one night each point is the average of the nights in it, and averaging medians gives a number that is not a statistic of anything. The session box says how many sessions there were, how long the machine ran in total, when the first began and the last ended, and **Events/hr**; over a period it also gives the average per day, across the days that hold a recording. Under them is a bar for each kind of event, showing how many of each, with the most frequent at the top.

Those figures are arithmetic over what your machine recorded, and nothing more. There is no score, no band, no target line and no verdict. Hours come from when each session started and stopped, never from counting rows.

**Events/hr is every event your machine wrote, over the hours it ran.** All of them, whatever they are called: an arousal counts as one, a Cheyne-Stokes period counts as one, an apnea counts as one. PAPvault has no opinion about which kinds matter, so it does not leave any out, and the bar chart below is there to show you what the number is made of.

**It is not your machine's AHI, and the two will not agree.** An apnea-hypopnea index counts apneas and hypopneas and nothing else, over a period your machine decides. This counts everything on the card. If you want the figure your machine reports, read it on your machine: PAPvault shows what was recorded and does not recompute what the device already declares.

**Dur. in the leak box is how long the leak rate was above zero**, in minutes. Your machine writes that rate every couple of seconds, and each reading above zero stands for the one step of recording it covers, so a leak lasting a single reading counts as one step. Over a single night that is the night's own total. Over a longer period the row reads **Dur./day** and gives the average across the nights that hold a recording, counted the same way as the "Across" figure in the session box, so a night with no recording does not drag it down.

PAPvault sets no threshold of its own. It has no view on what counts as a large leak, only on what the machine wrote, so this is time above zero and not time in trouble. A leak is never carried across the gap between two sessions, since nothing was recorded there.

**Leak is shown in liters per minute.** Machines do not agree on which unit to write it in, and a rate per second is a small number that is hard to read against. So where your machine recorded the leak in liters per second, PAPvault multiplies by 60 and labels it per minute; where your machine already wrote liters per minute, the number is untouched. Which one your card holds is read from the file itself, never assumed. This is the one place PAPvault changes a number before showing it to you, and it changes only its scale: sixty times a rate per second is the same rate per minute.

**Respiratory rate is headed "breaths/min", whatever your card calls it.** The file format your machine writes gives a unit only eight characters, so there is no room for "breaths/min" and machines write "bpm" instead -- which everywhere else means beats per minute, a heart rate. It is not one. PAPvault spells it out. Nothing but the wording changes: the numbers are your machine's own.

**The plots card in the middle shows one night or many.** Pick one night and it shows that night in detail. Pick a range and it shows a chart per figure instead, with a point or a bar for every night: hours used, how many sessions, events per hour, and the same pressure and leak figures.

**Over a period you can average by day, week, month or year.** The box above the charts says which, and it starts on whatever suits the length of what you picked -- daily for a few months, weekly for a year or two, and so on. **It is only a starting point.** Every choice stays available at every length, because how to look at your own data is your decision and not this page's.

**What an averaged point is.** Each point is the mean of the nights inside that week, month or year. The nightly figures are themselves means, so it is a mean of means throughout. **Nights with no recording are not counted**: a week you used the machine on four nights is the average of those four, not four sevenths of a week. That matches the **Dur./day** figure, which has always been the average across the nights that hold a recording. The chart is headed **Hours Used/day** to say so, and pointing at a bar reads **Hours/day** where a point covers several nights and **Hours** where it is one.

**Sessions are counted, not averaged.** They are the one figure a group adds up rather than means: a week's bar is how many times the machine ran that week, so the bars still add up to the number in the session box however you group them. Every other chart averages.

**The Events per Hour plot can be narrowed to the events you care about.** With a period on screen, **Choose Plots** also lists every event name your card holds; unchecking one takes its line off that plot and changes nothing else. Those boxes are your card's own names, so they start over, all on, each time you open a folder.

**A night with none of an event counts zero, not nothing.** If your machine named a kind of event on any night in the period you picked, every other night in that period shows zero of it rather than a gap. A gap would read as "not known"; zero is what was recorded.

**A single night is drawn as a stack of plots on one time axis**: flow, pressure, leak rate, respiratory rate, flow limitation, snore, tidal volume and minute ventilation. **Choose Plots**, at the top of the card, opens the list to check and uncheck; the page remembers what you chose. A period has its own list there, since its plots are different ones, and its own choice is remembered separately. Turning one on or off redraws the stack from what is already in hand, so it does not read your card again -- unless you turn on a plot whose signal has not been read yet, which is the one case where a file is opened.

**Oximetry is turned off in this version, and no oximetry file is opened.** ResMed records it only on the AirSense 10, and an oximeter it will work with is hard to come by, so there has been no card to test the reading against. Rather than show a figure nobody has checked, PAPvault leaves it alone until there is one. Nothing about it decides anything else either: how long a night lasted is measured from the flow and the pressure, never from an oximeter.

**The plots line up and move together.** Moving the pointer over any one of them draws a line at that moment across all of them, so you can see what every other signal was doing at the same instant. Drag sideways across a plot to zoom into it; every plot zooms with it. You can also hold Ctrl and use the wheel, or pinch on a trackpad. Scrolling up and down on its own moves the page, as it does everywhere else. Double-click to go back to the whole night.

**Once you are zoomed in, hold Ctrl and drag to slide the window along** -- Command instead of Ctrl on a Mac, where Ctrl and a click is a right click. The plots move with your pointer, the way a map does, and they keep the width you zoomed to. Slide to either end of the night and they stop there rather than running off it. This works on the summary plots too, when you have a period selected rather than a single night.

**On a trackpad you can also swipe sideways with two fingers to slide it**, with nothing held down. Swiping up and down still scrolls the page, and so does swiping sideways when the whole night is already on screen, since there is nowhere to slide to. Which of the two a swipe is doing is decided the moment it starts and does not change part way through, so a swipe that begins as a scroll stays one to the end.

**Events keep the words your machine wrote.** The strip at the top of the stack gives each event name its own row and its own color, and the same color marks that event across every plot below, as a line at the time your machine recorded, with its duration shaded to the left of that line. **Your machine writes an event down when the event is over**, not when it starts -- it cannot know an apnea lasted twelve seconds until twelve seconds have gone by -- so the shading covers the twelve seconds **before** the time in the file, which is when the thing itself happened. The **Legend** button in the bottom right corner lists every name with its color and how many there were, and stays within reach however far down the plots you have scrolled.

**On a ResMed card those words are** `Arousal`, `Apnea`, `Central Apnea`, `Hypopnea`, `Obstructive Apnea`, `CSR Start` and `CSR End`. They come from the card, not from PAPvault, so a machine that writes something else shows something else and is read exactly the same way. Nothing here is a list PAPvault checks against.

**Five of them are drawn short, because a row label has little room.** Where a name would crowd out the bars beside it, PAPvault draws a short form and keeps the words for the **Legend**, where hovering a row shows what it stands for:

| Drawn | Stands for |
|---|---|
| `Ar` | Arousal |
| `OA` | Obstructive Apnea |
| `CA` | Central Apnea |
| `HA` | Hypopnea |
| `A` | Apnea (Other) |
| `CSR` | Cheyne-Stokes |

A name PAPvault has no short form for -- anything else your machine writes, in any language -- is drawn in full, exactly as it came off the card. And the short form is only ever what is *drawn*: events are counted, colored and grouped by the word your machine wrote.

**What any of them means is your machine's business, not this page's.** PAPvault does not define an apnea or a hypopnea, holds no rule of its own about what counts as one, and never checks whether your machine was right to call one. Every event you see is what the machine reported, in the machine's own words, at the time the machine put on it. What your device counted, and why, is in your device's documentation and with the people who prescribed it.

**`CSR Start` and `CSR End` are drawn as one event, lasting from the first to the second.** Your machine writes a mark where a stretch of Cheyne-Stokes respiration begins and another where it ends, and what it is reporting is the time between them rather than two separate moments. So PAPvault shows one event spanning that time, named `CSR`, and a night with four such stretches counts four -- not eight, and not two rows of four. Nothing is lost: both marks are still in your file, and the period drawn begins and ends exactly where they do.

Where one of the pair is missing -- a stretch still running when the recording stopped, or an end with no beginning before it -- the mark is left alone and shown as your machine wrote it. PAPvault will not guess where a period began or ended.

PAPvault never renames an event, never merges two names into one kind, and never decides that one matters more than another. **The colors are labels and nothing else.** Nothing is meant by one name getting one color and another a different one, and a color says nothing about whether an event matters.

**Every name on your card gets its color when the card is opened, and keeps it.** Not per night and not per period: the moment you open a folder, PAPvault reads through it, collects every event name anywhere on it, and gives each one a color. So a name is the same color on every night, in both themes, and whatever range you pick.

**The rows are in the same order every time, too.** The strip above the plots lists them in a fixed order, so a row is in the same place tonight as it was last night and two nights can be read against each other. The five names below come first, in this order, and anything else your machine writes follows them:

| Row | Color |
|---|---|
| `CSR` | reddish purple |
| `OA` | bluish green |
| `HA` | orange |
| `CA` | blue |
| `A` | vermilion |
| `Ar` | sky blue |

**A name you have none of tonight still gets its row, and its row is empty.** That is the point of fixing the order: an event that happens on one night in fifty is not something you should have to notice the absence of. A name that appears nowhere on your card gets no row at all, so a machine that never writes `CSR` never grows a `CSR` row.

**In the summary card the bars run longest first instead**, since there the question is which happened most. A name with none in the period you picked still gets its bar, showing zero.

**The event colors are chosen to work if you are color blind.** They are Okabe and Ito's Color Universal Design set, drawn up so that people with the common kinds of color blindness can still tell them apart. The set was made for one background and this page has two, so neither theme uses the set's black; the remaining seven are used in both, which is why an event is the same color whichever theme you are in. Beyond seven names on one card the colors start again from the first.

Even so, **color is not how an event is identified here.** The strip names every row in the machine's own words, and the Legend lists every name against its color. If two colors look alike to you, the names are what to read.

Two annotations are left out: the ones a machine writes to mark where a recording begins and ends. PAPvault already knows both, from the recording's own file, and showing them again would put a session's edges among the things it observed.

Pick more than one day and the detailed plots are not drawn. Reading a night's flow signal means opening the largest file on the card, and there is no useful way to show a month of it at once; the summary above is what a longer period shows.


# Development

## History

> I want a reviewer to look at this and say that yes, AI agents can be used responsibly when what you are building is about someone's health.

I wrote the first version of this in early 2024, in R, by putting my own SD card in a reader and looking at what was on it. That work is where the understanding of these files comes from: which files a night is in, what the signals are called, how a sample gets its time. It ran as a small application on my own machine, and then I left it alone.

In September 2026 I picked it up again as a web page, so that it needs nothing installed. That is where an AI agent came in, and it came in after the format was understood rather than before. The design decisions, and every test against real data, are mine.

This page is built on three things: the published EDF standard, my own 2024 code, and OSCAR's source for the names ResMed gives its signals.

## The rules

The agent works under written rules, kept in `CLAUDE.md` in the repository. They are public for the same reason this page is.

- **No real data reaches the agent.** Reading a file into its context would send that file to a company's servers. A tool whose whole promise is that your data stays with you cannot be built by sending mine elsewhere, so everything the agent works against is generated.
- **Knowledge, never code.** Nothing from another project is copied or translated into this one. What may be taken is where the night's data sits and what it holds, never how another program reads it.
- **Every outside read is named, recorded, cleared and done,** in that order. The agent writes down what it wants to open and what it is looking for, I clear it, and only then does it read. That record is `dev/READING-LOG.md`, and each entry was written before the read, not after.
- **The agent never commits and never publishes.** I review the work as it lands, commit what I have read, and push it myself.
- **There is no automated test suite.** I test every change myself, on real data, on my own machine. `dev/CHECKLIST.md` says what is checked and what counts as a failure, and `dev/VERIFICATION.md` is what I found when I checked.
- **The page displays; it does not conclude.** No scores, no bands, no advice.

## When it went wrong

Twice so far, and both are written down in the repository.

**The one that mattered.** To build test data the agent needed details the standard does not fix, such as what ResMed calls each signal. It went to OSCAR's source and read the reader itself. I had already warned about leaning on OSCAR, and I stopped it. The problem was not only that another project's code was open: OSCAR was quietly becoming the authority on how my tool should behave. We rewrote the rule that day, and the agent's own account of why it happened is in `.claude/development-notes/other-projects.md`.

**The smaller one.** While surveying which machines exist, agents reported a sampling interval as though it were a rate. Checking their claims against the source caught it; a number wrong by a factor of forty would otherwise have gone into the notes. Since then an agent's report is treated as a draft, never as a finding.

Both are published because a record that shows only the parts that went well is evidence of nothing.

## What carries elsewhere

This is a small project, but the arrangement is not specific to it.

- **Write the read down before making it.** Written afterwards it is a summary. Written first, it is a decision, and anyone can check it was kept.
- **Keep reading and writing apart.** Code is written from notes, in a session that never had the other project's code in front of it.
- **Cite a fact to a commit,** not to a project. Projects move; a commit does not.
- **One source cannot be both a fact and the check on it.** Where a single project is all there is, this manual says so, and that machine is not claimed as supported.
- **With health data, ask what you can avoid reading.** Not being nosy turned out to be a design rule rather than a slogan: it decides which files are opened at all, and which fields are stepped over.
- **Responsibility does not move.** An agent wrote much of this code and much of this text. I read it, corrected it and published it, so it is mine.

## Checking it yourself

- The page is one file. Read its source in your browser.
- Rebuild it from the repository with `python3 build.py`, and compare the checksum it prints with the published one.
- `dev/CHECKLIST.md` is what gets checked before a release. `dev/VERIFICATION.md` is what I found when checking.
- Open your browser's network panel and use the page. Nothing should appear in it.

## Contributing

If you want a new feature, or another machine supported, open an issue at [github.com/ozankiratli/PAPvault/issues](https://github.com/ozankiratli/PAPvault/issues) and help me understand how that machine structures its data.

**Made-up data is enough to work from.** I do not need anyone's real recordings, and I would rather not have them. A description of the files, or a card's worth of invented data, is what lets me write a reader. What I do need before claiming a machine is supported is something I can test against, so a machine joins the list when I can check it rather than when I can guess at it.

If you would rather contribute a pull request, please make sure it follows the development rules in [CLAUDE.md](https://github.com/ozankiratli/PAPvault/blob/main/CLAUDE.md) -- in particular that no real device data goes anywhere near the repository, and that anything taken from another project is recorded in [dev/READING-LOG.md](https://github.com/ozankiratli/PAPvault/blob/main/dev/READING-LOG.md) before it is read. 
