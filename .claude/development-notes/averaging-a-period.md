# Averaging a period

**Written 2026-09-24, against the tree at `d9d9bfd`,** which is the commit carrying the work described here. It records decisions that were living in comments in `src/app.js` and `src/plots.js` and have been taken out of them.

Z, 2026-09-24, on why they are here rather than there: *"I have a strict rule about no comments and no dates in the scripts themselves. The definition should only be about what the function below does nothing else. Decisions have their own place: development notes."*

## Why a period can be grouped at all

Z proposed it on 2026-09-23, from the memory measurements rather than from the look of the charts: *"in the multiday view, we should have a selection at the top giving the user to choose daily, weekly, monthly, yearly(?) averages. That would decrease the amount of the loaded data right? And when a period above a year is displayed, we disable daily averages and switch to weekly view, above 5 years we disable the weekly too."*

Two halves, and only the first was adopted.

**The grouping does not reduce what is read.** A summary point is computed from figures that already exist per night, and those figures come from reading every night in the period. Grouping them changes how many points are drawn, not how many files are opened, so it saves drawing and nothing else. The agent said so and Z accepted it; the saving that would matter is in the range view holding `pressure` and `leak` for every session, which is a separate piece of work and is still open.

**No grouping is ever taken away.** Z, on the second half: *"We will give the knob and not enforce it."* So `groupingFor()` picks a starting point from the length of the period -- year above 1400 nights, month above 400, week above 120, day otherwise -- and every level stays selectable at every length, however crowded daily looks across five years. The rule behind it is `CLAUDE.md`'s: a computed default never removes the knob, and how to look at one's own data is not the page's decision.

## The arithmetic

**A group's point is the mean of the nights in it, and the nightly figures are themselves means, so it is a mean of means throughout.** The user documentation says this, because it changes what a number means.

**Nights with no recording are dropped, not counted as zero.** Z, 2026-09-23: *"Nights with no recording are dropped. (mean over 4)"* They are not in the list `meanOf` walks, so nothing has to skip them. A week used on four nights is the mean of four, not four sevenths of a week -- which matches the `Dur./day` figure, which had always been the average across the nights that hold a recording.

**A figure no night in the group carries stays null.** Zero would draw as a measurement of zero; null draws as a gap.

**The charts plot the mean, not the median.** Z, 2026-09-23: *"We also should replace medians with means."* An average of medians is not a statistic of anything, and a period longer than a night averages whatever the chart plots. The summary boxes still list both, because there the figure is of one period and not averaged across anything. Z chose that split when asked: charts only, boxes keep both.

**Sessions are counted, not averaged.** Z, 2026-09-24: *"On the second thought sessions plot should show the number of sessions, not the average."* It is the one figure a group adds up. A consequence worth knowing before it surprises someone: the first and last bars of a grouped Sessions chart are genuinely short whenever those groups are partial weeks or months, where averaging used to hide it.

## What a bar is drawn against

**A grouped chart is padded by half a step, not half a day.** Z reported for several days that the first and last bars of a grouped bar chart were cut in half, and it could not be reproduced because the longest card was five nights in one calendar week. With `long-range` built, the cause was one constant: `showSummary` padded the x scale by half a day at every level. A bar is centered on its point and clipped at the edge of the plotting area, so at a weekly grouping, where uPlot draws bars up to 40 pixels wide and half a day is a few pixels, both end bars lost the half that fell outside.

Z's instruction was to use the daily configuration everywhere, and half a step *is* half a day when the step is a day. The step taken is the shortest gap between two points, which is what uPlot measures a bar's width against, and a month is not a fixed length.

**The consequence at the yearly level is a wide axis.** Half a step there is half a year, so three and a half months of data draw an axis running from the middle of one year to the middle of the year after next, for two bars. Shown to Z on 2026-09-24 and accepted. Capping the padding at the drawn bar's half-width instead would avoid it and is a different rule from the one Z asked for.

## What a point is called

Z, 2026-09-24, on the cursor readout still saying `Day` on a chart whose points are weeks: *"Week should display 'Week of YYYY/MM/DD' / Month should show 'Month YYYY' / Year should show 'YYYY'"*. One formatter feeds both the axis ticks and the readout, so the two cannot drift apart.

The name in front of the reading was the agent's choice and not Z's: `Day` daily, `Period` grouped. `Week: Week of 2025/11/17` reads badly, and the reading already names what it is.

**`Hours Used/day`** is Z's wording, same day, for the chart whose bars are a mean per day at every grouping.
