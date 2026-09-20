# Drawing the plots

**Written 2026-09-20, against the tree at `e4fad7e`,** with everything described here uncommitted, on top of the reader in `reading-a-card.md`. This is the first code that draws anything.

## What was built

`src/plots.js` draws two stacks. The **day stack** is one chart per signal on a single time axis, with an event strip above them. The **summary stack** is one chart per figure with one point or bar per CPAP day. Both use uPlot 1.6.32, vendored in `lib/uplot/`. `src/app.js` chooses between them, computes the per-day figures and keeps the plot picker.

Z set the shape over this session, in five messages:

- *"Seven + Flow + Oxymetry but Oxymetry disabled by default. And the user can pick and choose which plots to display. The plots should be interactive too. So the user can zoom in at any particular time."*
- *"For each event assign a different color."*
- *"Can we convert summary to plots?"* then *"For the single day too."*
- Then, after seeing it: *"OK this didn't go well. Revert the the day summary plots decision. For the day the type of events can be displayed as plots. We should have single bars showing the numbers and types. The top card should be divided into two summary and calendar cards should not be together."*
- And on the bars: *"Not a bar chart but a horizontal bar maybe?"*

So the seven plots the prototype drew (`the-old-interface.md`) plus flow from `BRP` and oximetry from `SAD`, everything checked but oximetry, the choice kept in `localStorage`.

**The summary went one way and came back.** It was built as five charts for any period, a single day included, because that is what Z asked for. Seeing it, Z judged a chart per figure holding one bar to be the wrong thing for one night, and it went back to figures in words, with the day's events as a horizontal bar each -- one bar per event name, its length the number of times the device wrote it, its count printed at the end, in that name's own color. The five charts remain for a range, which is what they were good at. This is the churn the note exists to record: the single-day version was drawn, looked at, and dropped, and only the range version survived.

**The top card became two.** Summary and calendar had shared a card since `page-layout.md`; Z split them into two cards side by side, the calendar only as wide as it needs. Below the narrow breakpoint the calendar card goes away entirely and opens from the top bar, as before.

## The decisions inside it

**One axis width for a whole stack.** Every chart in a stack is given the same left axis width, so their plotting areas start and end at the same pixel and a cursor at one x means the same moment in all of them. The width is measured from the longest event name, up to a cap of 170 pixels, and the stack's title indent follows it through a custom property set from the same place. A name longer than the cap is cut short to fit rather than overflowing.

**A cursor and a zoom shared across the stack.** uPlot syncs cursors across charts that share a sync key. Zoom is not shared by that, so each chart's `setScale` hook pushes its x range to the others behind a flag that stops the echo. Wheel zoom about the pointer and double-click-to-reset are PAPvault's own, about forty lines, which is what the measurement in `page-layout.md` predicted when uPlot was chosen.

**A line breaks between sessions.** A day with two sessions is one chart with a null between them, so nothing is drawn across the gap when the mask was off.

**A period longer than a day opens no waveform file.** The chosen charts decide which signals are loaded, and a range asks only for pressure and leak, which are in `PLD`. The largest file on the card is never read for a summary.

**Units come from the file.** A chart's title takes the unit out of the signal's own header, so "Pressure (cmH2O)" is the file speaking rather than this code.

## The palette

Z: *"For color palette, use the one I used in the old project."* Those values, and how they were recovered, are in `the-old-interface.md`. The light theme uses them exactly.

**The dark theme changes only what failed.** Five of the eight measured under 3 against the dark surface. Each was lifted in lightness with its hue and saturation held, and the rest kept Z's value unchanged. The three pressures share one chart, so they were placed by hand rather than lifted independently: lifting them separately had turned blue into `#5C5CFF` and dark blue into `#5D5DFF`, one step apart and indistinguishable. They are now `#7B93FF`, `#ADD8E6` and `#5757F0`, which are 1.85 apart at the closest -- the same separation Z's own light values had, 1.78.

**Pulse, SpO2 and the session count are the agent's colors,** because the prototype had no plot for any of them. They are marked as such in `src/style.css`. Flow had none either, and Z set it after seeing the plot drawn: gray, dark on the light theme and light on the dark one, which is the only plot color that is neither the prototype's nor the agent's.

**The event colors are ten, and they are the same in both themes.** A color reads at 3 against white only if it is dark enough, and against `#181d26` only if it is light enough, and those two conditions leave a narrow band of luminance where both hold. Ten hues were placed inside it, so every one measures about 4.1 against both surfaces and no second set is needed. The cost is that they differ by hue alone and not by lightness, which is exactly what a color-blind reader cannot use, so the strip writes each event's name on its own row and color is never the only thing carrying it. The manual says the colors mean nothing.

**Their order was wrong, and Z found it with real data.** Z, 2026-09-20: *"the colors of the events are way too close to each other in the palette in their assigned pattern. Can we mix them in a way that I don't feel like I'm playing Hue, lol."* The ten were laid out in hue order and handed out in that order, so a card with five event names got the first five -- red, orange, olive, yellow-green, green -- which is a gradient, not a set of labels.

