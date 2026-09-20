# Checklist

**Z runs this list before each release.** Each entry says what to check, how, and what a failure looks like; a check with no stated failure is not a check. The agent proposes an entry with the change that adds the behavior it protects, and the entry joins the list when Z commits it. What a run of the list found is written in `VERIFICATION.md`, in Z's words.

Entries are named, not numbered, so a record can point at one and keep pointing at it.

## `headers` -- what GitHub Pages sends

**Protects:** the design assumption that the page arrives with no security header of its own, so the `<meta>` policy is the one in force.

**How:** `curl -sSI <PAPvault URL>`, and compare with the headers recorded at the previous run.

**Failure:** `content-type` is anything but `text/html; charset=utf-8`. A header that was not there at the previous run is recorded and raised, whether or not it looks harmful.

## `policy-blocks` -- the policy is in force

**Protects:** the promise that nothing leaves the page.

**How:** open the deployed page, and in the browser console run `fetch('https://example.com')`.

**Failure:** the request goes out, or fails for any reason other than a Content-Security-Policy violation reported in the console.

## `no-outbound` -- nothing leaves the page

**Protects:** the promise that nothing leaves the page, and that the site collects nothing.

**How:** open the deployed page in a fresh private window with the developer tools' network panel open, reload, and use every control on the page.

**Failure:** any request other than the page itself, apart from a link the tester follows on purpose.

## `framed` -- the page refuses to run inside a frame

**Protects:** the one gap a `<meta>` policy leaves, since it cannot forbid framing.

**How:** save `<iframe src="<PAPvault URL>" width="900" height="300"></iframe>` as a local HTML file and open it.

**Failure:** anything of PAPvault's interface appears in the frame, rather than the notice that it does not run inside one.

## `no-markup` -- nothing from a file becomes markup or code

**Protects:** the rule that text read from a file reaches the page only as text.

**How:** `grep -rnE 'innerHTML|outerHTML|insertAdjacentHTML|document\.write|\beval\(|new Function' src lib`

**Failure:** any line printed. The grep covers every directory the build inlines into the page, so a new one added to `build.py` is added here too.

## `vendored` -- the library in the page is the published one

**Protects:** the claim that PAPvault's one library is uPlot 1.6.32 as its author published it, unmodified, and that nobody has to take that on trust.

**How:** `sha256sum lib/uplot/*`, and compare with the table in `SOURCES.md`. Then check that `lib/` holds nothing else, and that the page names the library and its license where a reader can see it.

**Failure:** any checksum differs from the table; a file in `lib/` that `SOURCES.md` does not list; or a library in the page that Z has not approved by name.

## `rebuild` -- the served file is the one the source builds

**Protects:** the claim that anyone can rebuild the page and get the file that is served.

**How:** in a clean checkout of the release commit, run `python3 build.py` twice, then `curl -sS <PAPvault URL> | sha256sum`. The build prints the version beside the checksum; check it against `VERSION` and against the version in the page's own footer, which is the only way to tell from a running page which build you are looking at.

**Failure:** the two builds print different checksums; the served file's checksum differs from the build's; or the footer's version is not the one in `VERSION`.

## `oximetry-off` -- the untested signal is not read

**Protects:** that nothing PAPvault has never been able to test against a card reaches a reader, and that it decides nothing behind the scenes either.

**How:** open a card, pick a single day, and read the row of checkboxes above the plots: there are eight, and Oximetry is not among them. Read the Manual's section on the plots, which says so and why. On a card that holds `_SAD.edf` files, check that a night's length is the same as it would be without them -- the session box's total must match the flow and pressure, not an oximeter that ran on after the machine stopped.

**Failure:** an Oximetry checkbox; an oximetry plot drawn; a `_SAD.edf` file appearing among the files the page opened; or a night whose length follows an oximeter rather than the therapy.

## `calendar-select` -- the calendar selects the days it says

**Protects:** that the period the summary describes is the period that was chosen, with a day running from 6 in the morning to 6 the next morning.

