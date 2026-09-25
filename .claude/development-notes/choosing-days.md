# Choosing days

**Written 2026-09-24, against the tree at `65fe575`,** with everything described here uncommitted.

## What was wrong

The calendar had worked the way most date pickers do since it was built: the first click chose a day, the second turned it into a range, the third started over. Z, 2026-09-24:

> This is an issue I have no real solution for. The clicking around on the calendar. First click goes to the day second selects a range. Clicking around to see individual days is just annoying. The behavior should be every click goes to the day. Not sure how to handle the ranges. Maybe a button below shows "Choose Range", when activated the user has to choose two days?

The complaint is about the common case. Reading through your nights one at a time is what a person does most, and under the old rule every second click did something else.

## What it does now

**A click on a day shows that night.** Always, whatever was selected before.

**A range is asked for.** `Choose Range`, under the grid, and the next two days clicked are its ends in either order.

Four refinements followed, each from Z trying it:

- **The button stays on until it is pressed again** (*"Let's keep choose range active until the user turns it off"*), so ranges can be picked one after another. Only the button ever changes the mode; stepping a day with `Previous day` gives up a half-made range but leaves the button as the reader set it.
- **What is selected is written along the top bar** (*"On the top bar in the middle, we display the selected date"*). It is the only place the selection is named in words, and it never goes blank.
- **Pressing the button puts the old selection aside on the grid** (*"When range button is selected nothing will display selected on the calendar"*, then *"It should only deactivate the already selected day"*). The grid then marks what is being picked now -- nothing, then the first day, then the range -- so a mark on the calendar never means two things at once. The selection itself is untouched, which is why the bar can still name it.
- **The same day twice takes the pick back** (*"pressing the same day chooses only a single day to display. Instead I think it should cancel the selection"*) rather than making a range one day long.

**The plots do not move until both ends are in.** Clicking the first day of a range changes the calendar and the bar and nothing else, so no night is read that nobody asked for, and there is no flash of a single day on the way to a range.

## What it cost elsewhere

**Three page probes were selecting a range by clicking two days**, which under the new rule means "show that night, then show that other night". `make-probes.py`, `make-events-probe.py` and `make-grouped-probe.py` now press the button first, the way a person does. They passed the whole time the behaviour was wrong, because what they asserted was the *result* of a range being selected and they were no longer selecting one.

That is `CLAUDE.md`'s rule earning its keep -- after any change, ask what was pointed at the old thing -- and the answer here was three files.

One trap inside it: in the grouped probe the button has to be pressed **once**, not on each retry of a pick, because pressing it again gives the range up. A retry loop that re-pressed it would have quietly undone itself.

## How it was checked

Every state was read off the running page rather than reasoned about, by driving the calendar in a headless browser and reporting the button's `aria-pressed`, how many days the grid marks, the bar, and the hint:

| state | button | marked | bar |
|---|---|---|---|
| a day selected | off | 1 | `2026-01-14` |
| `Choose Range` pressed | on | 0 | `2026-01-14` |
| first day clicked | on | 1 | `2026-01-05 to ...` |
| that same day again | on | 0 | `2026-01-14` |
| two days clicked | on | 16 | `2026-01-05 to 2026-01-20, 16 days` |
| another pair, button untouched | on | 4 | `2026-01-09 to 2026-01-12, 4 days` |
| button pressed off | off | 16 | `2026-01-05 to 2026-01-20, 16 days` |

The row that mattered most is the sixth: a second range with the button never touched, which is the whole point of it staying on.

**Nothing in the suite pins this.** The probes exercise the calendar to get a range, so they would notice it breaking altogether, but no check asserts the marking rules or the bar. `dev/CHECKLIST.md` carries them, and a person runs that.