A palette is used a prefix at a time, and the fix is to order it for that. Ten hues evenly round the wheel were searched over all 362,880 orderings that begin at the same place, scoring each by the smallest Lab distance among its first three, four, five and so on, up to eight. The winner runs red, green, blue, magenta, amber, teal, pink, olive, leaf, violet. The worst pair among the first five went from 20.9 to 47.7; among the first three, from 33.5 to 103.5. At all ten it is unchanged at about 21, as it must be, since the same ten colors are in play whatever order they arrive in.

This is worth keeping in mind beyond color: **a list handed out a prefix at a time has to be ordered for its prefixes, not for the whole.** The first version was the one that reads well as a table.

## And then the whole palette went, because Z asked one question

Z, 2026-09-20: *"Is this colorblind friendly?"*

It was not, and the note above had already said the reason without acting on it: those ten differed by hue alone. Measured by simulating the three dichromacies and taking the smallest Lab distance among the five a card would use, the palette scored **13.9 under protanopia, 9.3 under deuteranopia and 1.0 under tritanopia** -- magenta and amber were the same color. Under deuteranopia the five read as three olives and two blues.

**The cause was the thing the note had been pleased about.** Holding every color at one lightness is what let a single set serve both themes. Lightness is the channel a dichromat keeps. It had been spent to buy a convenience.

**What was tried, and what it cost.** An optimizer allowed to vary lightness found sets that hold up under all four kinds of vision and are unusable: near-black `#0E0E07` and navy `#03033F`, indistinguishable from the axis text. Separation is not the only requirement, and chasing it alone produces murk. Z then suggested ColorBrewer, which is how the reads `R-019` and `R-020` began.

**What the reads found** is in the log; the short version is that licensing ran the opposite way to the agent's prediction, and no published qualitative scheme solves this. ColorBrewer's own `blind` flags are empty arrays in its export, so all eight of its qualitative schemes were measured directly: the best, `Set1`, reaches 10.7 at five colors and fails the contrast bar on white. Three independent lines then agreed on four: the paper Z named selects four, four of Okabe and Ito's eight clear both of PAPvault's surfaces, and the agent's own search over nine palettes found nothing holding five.

**What was adopted.** Okabe and Ito's colors, read from Figure 16 of the Color Universal Design page, unmodified. At five names they measure **22.4, 17.2 and 16.4** against the palette they replaced at 13.9, 9.3 and 1.0. They cost some separation for ordinary vision, 35.1 against 47.7, which is the right way round.

**Each theme takes the subset that reads against its own surface,** at Z's decision: five for the light theme, seven for the dark. The set was drawn for one background and PAPvault has two -- Black fails against the dark surface at 1.24, and Orange, Sky Blue and Yellow fail against the light one. So the palette's size is a custom property rather than a constant in the script, and `eventColorsFor` reads it, because the number differs between themes and two places holding it would drift.

**Each theme's order was searched separately,** maximising the worst pair among the first three, four and so on. That matters more than it sounds: vermilion and reddish purple are the one pair a tritanope cannot separate, and they are both in the set, so the order decides whether a card meets them at four names or at seven. The dark theme reaches seven; the light theme has only five colors to work with and meets them at five. An event may therefore be one color in the light theme and another in the dark, which is what buying the extra colors cost.

**Color still is not the identification.** The strip names every row and the legend lists every name, which is what a reader uses when two colors look alike. The manual says so rather than implying the palette solves it.

**The strip's pixel check broke twice more, and its second break taught something.** It first looked for an orange pixel, and stopped finding one when each event got its own hue. It was then made to look for a *saturated* pixel, which held until Okabe and Ito's set brought in black. Black has no saturation, so the bottom row read as empty.

The fix was not a better colour test. **A uPlot canvas is transparent where nothing is drawn** -- the white or dark surface behind it is CSS, not paint -- so every undrawn pixel is `rgb(0,0,0)` with no alpha, and a black bar is `rgb(0,0,0)` with alpha. No test on colour can separate those. The check now reads alpha alone, which is what actually distinguishes drawn from undrawn and does not care what colour arrives next.

Both earlier versions encoded an assumption about what the data would look like. That is the trap `CLAUDE.md` names -- after a change, ask what was pointed at the old thing -- and it caught this three times in one feature. The check earns its keep anyway: it reports the row order as `[75, 50, 37, 12]`, falling as the strip is read downward, and reinstating the inversion bug turns it into `[12, 37, 50, 75]`.


## Four bugs, each found by looking at the output

**A machine at a fixed pressure would have hung the page.** The first range drawn threw `RangeError: Invalid array length`. The synthetic pressure and leak are constant across every night, so the y scale had zero span, and uPlot built axis splits until the array would not grow. It looked like a quirk of synthetic data and is not: a machine held at one pressure writes exactly that, every night, and fixed-pressure CPAP is the ordinary case. Every y scale now goes through `paddedRange`, which also refuses to put a negative axis under a figure that cannot be negative.