**How:** open the page and note the preselected day and the time; click a day other than the preselected one; click a later day in the same month; click once more; then go back a month and click a day there; then select a range that contains the Sunday in early November when daylight saving time ends. Open the month picker from the month name, step back a year, and choose a month.

**Failure:** the preselected day is not the CPAP day containing the current time, so before 6 in the morning it is not yesterday's date, and from 6 onward it is not today's; the first click selects a range rather than that one day at 6:00 to the next day at 6:00; after the second click, the shaded days, the two ends or the day count disagree with the days clicked; the third click does not start over; the range picked in reverse across the month boundary is wrong; the range across the time change shows a day count that is not a whole number or is off by one; or the month picker does not move the calendar to the month chosen.

## `time-format` -- times follow the reader's choice

**Protects:** that every time on the page is shown the way the reader chose, and that the choice lasts.

**How:** in a fresh private window, open the page and note the time format it starts in; open Settings and switch to the other format; reload.

**Failure:** the page does not start in the format the browser's language uses, 12-hour for United States English and 24-hour for most others; after switching, any time on the page is still in the old format; or after the reload the choice is lost. A private window that blocks storage may lose it on reload, which is not a failure.

## `sessions` -- a night is counted as the machine recorded it, not as it stamped it

**Protects:** that one night's sleep is one session, whatever the machine chose to call its files, and that a real break is still two.

**How:** read a card and look at a night you know you slept through. Count the sessions the summary gives. Then count the `_EVE.edf` files in that night's `DATALOG` folder: the two should agree, since a machine writes one per recording. On a night when you know the mask came off for a while, check it reads as two. Compare the total hours against the plots: a break longer than five seconds shows as a gap in the flow line, and the hours must not include it.

**Failure:** a night you slept through shown as two or three sessions; a session count higher than the number of `_EVE.edf` files for that night; a break of minutes swallowed into one session; or hours that count time when nothing was being recorded.

## `calendar-step` -- the day buttons move between nights that hold data

**Protects:** that stepping through nights never lands on one with nothing to show, and stops at the ends rather than running off.

**How:** read a card, pick a night in the middle, and click **Next day** until it goes dead, then **Previous day** until it goes dead. Watch that the calendar follows into the next month when the run crosses one, and that a selected range collapses to a single day on the first step.

**Failure:** a step onto a day whose summary says the folder holds no recording here; a button still live at the first or last night on the card; the calendar staying on the old month while the selected day is in another; or a range that survives a step.

## `landing` -- the page before anything is read points at the manual

**Protects:** that someone opening PAPvault for the first time is told to read the manual before they read their own data, and can reach it from where they are standing.

**How:** load the page with nothing selected. Read what the Plots card says, click the button it offers, and check the manual opens at its first section. Close it, read a folder, and look at the Plots card again.

**Failure:** the card says only that nothing is loaded; the button does nothing, which is what happens if the dialogs are bound once per element at load rather than by delegation; the manual opens somewhere other than its beginning; or the invitation is still on the page after a folder has been read.

## `sticky-bar` -- the top bar stays reachable

**Protects:** that the folder, the calendar, the manual and the theme can be reached from anywhere in a stack of plots that runs several screens long.

**How:** read a card, pick a single day so the plots are long, and scroll to the bottom. Check the bar is still at the top of the window and that a plot is passing underneath it rather than over it. Then narrow the window until the bar wraps onto two rows, and check the summary and calendar cards still begin below it rather than under it.

**Failure:** the bar scrolls away; a plot, a title or a legend row draws on top of it; the sticky cards start underneath it or leave a gap that grows when the window is narrowed; or the bar covers the first card on a narrow screen.

## `narrow-calendar` -- the calendar is reachable on a narrow screen

**Protects:** that below 650 pixels wide the calendar moves into a dialog rather than disappearing, and keeps its selection.

**How:** select a range on a wide window; narrow the window below 650 pixels; open Calendar from the top bar; widen the window again.

