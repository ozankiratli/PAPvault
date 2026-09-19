# The card layout and the calendar

**Written 2026-09-19, against the tree at `690129c`.** The page as it became cards, in two rounds the same day, before any data could be loaded and before a charting library was chosen. The brief behind both rounds is in `product-brief.md`, under *Added 2026-09-19*.

## What was built

**Two cards.** The top card holds the summary on the left and a monthly calendar on the right; below it, a card for the plots. Both show only a placeholder until data can be loaded. The Date and Time placeholders in the top bar went, since the calendar now lives in the card and the time range will be selected on the plots.

**The top bar opens dialogs**: Select Folder, which so far only says what it will do, and Manual, which is empty. All dialogs are native `<dialog>` elements opened with `showModal()`, so the browser handles focus and the Escape key; each closes with its own button or a click on the backdrop.

**Below 650 pixels the calendar moves into a dialog**, opened by a Calendar button that appears in the top bar only then. There is one calendar, moved between the card and the dialog, so its selection cannot differ between the two. The breakpoint is written once, in `app.js`, which sets a `narrow` class on the page for the stylesheet to follow; a media query in the CSS as well would have been a second copy to keep in step.

**The month name opens a month picker**: the year at its top with arrows either side, and the twelve months below it. Choosing one moves the calendar there.

**The CPAP day is defined in code on its own.** `cpapDayOf()` names the CPAP day containing a moment, and `cpapDayStart()` gives the 12:00 at which a CPAP day begins; the label is built from the latter. The page opens with the CPAP day containing the moment it was opened already selected, and that day is outlined.

**The theme button shows a glyph and a word**, naming the mode it switches to: a moon and "Dark" in light mode, a sun and "Light" in dark mode. Each glyph carries U+FE0E, which asks for its text form rather than an emoji. In the source they are `\u` escapes, so `app.js` stays ASCII; the trap in writing them is in `platform-traps.md`.

## Decisions the agent made, for Z to overrule

- **Selecting.** A click selects one day and waits for a second. A click on another day then makes a range from the two, in whichever order they were clicked; a click on the same day again settles on that one day. The click after either starts over. A hint under the calendar says so, and says what a day is.
- **The label spells out the CPAP day.** One day reads `2026-09-10 12:00 to 2026-09-11 12:00`; a range adds the count of days. The label is the definition of a day made visible, rather than a date the reader has to know to interpret.
- **Dates are ISO**, `YYYY-MM-DD`, so no reader has to guess which of two numbers is the month.
- **Weeks start on Sunday.**
- **The calendar is rebuilt on every change**, with `createElement` and `textContent` only. Focus goes back to the day that had it, so a keyboard user does not lose their place.
- **The folder dialog promises nothing is uploaded.** That sentence is user-facing, so it is Z's to keep or reword.

## A mistake the default selection introduced, and its fix

The first round selected nothing on load, and treated a first click as the start of a range and a second as its end. When the second round preselected the current CPAP day, that logic read the preselected day as a pending first click: clicking the 10th on the morning of the 19th would have selected the 10th to the 18th. It was found while rewriting the `calendar-select` checklist entry, before any probe had run, and none of the first round's probes could have caught it, since they began from an empty selection. The fix keeps the state explicit: a selection is always a start and an end, and a separate flag says whether a click is waiting for its partner. The preselected day is not waiting.

## The third round: icons, Settings, and the wording

**Every top-bar button is an icon**, with its name shown beneath it on hover or keyboard focus. The icons are small SVGs drawn by hand in `index.html`, not Unicode characters: Unicode has no plain-text calendar, folder or book, only emoji, which render differently on every system and ignore the theme. An SVG takes the text color of the theme it is in, and needs nothing the policy blocks. The name shown on hover is the button's `aria-label`, read by the stylesheet (`content: attr(aria-label)`), so the label a sighted reader sees and the one a screen reader announces are one string. The month and year arrows and the close buttons carry the same labels; a close button shows its label to its left, since below it the label covered the next-month arrow.

**Settings opens a dialog** whose first choice is the time format, 12-hour or 24-hour. Until the reader chooses, it follows what the browser's language uses, read from `Intl.DateTimeFormat().resolvedOptions().hourCycle`; the choice is kept in `localStorage` beside the theme's.

**The theme button shows a moon or a sun**, the mode it switches to, and says so on hover. It swaps two SVGs with the `hidden` attribute through `toggleAttribute()`: an SVG element has no `hidden` property, so assigning `.hidden` would have done nothing.