**The event strip's names and its bars were inverted.** The strip's top row was labeled `Synthetic event two` while the bar on that row was the 22:40 event, which is `Synthetic event one`. uPlot's y axis counts up from the bottom and the drawing counted down from the top, so every event was shown against another event's name. Nothing in the DOM could have caught it, because uPlot paints axis labels onto the canvas. The check that did is a probe that reads the strip's pixels row by row and reports where each row's first bar starts: the values must fall as you go down the strip, since the rows are in first-seen order and first-seen is earliest. Those values fall as you read down the strip now, and putting the bug back makes them rise. The numbers themselves move with the card's width, so what the check asserts is the order and not the pixels.

**Every summary chart was drawn at the 320-pixel minimum.** `#summary-plots` had a `:empty { display: none }` rule, so at the moment its width was measured it was not laid out and `clientWidth` was 0. The rule is gone and the script shows the container before drawing into it. The lesson is narrow but repeatable: a rule that hides an element from the stylesheet also hides its size from the script.

**A fourth, in a check rather than in the page.** After each event got its own color, the strip's pixel check started reporting no bar on its top row. The check had been written to look for orange, and that row had become green; the page was right and the check was aimed at what used to be there. It now looks for any saturated pixel. This is the trap `CLAUDE.md` names -- after a change, ask what was pointed at the old thing -- and it cost nothing only because the check reported an impossible result rather than a pass.

## What Z changed after seeing it drawn

A second round, all of it from looking at the working page:

- *"Let's make event lines thicker and more pronounced. Also have a legend."* An event is now a solid line at the moment it began with its duration shaded behind, rather than a faint band alone. At a whole night's width a ten-second apnea is well under one pixel, so without the line it was invisible.
- *"Scrolling on the plots zooms in and out. It should be either pinching or Ctrl+Scroll. Normal scrolling should just scroll through the page."* Correct, and it was the agent's own addition rather than anything uPlot did. The wheel handler now returns unless Ctrl is held, which is also what a trackpad pinch sends.
- *"'Recording starts' is an event in Resmed apparently, we should remove it. Didn't my code already do it?"* It did not: `R-003` records that `prepare_data()` drops only *empty* annotations, and separately **adds** rows named "Recording starts" and "Recording stops" taken from each signal file's header. PAPvault already drops the EDF+ time-keeping annotation, which is where the generator puts that text, so it had never appeared on synthetic data. A named list in `card.js` now leaves those texts out of the events. **It matches on exact text, so a device set to another language would not be caught**, and that is recorded here rather than hidden.
- *"The directory box still opens as 'Upload'."* That window is the browser's, and a page cannot rename it: choosing a folder is one browser feature whether the page uploads it or reads it in place. The page's own button became "Read Data" and the note beside it now says plainly whose window the next one is. The dialog also closes itself once a card is read, unless there was nothing to read or a file was refused, since closing then would hide the report.
- *"This is impossible to read. Let's make this more presentable."* The day's figures were four sentences of prose. They are now three tinted boxes -- session, pressure, leak -- with mean added to median and the 95th percentile. Z specified the boxes, their contents and the tinting.

The session box is tinted with the hours-used green rather than the accent, because the accent and the mask-pressure blue are close enough that two of the three boxes did not read as different colors.

## A third round, and the layout it settled on

- *"Let's move the calendar on the right. (sticky) Summary moves to left, becomes sticky, Daily view shows summary. But the boxes are arranged: 2 boxes / 1 box / bar chart. Summary plots gets displayed inside plots card. Plots card remains the same size and remains in the middle."*
- *"For pressure, we should have max and min, for leak we should have max."*
- *"If an event is not recorded on one day, we should set the number to zero. Retrospectively."*
- *"Let's make gray a little darker on dark and lighter on light."*

**Three columns above 1200 pixels**, summary and calendar sticky either side of the plots. Below that they stack; below the narrow breakpoint the calendar still leaves the page for its dialog. The page's width cap went from 72rem to 100rem, so putting two columns beside the plots did not take the plots' own width away. This is the one breakpoint written as a media query: the 650-pixel one is in `app.js` because the script has to move the calendar element, and there is nothing for the script to do at 1200.

**The summary card now describes the period rather than the day.** It was showing the day's figures for one day and a single sentence for a range; it now shows the same boxes either way, computed over every session in the selection, with the range's charts moved into the plots card. So the two cards divide by question rather than by length of period: the left says what the period was, the middle draws it.

**Zero, not a gap.** A name the machine wrote on any day of the period now reads zero on the days it wrote none. The line used to break there, which reads as "not known" when what is known is that there were none of them.

**Two faults the three-column layout introduced, both found by looking:**