**Failure:** below 650 pixels the Calendar button is missing or the calendar still shows in the card; the dialog's calendar does not show the range selected before; or after widening, the calendar is not back in the card.

## `card-read` -- reading a folder finds the nights it holds, and opens nothing else

**Protects:** that every session on a card is found, that each lands on the right CPAP day, and that only night data is ever opened.

**How:** open Select Folder and choose a card. Compare what the page reports -- the count of night files, the sessions, the days, the first and last recording -- with what is on the card. On a synthetic case from `dev/synthetic/out/resmed/`, compare with its `answer.json`. Check the calendar's dots against the days in it. Then, with the developer tools open, confirm that a session beginning after midnight is dated to the day before, and that the page reports every file it refused.

**Failure:** a session missing, counted twice, or dated to the wrong CPAP day; a count that disagrees with the card; a dot on a day with no recording, or none on a day with one; a file named in `formats/resmed.md` as never opened appearing anywhere in what the page read; or a malformed file that is read past rather than named and skipped.

## `day-plots` -- one night's plots line up and move together

**Protects:** that a cursor at one place in one plot means the same moment in every other, which is the whole reason the plots are stacked.

**How:** pick a single day with data. Check every plot on, then off one at a time. Move the pointer across a plot and watch the others. Drag sideways to zoom; then scroll the wheel over a plot with nothing held, and again with Ctrl held; then pinch on a trackpad if you have one; then double-click. Compare the first and last times on the bottom axis with the session times the summary names. On a night with two sessions, look at the gap between them. Read the bottom axis: every label carries seconds, none runs into the next, and the last one is whole rather than cut off at the right edge. Zoom in until the ticks are a few seconds apart and read them again.

**Failure:** the plots' left edges or right edges do not line up with each other; the cursor line appears in one plot and not the rest, or at a different place in each; a zoom in one plot does not move the others; **a plain scroll over a plot zooms instead of moving the page, or Ctrl and the wheel moves the page instead of zooming**; double-click does not return to the whole night; a line is drawn straight across the gap between two sessions instead of breaking; the axis runs outside the night's own start and end; two time labels overlapping, or the last one clipped by the edge of the plot; a time label without seconds, or two neighboring ticks reading the same moment; or a plot whose signal the card does not hold is drawn empty rather than named as missing.

## `event-colors` -- an event sits on the row that names it

**Protects:** that an event is shown against the words the device wrote for it, and never against another event's name, and that one order of names runs through everything that lists them.

**How:** pick a day with more than one kind of event. In the strip at the top, check that each row's bars line up in time with the shading of the same color in the plots below, and that the name on the row is the name of the event at that time. Compare against a synthetic case's `answer.json`, which gives every event's text and time. Then look at the bar chart in the summary: the bars run longest at the top down to shortest at the bottom, the longest one in the first color of the palette and the rest in the palette's order, and each count starts just to the right of its own bar's end. Open the Legend and check that it lists the names in that same order with those same colors. Pick a different period in which the names are written a different number of times and check that all three move together.

**Failure:** a bar on a row whose name belongs to a different event; a color in the strip that is not the color shading that event in the plots below; two different names sharing one color while a color goes unused; an event in `answer.json` missing from the strip; a shorter bar sitting above a longer one; the first color on a bar that is not the longest; a count centered on the end of its bar, overlapping it, or sitting far from it; or the Legend giving an order or a color the bars do not.

## `summary-plots` -- the figures are the arithmetic they claim

**Protects:** that the top card describes the period that was chosen, and that its figures come from the recording rather than from anywhere else.

**How:** pick one day and read the boxes, then count the event bars against the events the strip in the Plots card shows. Check that the summary card sits on the left and the calendar on the right, that both stay put while the plots scroll, and that neither has grown a sideways scrollbar. Then pick a range and compare hours used, session count, events per hour and the pressure and leak figures with a synthetic case's `answer.json`. On a range, check that a day with none of an event shows zero rather than a break in its line. Check that the date axis names each day once, that the first and last bar are drawn whole, and that a day with no recording inside a chosen range leaves a gap rather than a zero. Read the leak box's `Dur.` against the leak plot for the same night: it can never be longer than the machine ran, it equals the running time only where the leak plot never touches zero, and it is zero only where the plot sits on zero throughout. On a range that row reads `Dur./day` instead: multiply it by the number of days the session box gives under "Across" and check the result against those nights' own figures added up.

