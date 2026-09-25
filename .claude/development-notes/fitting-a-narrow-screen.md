# Fitting a narrow screen

**Written 2026-09-24, against the tree at `7e8ad1d`,** with everything described here uncommitted.

## The ladder

The page had two widths in it: three columns from 1200 pixels, and a `narrow` class below 650 that moved the calendar into a dialog and collapsed the manual's navigation. Z took it apart over one session, a step at a time, each step named by Z at a width Z had measured on the running page.

| width | what changes |
|---|---|
| 1500 and up | three columns: summary, plots, calendar |
| 1200 to 1500 | two columns, and the calendar moves to the top bar's dialog |
| below 1200 | the two cards stack |
| below 850 | the selected day or range takes a row of its own in the top bar |
| below 650 | the manual dialog's navigation stops being a column beside the text |
| below 500 | the bar's five buttons leave it for a full-screen menu |

Z, on the first of those: *"We have 3 column design. Around 1500px, we should move the calendar to the button and modal (which is already built). And switch to a 2 column design."* On the second: *"Around 850px, the date/range displayed on the top bar should move to a second line in the top bar."* On the last: *"Let's move all 5 buttons inside a hamburger menu, below 500px."*

**Two things that had been one.** The old `narrow` class did the calendar's placement and the manual's layout at the same breakpoint. Once the calendar left the page at 1500 and the manual's navigation still wanted 650, they had to be separate: `docked` says where the calendar lives, `narrow` stays what it was. They are two media queries in `src/app.js` now, and the class each sets is used by nothing else.

## The chart floor

**A chart was never told the window had changed.** The summary card's Events chart is built from its container's width and handed back a `resize`, and nothing called it -- the window listener knew the day stack and the summary stack and not that one. Worse, the width it was built at floored at 240 and the width its `resize` would have used floored at 320, so the first resize after a fix would have made it 80 pixels wider than the card that holds it. A pair kept in step by hand had drifted, exactly as `CLAUDE.md` says such pairs do.

**Then Z removed the floor as a number.** Z, measuring on the page: *"I also measure around 500px where cards stop changing size, in narrow view. I think we should let them go down to 240, for some mobile viewers."* There are now no separate floors: `PLOT_LEAST` is 240 and every chart uses it.

Measured by shrinking the plots card on the running page and firing a resize, before and after:

| plot container | canvas at floor 320 | canvas at floor 240 |
|---|---|---|
| 378 | 378 | 378 |
| 318 | 320 | 318 |
| 258 | 320 | 258 |
| 240 | 320 | 240 |
| 198 | 320 | 240 |

The container is the viewport less 82 pixels -- 20 of page padding and 20 of card padding on each side, plus the card's borders -- so the old floor started pushing the card out at about a 400 pixel viewport, and the new one at about 322. The overhang is invisible until it passes the card's own 20 pixels of padding.

## A slider that was not there

Z: *"The cards still not get smaller, they get pushed outside and a slider at the bottom shows up. Is it about the top bar?"*

It was not the top bar. With the whole application squeezed to 240 pixels the bar fits inside it: the name measures 169 and the button row 200, and the two wrap onto separate lines. What stuck out was the charts -- `#plots-body` with 158 pixels of room and a 240 pixel canvas in it.

And at real viewports the slider was already gone. Measured at 480, 400, 360 and 320: the page is the viewport less the 15 pixel scrollbar every time, nothing overflowing, ten charts drawn. Z found the answer on their own side: *"You know what, yes I'm wrong. I opened with ctrl+shift+m It loads fine."*

**The part worth keeping is why it took a new instrument to say so.** Headless Chromium will not give a window narrower than 500 css pixels, so every measurement below that width had been impossible and the question could not be settled by looking. That trap is in `platform-traps.md`, with what gets round it.

## The menu

Z asked for the five buttons to go into a hamburger below 500, then, seeing it: *"Menu can open full screen with animation and can have an x button at the right."*

It is the same five buttons, not a copy of them: `.topbar-actions` becomes a fixed, full-screen panel, so every click handler already wired to those buttons keeps working and there is no second list to keep in step. The words beside each icon are the tooltip's, through `content: attr(aria-label)`, so a button that gains or changes a label cannot end up with two names. It fades and slides in over 0.18 seconds, and a `prefers-reduced-motion` rule drops that.

The background went through three values in front of Z: half transparent, then *"Give some alpha 0.5 to the menu background"* honored exactly, then Z asking for a 2 pixel blur back that the agent had added uninvited and removed -- *"did you take blur back. I think it was great"* -- and then 60 and 70 percent. It sits at 70 with the blur.

**One bug, and it is a reminder that specificity is not the only rule.** The hamburger showed at every width. `.topbar-menu { display: none }` had been written directly under `.topbar-actions`, which is above `.icon-button` in the file; both selectors carry the same weight, so the later one won and the button kept `inline-flex`. Reading the rule said it was hidden. Asking the page said `display: flex` at 700 pixels wide. It is now below `.icon-button`, and its comment says why it has to be.

## How to check any of this

The ladder is `grep -n "min-width\|max-width" src/style.css`, and the widths above are the numbers it prints.

The behavior needs a real viewport, which the browser's own responsive mode gives -- in Firefox and in Chromium, ctrl+shift+m. What to look for at each width is in `dev/CHECKLIST.md`, under `narrow-calendar` and `narrow-menu`.