- Every sticky card grew a horizontal scrollbar. `overflow-y: auto` on its own makes `overflow-x` compute to `auto` as well, and the calendar was 17rem inside an 18rem column. Both axes are now named, and the calendar takes the width of the column it is in.
- The event chart was floored at 320 pixels wide, which is wider than the summary column. It has its own lower floor, and its left axis may not take more than half the card, so the names cannot crowd out the bars they label.

**The greys moved toward the middle.** Flow was `#3A3F47` on light and `#CED4DE` on dark; at Z's word it is `#5A616B` and `#AAB2BE`, still 6.3 and 7.9 against their surfaces and 4.8 and 6.1 against the gridlines.


## What was checked

These are the agent's checks, not Z's verification.

- **The stack lines up**, measured rather than eyeballed: every chart's `.u-over` reports one `left` and one `width` per stack. The first run reported the bottom chart 25 pixels narrower than the rest, because uPlot reserves room on the right only for a chart whose time axis is shown; every chart now has the same explicit padding.
- **The page draws both stacks** from a probe carrying a whole synthetic card through the real file input. One day: the figures in words, one event chart, and 9 day charts, with the picker shown. A five-day range: 5 summary charts, no day charts, the picker hidden. No policy violation and no uncaught error in either.
- **The figures match the card**: one day reported 1 session, 8 hours, 10:30 PM to 6:30 AM; the five-day range reported 6 sessions on 5 days and 36 hours. Both agree with `answer.json`.
- **The reader still agrees with the answers**: 822 checks, no mismatches, unchanged by any of this.
- **The event strip** check above, shown to fail when the bug is put back.
- **Screenshots** of both stacks in both themes.
- **The wheel**, by dispatching one over a plot with and without Ctrl and reading back whether the page kept the event and whether the canvas changed. Without Ctrl: not prevented, canvas unchanged, so the page scrolls. With Ctrl: prevented, canvas redrawn. A handler that swallowed the event without zooming would fail the second half.
- **The legend**, by clicking its button and reading the panel back: it starts closed, opens, flips `aria-expanded`, and lists every event name against the exact palette color the plots give it.
- **The folder dialog closing itself**, read from the same probe: after a card is read it reports `open` as false, and the button reads "Read Data".

## What is not checked

- **No real card**, so no real event name, no real signal label, and no palette seen against real data. All of that is Z's.
- **The cursor sync and the zoom were not driven by a synthetic pointer.** They are uPlot's own for the cursor, and PAPvault's roughly forty lines for the zoom; nothing here has moved a mouse across the stack. That is the first thing for Z to try by hand, and `day-plots` in `dev/CHECKLIST.md` says so.
- **Nothing has more than four event names**, so the palette has never cycled and the ten colors have never all been on screen at once.
- **No period longer than five days has been drawn**, so how the date axis behaves over a month or a year is untested.

## A fourth round: what Z changed after living with it

- *"Let's replace 'black' event with another color."* Black was the only one of Okabe and Ito's eight to clear PAPvault's contrast bar against white, so removing it meant accepting something under the bar. Of what was left, Sky Blue reads best at 2.31 and Yellow separates best but measures **1.32**. Z: *"I think yellow works fine somehow."* It was put in and rendered in place rather than argued about, and it does read: a saturated hue at two pixels carries even where its luminance contrast does not. The measurement stands in `src/style.css` beside the value, because it is the kind of thing a later reader should be told rather than left to rediscover. Placing yellow third, not last, keeps reddish purple out of the first four and lifts the worst pair at four names from 0.9 to 20.9.
- *"Move Session box on top of Pressure and leak boxes."* Done, which reverses the two-then-one arrangement Z asked for the round before. The session box was always the one that needed the full width.
- *"Let's lose the row showing '2026-03-10 6:00 AM to 2026-03-15 6:00 AM (5 days)'. And display date for the single day inside the Sessions box."* The period line went, and the session box gained a `Day` row. Z's reason is worth recording because it is a rule and not a preference: *"The calendar already says what a day means, the manual should too. We don't need to repeat it so many times."* The definition belongs in the calendar's hint and in the manual, and nowhere else.
- Removing that line left `renderSelection` and `renderSummary` as two functions that did nothing but call `renderPeriod`. Both went.

## The manual's navigation

Z: *"Too many buttons in boxes on the left feels crowded. Maybe each H1 is collapsible and when an H2 is picked only that H1 is open, the others remain collapsed?"*

Fifteen section buttons were shown at once. Each `#` heading in `docs/manual.md` is now a group that collapses, holding its `##` sections; one group is open at a time, and choosing a section opens the group that holds it and shuts the rest. Clicking an open group's heading closes it, which hides its buttons and not the section being read.

`build.py` emits the groups, so the markdown did not change shape. A manual that began with a section rather than a group would still work: the renderer makes an unnamed group to hold it, rather than dropping the button on the floor.

Measured from the page rather than asserted: on opening, three groups with the first expanded and **5** section buttons visible; after choosing the last section of the last group, only that group open and 6 visible; after collapsing it, 0 visible and the section still on screen.