**The calendar's hint was rewritten** as American prose, after Z found *"Each day runs from 12:00 to 12:00 the next day"* unclear: *"Days run from noon to noon, so each night belongs to the date it began."* A tool to catch Britishisms in the style of PoolSeqFlow's `americanize.py` was not built: the page's prose is a few sentences, read in review.

## What the agent checked

These are the agent's checks, not Z's verification.

- **Clicking.** A scratch copy of the built page, with extra hashed scripts: one before the app that fixes the clock at 2026-09-19 09:00, and one after it that clicks days by date and reads the label after each click, run in headless Chromium with `TZ=America/New_York`. It returned: the preselected day, `2026-09-18 12:00 to 2026-09-19 12:00`; a first click on the 10th, `2026-09-10 12:00 to 2026-09-11 12:00`, the case that shows the mistake above is fixed; the range to the 18th, `(9 days)` with 7 cells shaded and 2 marked as ends; a new single day; the same day clicked twice, still one day, after which the next click starts over; a range picked in reverse across the month boundary, `2026-08-28 12:00 to 2026-09-16 12:00 (19 days)`; and a range across the end of daylight saving time on 2026-11-01, `(4 days)`. Without the rounding in `dayCount()`, the extra hour of that night would have shown as a fraction, so that case can fail.
- **The preselected day.** With the clock fixed at 09:00 and 11:59 on 2026-09-19 the page opened on the 18th; at 12:00 and 15:00, on the 19th; at 09:00 on 2026-10-01, on 2026-09-30, showing September; at 09:00 on 2027-01-01, on 2026-12-31, showing December 2026.
- **Dialogs and placement.** At 1100 and at 420 pixels wide: the month picker opens on the shown year, steps back a year, and choosing March closes it and shows March 2025; Select Folder opens and closes with its button; Manual closes on a backdrop click. At 1100 the calendar sits in the card and the Calendar button is hidden; at 420 the calendar sits in its dialog and the button shows.
- The browser logged no policy error and no exception, and the markup grep still finds nothing in `src/`.
- Screenshots in light and dark mode, of the month picker and the folder dialog, and at a phone's width with and without the calendar dialog open. At that width the top bar wraps onto two rows.
- **Third round, settings.** With the clock fixed at 09:00 on 2026-09-19 and United States English: the label read `2026-09-18 12:00 PM to 2026-09-19 12:00 PM` with the 12-hour choice checked; choosing 24-hour gave `2026-09-18 12:00 to 2026-09-19 12:00` and stored `24`; choosing 12-hour again restored the first form. The theme button's label and icon flipped with the theme. The top bar's labels read Calendar (hidden at that width), Select Folder, Manual, Settings, and Switch to Light Mode.
- **Third round, the browser's language.** Started with `LANG=de_DE.UTF-8`, the browser reported the locale `de` and hour cycle `h23`, and the page opened in 24-hour form; with `LANG=en_US.UTF-8`, `en-US`, `h12`, and 12-hour form. The first attempt passed `--lang=de-DE` instead, which the browser ignored, and every language came back 12-hour; that trap is in `platform-traps.md`.
- **Third round, screenshots**: a hover label shown under keyboard focus, the Settings dialog in dark mode, and a phone's width, where the five icons now fit on one row.

## The charting library, measured before the choice

The brief asks for plots on one time axis with a tracking line shared across them, and a selection that runs along the x-axis only. Z named Plotly's select feature; the agent had suggested uPlot earlier. On 2026-09-19 both were measured against the rules in `CLAUDE.md`, from the packages as published on npm and fetched through jsDelivr into a scratch directory, never into the repository.

| | uPlot 1.6.32 | plotly.js-dist 4.1.1 | plotly.js-strict-dist 4.1.1 |
|---|---|---|---|
| License | MIT | MIT | MIT |
| Runtime dependencies | none | none | none |
| Unminified file | 150,232 bytes | 10,106,046 bytes | 10,945,439 bytes |
| Lines matching `new Function` | 0 | 1 | 1 |
| Lines matching `\beval\(` | 0 | 1 | 1 |
| Lines matching `innerHTML` | 0 | 10 | 10 |
| Lines matching `.attr('style'` | 0 | 5 | 5 |
| Lines matching `createElement('style'` | 0 | 2 | 2 |

The counts are lines matched by `grep -cE`, not an audit: some of Plotly's may sit in code PAPvault would never run. But `no-markup` in `CHECKLIST.md` greps everything that ships, so vendoring either Plotly build as it stands would fail it, and showing those lines unreachable would mean reviewing ten megabytes.

uPlot's source has both behaviors the brief asks for. Charts that share a sync key move their cursors together (`_sync`, at line 1735 of `dist/uPlot.iife.js`), and a drag selects along x only by default (`drag: { x: true, y: false }`, at line 1380).

