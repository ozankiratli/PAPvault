# Gestures on a plot

**Written 2026-09-24, against the tree at `65fe575`.**

The trackpad work was built and reverted four times before any of it stayed. This note exists because none of the reasoning is allowed to live in the source, and because the thing that finally settled it was a measurement nobody had taken.

## The constraint the browser imposes

A wheel gesture is latched to whatever scrolled first. Take some events of a gesture and leave others, and the rest of that gesture belongs to the page whatever the page does later. So **which of the page and the plot owns a gesture has to be settled on its first event and cannot be revised.**

Every earlier attempt decided per event, by the direction of that event, and that is what handed whole gestures to the page. Z stopped it on 2026-09-23 and it was removed the same day, before it was ever committed.

## What a trackpad actually sends

Measured on Z's machine on 2026-09-24 with a throwaway page that drew nothing, after an earlier instrument was killed for lagging the way the thing it measured lagged. These are one machine's numbers.

| gesture | total | events | per event | first events |
|---|---|---|---|---|
| swipe sideways | 1354.9 dX, dY exactly 0.0 | 31 | 43.7 | `+28.1` straight away |
| swipe up and down | 404.1 dY, dX exactly 0.0 | 73 | 5.5 | `-14.1` straight away |
| pinch | 172.9 dY, dX 0.0 | 231 | 0.75 | six of `-0.1` |
| ctrl and two fingers | 404.1 dY | 73 | 5.5 | `-14.1` straight away |

Three things came out of that table, and all three are load-bearing.

**The axes are cleanly separated**, exactly 0.0 on the one not being used, so deciding an owner from the first event is sound here. There is no ratio to tune.

**The plus or minus 0.1 at the start belongs to the pinch, not to the swipe.** That is why a pinch cannot have its direction read from its first event and a swipe can. It is also the whole of an old complaint of Z's -- *"when I pinch my fingers together to zoom out slowly, the graph initially zooms in then starts zooming out"* -- because under the rule of the time those six events alone came to `0.8^6`, a 3.8x zoom in before the fingers had moved.

**A pinch and a two-finger scroll are the same event with steps seven times apart.** Z, on 2026-09-24: *"On the other hand ctrl+two finger up down (scroll) provides perfect control."* Both arrive as a wheel with ctrlKey set, through one handler. One rate served the scroll at 42x a gesture and the pinch at 4.9x, which is why a pinch could not cross the range. They now have their own rates, chosen so a full pinch zooms as far as the scroll Z called perfect.

## What the page does with them

- **The owner is settled once**, on the first event of a gesture carrying any movement, and held until a gap of `GESTURE_GAP` with no wheel event ends it.
- **Sideways takes the plot only when there is somewhere to slide to.** With the whole period on screen the gesture is the page's, so a reader is never swiping at a chart that cannot move.
- **Distances are added up and spent once a frame.** Events arrive around 140 a second and nothing throttles them; a stack of charts cannot be redrawn that often, so without this the queue grows and never drains. Z's words for it: *"It works fine for a second. Then it starts suffering."* The first event of a gesture is spent where it lands, so a gesture still answers the moment it starts.
- **Zooming follows the distance travelled, not the number of events.** Factors multiply, so adding the distances and raising two to the total once is the same answer as taking each event in turn. Under the old rule one of Z's pinches left the window `1.18e-18` seconds wide, which is what Z saw as *"looking at a horizontal line"*.
- **Which rate applies is settled on the first step over `ZOOM_TRACE`**: under `PINCH_STEP` it is a pinch, over it a wheel notch or a scroll.

The numbers are `GESTURE_GAP` 200, `PINCH_TRAVEL` 32, `WHEEL_TRAVEL` 75, `PINCH_STEP` 3, `ZOOM_TRACE` 0.5, all in `src/plots.js`. Every one of them is a number judged by feel on hardware the agent does not have, and Z set the last of them by trying it.

## Open: a gesture that lands on the page

Z, 2026-09-24, asking for it to be recorded rather than chased:

> Sometimes, pinch and finger moves apply to page first and plot second, sometimes mid-way, they stop applying to plot and for a split second they apply to the page. I believe the root cause is the same.

Three candidates, none of them measured. They are not exclusive.

1. **The first event decides, and the first event may not be representative.** A swipe on Z's machine opens at full size, so this looks unlikely there -- but that is two gestures of one trackpad, and a first event whose two axes are close in size would hand the whole gesture to the page.
2. **A pinch whose first event does not carry `ctrlKey`.** It would then be read as a swipe, the axis decision would run on it, and the gesture would be latched before the browser said it was a pinch. Nothing has measured whether this happens.
3. **One movement split into two gestures.** A gesture ends after `GESTURE_GAP` with no wheel event, and the decision is then taken again part way through one physical movement. This matches *"mid-way, they stop applying to plot"* most closely, and there is a coupling worth suspecting: **the level settle and the gesture end are the same constant.** The settle fires `GESTURE_GAP` after the last event and does a `setData` across up to 180,000 points, which can block the main thread for longer than the gap it is measured against. If this is the cause, the two timers should not share a number.

**What would tell them apart.** The instrument that produced the table above already records, per gesture, the first six events and the median gap. Extend it to record per event `ctrlKey`, the gap since the event before it, and whether the page claimed it; then reproduce the annoyance and read the rows around the moment it went wrong.

- Candidate 1 shows as a first event whose two axes are close in size.
- Candidate 2 shows as a first event with `ctrlKey` false followed by events with it true.
- Candidate 3 shows as a gap over 200 milliseconds inside one continuous movement.

Until one of those rows exists, all three are guesses, and this project has spent four rounds on guesses about this hardware already.