## A fifth round: the prototype's palette leaves, and ColorBrewer arrives

Z, 2026-09-20, after seeing the dark theme: *"The dark view was fine, now we have 2 blues there."* Then the order, set explicitly: orange, bluish green, yellow, then sky blue or blue, then reddish purple or vermilion, with each theme taking the other of the pair next. **Both themes now carry all seven**, differing only in order, so neither meets its second blue or its second red early.

That order measures worse than the one it replaced -- 16.4 at three names against 31.2 -- and the reason it is still right is that **all three of its close pairs are close only under tritanopia**. Orange with yellow, orange with vermilion, bluish green with blue: under protanopia and deuteranopia, the two that between them account for almost all color blindness, the seven stay apart. A single worst-case number hid that, and it is the argument for reporting per kind rather than as one figure.

A count in the events chart sat six pixels from the end of its bar, which on a bar that ended at a gridline left the numeral touching both. Measured from the rendered page rather than judged: the gaps were 1, 3, 4 and 4 pixels. They are 5 to 8 now.

**The signal plots left Z's prototype palette.** Z: *"For the other plots it is not extremely important for them to be color blind friendly as they display a single color. Each color can be selected from r brewer palettes dark2 for light theme and set2 for dark theme. They match too, it would work."* They do match: Dark2 and Set2 pair entry for entry, so a signal keeps its place in the scheme when the theme changes, and entry 8 of each is the neutral grey that flow already wanted. A plot drawing one signal only has to be told from its own background; where a plot draws several, they take different entries.

So the palette recovered under `R-018` -- the blues, the red, the green, the brown and the purple of `CPAP_old/app.R` -- is no longer in the page. `the-old-interface.md` records where it came from and is not rewritten to follow this; what it says was true when it was written.

**ColorBrewer moved from consulted to used, which turned its licence into an obligation.** Condition 2 requires that end-user documentation carry *"This product includes color specifications and designs developed by Cynthia Brewer (http://colorbrewer.org/)."* The manual now carries that sentence verbatim, as a quote rather than a paraphrase, and `SOURCES.md` records the condition alongside conditions 4 and 5, which forbid using the name to endorse this product.

## The manual's navigation, second pass

Z: *"Let's still lose the framed button design, use the same font face and size with H1, but make H2 small caps. When hovered just highlight the background a little, when selected make the H2 bold."*

The navigation no longer looks like controls. Nothing has a frame or a fill; hovering tints the background by mixing seven percent of the text color into it, and the section being read is bold and nothing else, the accent-colored frame that used to mark it being gone.

The first attempt read *"use the same font face and size with H1"* as *make the group look like a heading*, and set it larger. Z: *"The font face for H1 has changed I don't know why? It should remain all caps and smaller."* The sentence meant the other thing -- give the **sections** the same face and size as the group, and separate them by capitals alone. So both sit at 0.8rem: a group in full capitals, its sections in small ones. The lesson is small and general: *"use the same X with Y"* does not say which of the two moves, and the one that reads as obvious to the writer is a coin toss to the reader.

## A sixth round: the counts, the order, and yellow again

*2026-09-20, later the same day.* Z, on the summary's event bars: *"The numbers on the Summary event still not good. You moved them a few pixels but that's not the fix. They are centered highest point, instead they should be left justified."*

The round before had read the counts touching their bars as a spacing problem and widened the gap from six pixels to ten, and left a comment in the source saying why. The diagnosis was wrong. The draw hook is handed uPlot's own canvas context, after uPlot has drawn the axes with it, and it set `textBaseline` but never `textAlign`, so it inherited `center` from the axis drawing and every count straddled the point it was placed at -- half of it over its own bar. One line sets `textAlign` to `left`, and the gap goes back to six. The comment that justified the ten went with it, because a comment that outlives its disproved reason is worse than no comment.

Measured on the four-name card, the count's leftmost pixel now falls 7, 7, 8 and 7 pixels past the end of its bar. With the centering put back it is 4, 5, 4 and 4 -- and those counts are all single digits, which is the weakest case for the measurement to show anything; a two-digit count centered on the same point sits on the bar. The thing that holds whatever the count is, and the thing the check states, is that the count's leftmost pixel is right of the bar's end.

Then the order. Z: *"The Summary event plot, the bars should be from the longest to shortest from top to bottom. Longest gets color1: orange, and the order of colors remain the same."* The names had been handed out in the order the device first wrote them, and that same order gave each its color. Now `renderPeriod` counts the names over whatever period is chosen, sorts them most-written first, and hands that one array to the summary's bars, to the legend, to the per-hour chart and to the day's plots; a tie keeps the order the device wrote them in. So the first color is on the longest bar, and it is the same color for that name everywhere else on the page. The cost is that a name can take a different color when a different period is chosen, and the manual now says so where it used to say the colors follow first appearance.

The strip above the day's plots was left in first-seen order. Its rows carry their own names and its x axis carries time, so nothing there is read off the order -- but it does mean the strip and the legend beside it list the same names in different orders. That is Z's call, not one to make quietly.