**Z's objection, the same day**, which is about the reader rather than the rules: *"In terms of the way people will interact with this tool, is that they might want to zoom in and zoom out into certain points during their sleep. An apnea event happens only for a few seconds, and the user might want to investigate that. With uPlot we'd need to set up filters and stuff. It's not great experience for the user."*

What the two sources say on that, read the same day:

- **uPlot** zooms by dragging along x, since a drag sets the scale by default (`setScale: true`, line 1381), and resets on double-click (its `dblclick` handler). It has no mouse-wheel handling at all, since nothing in its source matches `wheel`, so wheel zoom, panning, hover tooltips and zoom kept in step across plots would be code PAPvault writes.
- **Plotly's strict build.** Its one `new Function` line is a fallback for finding the global object (`return this || new Function("return this")()`, line 127430). The one `eval(` match is a program held as a string, from the MapLibre map library bundled for map traces (line 224718). The `innerHTML` lines are in its bundled copies of d3 and MapLibre. It also creates `<style>` elements at run time (lines 16748 and 17729). Whether the page's hash-only `style-src` lets those work was not tested; it is the first thing a trial of Plotly under the page's policy would show.

## The comparison pages

Z asked for the choice to be settled with data: two scratch pages, two plots each, with a line that tracks the mouse across both. They were built on 2026-09-19 in the agent's scratch directory, not in the repository. Each is one self-contained file under the same policy directives `build.py` writes, with its own hashes, and each reports on the page how long its charts took to build and draw, and every policy violation the browser raised. Both show the same synthetic night, generated in the page from a fixed seed: eight hours from 22:30, flow at 25 samples a second (720,000 points), pressure every two seconds, and 40 events, in which apneas flatten the flow and hypopneas halve it.

- **uPlot 1.6.32**, two charts sharing a sync key. Built into uPlot: the tracking line, drag to zoom along time, double-click to reset. Written for the page, about 40 lines PAPvault would own: wheel zoom around the pointer, and keeping the two charts' zoom in step. Not written: panning.
- **Plotly 4.1.1, strict build**, one figure with two stacked plots on a shared time axis, `hovermode: "x unified"` with `hoversubplots: "axis"`, a spike line across both, wheel zoom and the toolbar on.
- **The same Plotly page with `style-src 'unsafe-inline'`**, added to tell apart what the policy broke from what headless rendering broke.

What headless Chromium showed, with its software WebGL renderer, so the times stand for a ratio and not for Z's machine:

| | uPlot | Plotly under PAPvault's policy | Plotly with inline styles allowed |
|---|---|---|---|
| File | 158,940 bytes | 10,951,389 bytes | 10,951,512 bytes |
| Built and drawn in | 71 to 86 ms | 1,429 to 1,751 ms | 1,454 to 1,460 ms |
| Policy violations | 0 | 2, both `style-src-elem`: Plotly's own `<style>` elements, one of them empty | 0 |
| As drawn | correct | toolbar unstyled and always showing; a pale band over the top of the flow plot; the flow axis title drawn below the chart; no pressure axis title | correct |
| Tracking line, from a synthetic mouse move over the first plot | dashed, on both charts, each with its value in its legend | not tried | solid, across both plots, with one hover box for both; the pressure entry in it prints its time inside the value |

So Plotly works in PAPvault only if the policy allows any inline style. The pages are for Z to try by hand, which is the part a screenshot cannot settle: how zooming into a few seconds of one event feels in each.

One mistake in building them: the first Plotly page shifted its times by the time-zone offset, on the belief that Plotly shows dates without converting them, and its axis ran four hours early. Plotly shows millisecond timestamps in local time; without the shift the axis runs 22:30 to 06:30, as uPlot's does.

## The decision

Z tried the pages by hand and chose uPlot: *"My experience with uPlot was outdated. I cleanly yield. It works."*

The disagreement was settled the way `CLAUDE.md` asks, by building the case that would distinguish the two claims and reading what came back, not by argument. Neither side's first position survived whole. Z's objection, that uPlot leaves the reader without good zooming, was right about what uPlot provides out of the box: its source has no wheel handling. The agent's first case, that Plotly's forbidden lines alone ruled it out, was weaker than the one the pages made, since most of those lines sit in bundled code PAPvault would never run. What decided it was measured: Plotly draws correctly under PAPvault's policy only with inline styles allowed, and uPlot, with about 40 lines of PAPvault's own, gives the zooming the reader needs.

uPlot 1.6.32 is the approved charting library. It enters the repository, unminified and with its license, in the change that first draws a plot.