**Failure:** a figure that disagrees with the card; a lowest above a mean or a highest below one; hours that look like a count of samples rather than elapsed time; an event bar whose number does not match how many of that event the day holds, or whose color differs from that event's color in the plots below; a day inside the period with a gap in an event's line where it should read zero; a sticky card that scrolls sideways or covers the plots; a repeated or missing date on the axis; a bar cut off at either end; a negative value on a figure that cannot be negative; a leak duration longer than the machine ran, or equal to it on a night whose leak plot drops to zero; a range whose row still reads `Dur.` rather than `Dur./day`, or whose figure is the period's total rather than the average across its days; or the charts failing to draw for a period in which a signal never changes, as a machine at a fixed pressure produces.

## `contrast` -- the colors stay readable in both themes

**Protects:** that a change to the palette does not quietly make text hard to read, especially where text sits on the accent color.

**How:** in both themes, look at a selected day and a selected month in the calendar, the current section in the manual, a link, and the muted text under the calendar. Then look at every plot line and every event color in both themes. The agent's measured ratios at the last change were 5.07 for white on the selected day in light, 5.85 for the dark theme's, and above 4.6 for every link and muted line.

For the plots, measured against each theme's own surface: **in the dark theme every one of the 22 colors clears 3, the lowest being blue at 3.26.** In the light theme seven do not, and each is there on purpose -- the event yellow at 1.32, flow limitation at 2.06, the event orange at 2.25, the event sky blue at 2.31, and the respiratory rate and hours-used green at 2.98. Those are published values, from Okabe and Ito and from ColorBrewer's Dark2, kept whole rather than adjusted, and Z has looked at each of them in place.

**Failure:** any text that is hard to read against what is behind it, a selected day whose number is faint, a focus outline that cannot be seen against the card, a plot line that disappears into its background, or two lines in one plot that cannot be told apart from each other. A color below 3 that is **not** in the list above has drifted and is a failure even though the ones above are not.

## `manual-nav` -- the manual opens one part at a time

**Protects:** that the list of sections stays short enough to read, which is why the groups collapse at all.

**How:** open Manual. Note which group is open and how many section buttons are showing. Click another group's heading, then a section inside it. Click that group's heading again. Then narrow the window below 650 pixels and do it once more.

**Failure:** more than one group open at once; picking a section leaves its own group shut, or leaves another group open; a group heading that does not collapse when clicked a second time; the `+` and `-` not matching what is open; or the section being read disappearing when its group is collapsed -- collapsing hides the buttons, not the text.

## `manual-truth` -- the manual says only what is true today

**Protects:** the manual is part of what PAPvault delivers, and a claim in it that the page does not keep is worse than no manual at all.

**How:** open Manual and read every section against the page as it stands: what is built and what is not, which files are read, which fields are skipped, which machines are claimed, and what the account of how it was built says.

**Failure:** any sentence that is not true on the day it is read, a feature described as working before it works, or a machine named as supported that has not been tested.

## `folder-select` -- choosing a folder reads nothing and sends nothing

**Protects:** the promise, at the one moment a reader hands the page their data. Choosing a folder gives the page a list of files and nothing else.

**How:** open the developer tools' network panel, then Select Folder, and choose a copy of a card with the Choose Folder button. Do it again by dragging the same folder onto the box. Compare the count the page shows with the number of files in the folder, counted outside the browser.

**Failure:** any request in the network panel; a count that does not match; a file's contents appearing anywhere on the page; or the drag not being recognized. The browser asking whether to upload the files is the browser's own wording and is not a failure, but the page saying anything that is not true about it is.