And yellow moved: *"For event colors, you were right about yellow (kind of), let's make it the 5th color instead of the third."* It stays in both palettes, everything between third and fifth shifting up one, so a card with three or four names never reaches it. The light order is now orange, bluish green, blue, vermilion, yellow, sky blue, reddish purple; the dark is orange, bluish green, sky blue, reddish purple, yellow, blue, vermilion. The contrast figures do not move, since the set is the same colors in a different order.

A new probe reads the summary's event chart the way the strip probe reads the strip: it finds each bar by its own palette color, places it by the pixels it covers rather than by arithmetic this script and the page would have to agree on, and reports where the bar ends and where its count begins. Patching both behaviors back out made it report the bars ascending down the page, 27, 53, 81 and 108 instead of 108, 81, 53 and 27, and the gaps at 4 to 5. It is in the scratchpad with the rest -- see below.

## A seventh round: seconds, the box order, and a figure that needed a decision

*2026-09-20, later again.* Z asked for three things: the day's times to the second, the two spread boxes reordered, and a new figure, the total time the leak ran.

The seconds were one line, and the second and third order effects were not. At a whole night's width the axis had been drawing about twelve ticks; `10:51:40 PM` is half as wide again as `10:51 PM`, and the labels ran into each other -- `10:51:40 PM1:33:20 PM` on the screenshot. uPlot spaces its splits by a fixed number of pixels, so the axis now measures the widest label it will actually draw, at thirteen moments across the range, and asks for that much room plus a gap. Six ticks, none touching. Then the last label, centered on the very end of the night, was clipped by the plot's right edge: eighteen pixels of padding fitted `6:30 AM` and not `6:30:00 AM`. The stack's padding is now computed from the same measurement -- half the widest label plus a margin -- and every chart in one stack still gets the identical padding, which is the whole reason that constant existed. The probe reports one distinct plotting box for all nine charts in the day stack and one for all five in the summary.

The third was a decision rather than a change, and it went to Z twice. Z's rule: *"calculate each duration from the time stamp right before a leak started to the time stamp it ended - 1 step time difference. Then add all the durations up."* That reads two ways at the end, and they differ by a whole step, so a leak lasting one sample is either one step or nothing. Z settled it: A is the last clear stamp, A+1 to B leak, B+1 clear again, and the duration is `(B+1) - A - 1 step`. That works out to exactly the leaking samples times the step between them, which is what the code does, so a run at the very start or end of a session -- where Z's formula has no stamp to reach back to -- needs no special case.

What counts as leaking was the other half, and `formats/resmed.md` does not say what the leak figure means or where a leak begins. That is a gap, so it went to Z rather than to a plausible number: Z chose any value above zero. **PAPvault therefore has no threshold of its own and no view on what a large leak is**, which is the same reason it has no severity bands. The manual says so in as many words, because a figure called "total time" in a leak box will otherwise be read as time in trouble.

**The synthetic data cannot check that figure, and this is the gap to close.** Both committed cases carry a leak that ramps from 60 to 120 L/min and never reaches zero, so the total necessarily equals the recorded time -- 480m for an eight-hour night -- and a reader that ignored the values entirely would pass. A scratch script therefore writes physical zero over half the leak samples of `plain-night`, through the file's own calibration, and the page then reports 240m against 4 hours known by construction. That belongs in the committed cases as a night whose leak goes on and off with a total known by construction, and it is a case for Z to agree rather than for the agent to add.

The figure is in minutes because of how it fell in the box. Written as the session box writes a duration, `08h 00m` broke across two lines in a column 123 pixels wide, and Z said to use minutes. The values in those boxes no longer wrap at all, and the label fits beside `480m` where it did not beside `480 min`.

## An eighth round: the bar stays, and the page says where to start

*2026-09-20, last of the day.* Two asks from Z: make the top bar sticky, and tell someone who has just arrived to read the manual first.

The bar took one rule and one measurement. Sticky at the top with a z-index above the cards, so a plot passes underneath it rather than over it -- `elementsFromPoint` at the top of the window, after scrolling 900 pixels, finds the bar first and a plot title second. The measurement is the offset the sticky summary and calendar cards start at, which has to be the bar's height plus their margin. Writing that height into a variable and the bar's height into CSS would be two things kept in step by hand, and the first attempt did exactly that: `3.5rem` against a bar that renders 61 pixels, leaving the cards 5 pixels higher than intended. So the page measures the bar and writes `--topbar-height` itself, at startup and on every resize, and the CSS value is a fallback for the moment before the script runs. The probe reports the bar's height, the card's resolved `top`, and the 20-pixel gap between them.

The landing page needed the dialog binding to change. It had been one listener per `[data-dialog]` button, queried once at load, so a button the page builds later opened nothing. It is now delegated from the document, and the probe clicks the button the landing text builds and checks the manual actually opens -- which is the check that fails if anyone puts the old binding back.

