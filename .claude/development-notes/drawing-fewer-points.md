# Drawing fewer points

**Written 2026-09-24, against the tree at `d9d9bfd`,** with everything described here uncommitted.

A night of flow is a sample every 40 milliseconds: about 720,000 points for eight hours, on a chart a thousand pixels wide. Every one of them was being drawn. That is the cost behind the trackpad gesture Z spent a session finding unusable, and behind the wait when a night opens.

## The attempt that broke everything, 2026-09-23

The first attempt thinned the data **to the visible window** and handed uPlot the slice. It broke zooming, and Z stopped it: *"OK select zoom is broken. It is hard to explain. I think it zooms in but only the area I selected is displayed on flow. Some plots disappear. I feel like again fixing one thing, everything is broken."* It was reverted the same day.

The diagnosis, written down at the time and acted on here: **the data followed the scale.** Once a chart holds only what is on screen, there is nothing to zoom back out to, and every uPlot mechanism that reads the series to work out a range is reading a window instead. The agent's own summary of what to do instead was *"Never slice. Always give uPlot the whole series -- just a smaller version of it."*

## What was built

**A pyramid, per chart, built once when the stack is drawn.** Level 0 is the samples. Each further level takes a run of samples -- 8, then 64, then 512 -- and emits two points for it, the lowest and the highest in the run, placed at the run's first and last moment. Two points per run, so a step of 8 draws a quarter of the samples and a step of 512 a 256th, and the line drawn from them covers the same ground as the samples it stands for.

**Every level covers the whole period.** That is the entire difference from the attempt that failed. Handing over a level never changes what the chart holds, only how finely it is described, so the scale the reader chose is untouched and the chart can always be zoomed back out.

**The level follows the window.** On a scale change, the coarsest level whose points across the window still come to about two per pixel. Zooming in therefore brings a finer level in, and zooming out lets a coarser one take over.

**Only charts that need it get one.** Below 20,000 samples nothing is reduced. On a ResMed card that means flow and its mask pressure are reduced and every `PLD` signal, at a sample every two seconds, is drawn whole -- 14,400 points for a night, which was never the problem.

**Three details that are not free choices.** `setData(data, false)` does not draw at all, so the swap is followed by `redraw()` with no argument, which is the sequence that works (`platform-traps.md`). The swap runs in a microtask rather than inside the `setScale` hook that asked for it, because it is a commit inside a commit otherwise. And the redraw fires `setScale` again, which asks for the same level and stops, so it does not loop.

## What it measured

On the `plain-night` card, a whole night on screen:

| | points drawn for flow |
|---|---|
| before | 720,000 |
| after | 2,814 |

**The picture is the same to 0.022%.** The day stack was rendered twice at 1500x2400, once with the reduction and once with it disabled, and the two screenshots differ in **802 pixels out of 3,600,000** -- the antialiased edge of the envelope. Both pages were confirmed to have actually rendered before the comparison, which is the trap that made an earlier version of this measurement worthless: a comparison against a reference that was never drawn agrees with everything.

**This is not yet a report from Z that it feels better.** It is a point count and a pixel count. Whether the gesture is usable is Z's judgement on Z's hardware, and the reason that matters is written up in the agent's memory as its own rule.

## What guards it

`dev/tests/page/make-pyramid-probe.py`, nine checks. It opens a night, reports each chart's point count and level, drags a selection across the flow chart, and reports both again. Two of its checks exist only to catch the 2026-09-23 failure returning: after a zoom the series must still reach from the start of the night to the end of it, and must cover far more than the window on screen. Reintroducing the slice makes both fail, with the series covering 10,086 seconds against a window of 10,088.