What it says, in order: nothing is loaded yet; start with the manual, which says what PAPvault reads from a card and what it never touches, what every figure means, and how a day is counted; then open a folder. The manual comes before the folder because that was the ask, and because by the time someone has read their own data the question "what does this page do with it" has already been answered by the page doing it.

The one thing that could not be seen: a headless screenshot of a scrolled page comes back blank, every time, while `--dump-dom` of the same run reports the scroll happened and the layout is right. That is in `platform-traps.md` now. The sticky bar is therefore checked by measurement rather than by looking, which is a weaker check than this project prefers, and it is named here rather than glossed.

## A ninth round: the duration row, and a word the page does not own

*2026-09-20.* Z renamed the leak duration to `Dur.` and moved it under the 95th, and asked for a daily average rather than a total over a period.

The average is over the days that hold a recording, the same count the session box prints under "Across", rather than over the calendar days between the two dates. A month with four nights on the card would otherwise read as a month of almost no leak. The label carries the difference -- `Dur.` over one night, `Dur./day` over a period -- because the same label on a total and on an average is how a figure gets misread, and the row is the only one in either box that is not a statistic over the samples themselves.

Then Z asked about the word the browser uses: the folder picker says "Upload", and it asks the reader to confirm an upload, on a page whose whole promise is that nothing is uploaded.

**The page cannot change it.** The picker and its confirmation are the browser's own windows, and `<input type="file" webkitdirectory>` has no attribute that renames either; the same windows appear whether a page sends the folder somewhere or reads it where it sits, because to the browser it is the same permission. What the page can do is say so before the reader sees it, which the folder dialog and the manual's list of promises already did, and which the manual's numbered steps now do as well -- along with the one way out, which is that dragging the folder onto the box skips the browser's window entirely.

One thing was left for Z rather than decided here: Chromium has a different API for this, `showDirectoryPicker`, whose wording is about viewing files rather than uploading them. Whether Firefox implements it was **not** checked -- that would need a read of the specification or MDN, and reads are cleared first. Either way it would mean a second path through the code for a label on one browser, which is Z's call and not a tidy-up.

## A tenth round: what a session is, and a sentence the manual could not back

*2026-09-20.* The session box gained an average per day, over the days that hold a recording, matching `Dur./day` and the "Across" count.

Then Z, from a real card: nights that were certainly one night's sleep were showing as two or three sessions, and asked how PAPvault counts them and whether the prototype had handled it.

**How PAPvault counts:** a session is the set of files whose names carry the same `yyyyMMdd_HHmmss` stamp, wherever under `DATALOG` they sit, and the count is the number of distinct stamps. Nothing else enters into it -- not the folder, not the headers, not the gap to the next recording.

**The prototype has no such notion**, which R-004 already recorded before this came up: *"the prototype does not work out days itself: each folder counts as one day"*, and a day's files are every `.edf` in it. R-018 adds that `app.R` prints one start and one end per day. So the prototype takes a day folder whole and never splits it, which means there is no earlier behavior here to match -- the session is PAPvault's own idea, and this is the first time it has met a real card.

**The manual carried a sentence PAPvault cannot back.** It said *"A session is one stretch with the mask on."* PAPvault does not know whether a mask was on; it knows what the machine wrote. That is now corrected to say what is actually counted, with the consequence spelled out: a night can hold more than one session, PAPvault never joins two together, and joining them would be PAPvault concluding something the machine did not record. The wrong sentence is the kind this project is supposed to catch -- it reads as a definition and is really an inference.

**What was not decided here.** Two things would produce what Z saw: the machine wrote several recordings, or it stamped one recording's files a few seconds apart and the grouping split them. `check/card-shape.py` in the scratchpad tells them apart from file names alone, opening nothing, and prints no date and no value. If it is the first, whether adjacent recordings should ever be shown as one is Z's call and needs a threshold, which is exactly the kind of decision PAPvault does not make for itself.

## An eleventh round: the session stops being a file name

*2026-09-20.* Z, on the previous round's answer: *"I think distinct stamps is a wrong way to handle the session number. Because different things get activated at different times. So is the machine lying, most certainly yes (in a sense)."* Z offered the count of `EVE` files as a proxy and then settled on the better rule: **if the recording is cut for more than about five seconds, that is a new session.**

The thing that made this cheap is that it needs no waveform. A gap inside one file would make the file discontinuous, and `card.js` already refuses those; a gap between two recordings is the distance from one file set's end to the next one's start, and both come from headers the scan already reads. `CLAUDE.md` says a period longer than a day opens no waveform file, and that still holds: session counting reads nothing it did not read before.

So `read()` now gathers **recordings** -- the sets of files sharing a stamp, as before -- and then folds them into sessions: sorted by start, each one joins the session still open when `start - end` is no more than five seconds, which takes in every recording that overlaps one already running. That is the oximeter case Z described, and it needs no special handling, because a stream that begins during another ends up with a negative gap.

**No committed case could tell whether this worked.** Every stamp in `plain-night` and `five-days` is hours from the next, and the 822 reader checks pass identically before and after the change -- which is the point: they prove it broke nothing, and prove nothing about what it was for. Three scratch cards do that, each `plain-night` with the `SAD` file moved to a stamp of its own and its header start moved to agree: 40 seconds after the recording began (inside it), 3 seconds after it ended, and 40 seconds after it ended. Under the old rule all three read as two sessions. Under the new one they read 1, 1 and 2, which puts the threshold between the second and third.

What is still open is the figure itself. Five seconds is Z's, and it is a decision the page cannot make for itself, so it is named in the manual in as many words rather than buried as a constant. The real card is where it gets tested: the check to run there is the one now in `dev/CHECKLIST.md`, comparing a night's session count against the number of `_EVE.edf` files in its folder, since a machine writes one of those per recording.

The calendar also gained **Previous day** and **Next day**. They step between the nights the card holds rather than between calendar dates -- a step onto an empty day shows a card saying the folder holds no recording there, which is a dead end -- and they go dead at the first and last night. That is a choice rather than a literal reading of "next day", and it is the kind that should be visible: the manual says which of the two they do.

## A twelfth round: the session becomes the flow, and the first version

*2026-09-20.* This round was mostly the agent being wrong in public, and it is worth writing down plainly.

Z said the session count was wrong, and named the rule: *"if the flow recording is cut more than 5 seconds or something we can record different sessions."* The first build measured the gap between the **file sets** a machine stamps, from the headers of `BRP`, `PLD` and `SAD` together. Z said it was still wrong. The agent then argued that measuring from flow alone could not help, since a flow-only end is never later than the latest of the three, so every gap would grow rather than shrink. **The arithmetic was right and the premise was wrong.** Z was not saying to measure the same sets differently; Z was saying the extra sets are not sessions at all -- *"the machine transmitting stuff unplugged and replugged and all kinds of stuff"* -- and then, flatly, *"You need to trust my understanding of the data!"*

That is the second time in this project the agent has defended its own work with a number where the person holding the data already knew the answer. The lesson is not "argue better". It is that when someone who can see the data states a rule twice, the next move is to build it and measure, and to put the disagreement after the measurement rather than instead of it.

The rule as it now stands:
- A session is one unbroken stretch of **flow**. Two stretches are one session when the flow is cut for no more than five seconds, which takes in any that overlap.
- A set of files with **no flow** in it is never a session. Unplugging the machine and plugging it back in makes it write an event file saying a recording started, with no recording behind it.
- A no-flow set joins the session nearest to it, so nothing it holds is lost, but **it cannot set a session's start or end**. That last clause was itself a bug for about an hour: without it a stray set stamped at two in the afternoon dragged a night's start back to itself, and a set stamped before six in the morning would have moved the whole night onto the day before.

Z suspected the 6 o'clock cut had drifted, which was a good guess at the class of bug and wrong about the place. `cpapDayOf` was checked at every edge it has -- 05:59:58, 05:59:59, 06:00:00, 06:00:01, midnight, 23:59:59, a month end, a year end, a leap day, and both daylight-saving changes -- in three time zones, and it holds. The bug was next door, in what could move a session's start, which is the input to that rule rather than the rule itself.

**Oximetry is off, and this is version 0.0.1.** Z: ResMed records oximetry only on the AirSense 10 and a compatible oximeter is almost impossible to find, so there is no card to test it against and it will be its own piece of work. The chart is defined but not offered, nothing opens a `SAD` file, and oximetry no longer decides how long a night was either -- that is measured from `BRP` and `PLD` alone, so an untested signal cannot set a figure. The version lives in one file, `VERSION`, which the build reads, prints beside the checksum, and puts in the page's footer. That last part answers a question this session could not answer for an hour: which build is the one in front of you.

## Where the checks are, for whoever picks this up

Everything this note reports as measured was measured with scripts that are **not in
this repository**. They are in the agent's session scratchpad, and they go when the
session does. Their inventory is a file called `CHECKS.md` at the root of that
scratchpad: what each one proves, how to run it, and which of them were shown to fail
when the code was broken.

That is a gap, and it is named rather than papered over. Two Node scripts drive
`src/edf.js` and `src/card.js` against the synthetic answers, 665 and 822 checks; five
Python scripts build probe copies of the built page, carrying a synthetic card inline
and feeding it through the real file input, which is how the day and range views, the
event strip's pixels, the scroll behaviour, the legend and the manual's groups were
all checked. Whether any of them belongs in `dev/` is Z's decision and has not been
made: `CLAUDE.md` says there is no automated suite because a suite the agent writes
and runs is the agent vouching for itself, and that reasoning does not stop applying
because the scripts turned out to be useful.

What a reader can re-run today without them: `python3 build.py` twice for the
checksum, the `no-markup` grep, and every entry in `dev/CHECKLIST.md`.
