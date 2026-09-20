# The prototype's interface, as PAPvault takes it up

**Written 2026-09-19, against the tree at `e4fad7e`.** uPlot had just been vendored and nothing could draw yet. This is the read cleared as `R-018` in `dev/READING-LOG.md`, written down so the plots are built from a file rather than from the prototype, as `CLAUDE.md` requires. It quotes no code. `CPAP_old/app.R` was read at SHA-256 `3916cc6a...`, `CPAP_old/plotting.R` at `86bb4990...`.

Z, 2026-09-19: *"We will use uPlot and the template I created in CPAP_old folder."* and *"For color palette, use the one I used in the old project."* So unlike a read of another project, this one takes the design and not only the facts: it is Z's own work, and Z asked for it to be carried over.

## The template

A title, then a sidebar beside a main panel.

**The sidebar** picks a folder, confirms it, shows the path it settled on, and offers a dropdown of dates. Only once a date is chosen does a checkbox group appear, listing which plots to show: Pressure, Leak Rate, Respiratory Rate, Flow Limitation, Snore, Tidal Volume and Minute Ventilation, with the first three checked to begin with.

**The main panel** is a tab set of four: Visualizations, Summary Statistics, Raw Data, Help. Visualizations stacks one plot per checked signal, each 250 pixels high, in the order of the checkbox list, inside a container whose single stylesheet rule removes the gap under each plot so the stack lines up. Summary Statistics prints text. Raw Data shows two tables. Help lists the four steps.

**What PAPvault keeps:** the stack of aligned plots on one time axis, the seven plots and what each holds, the reader choosing which to show, and the order. What Z has already changed: the folder and the date move into the top bar and the calendar card, a range of days is selectable where the prototype had one folder, and a cursor line follows the mouse across every plot at once, which the prototype does not have.

## The plots

Seven, each a line against time, only the bottom one labeling its x-axis. Hovering shows the nearest point on that plot alone.

| Plot | What it draws | Its y-axis |
|---|---|---|
| Pressure | three lines together: mask pressure, pressure, EPR pressure | Pressure (cmH2O) |
| Leak Rate | leak | Leak (L/min) |
| Respiratory Rate | respiration rate | Breaths per minute |
| Flow Limitation | flow limitation | Flow Limitation |
| Snore | snore | Snore Index |
| Tidal Volume | tidal volume | Volume (L) |
| Minute Ventilation | minute ventilation | Ventilation (L/min) |

Every one of these comes from the `PLD` file, sampled every two seconds. The prototype draws nothing from `BRP`, the 25-a-second flow and pressure, and nothing from `SAD`, the oximetry, although `prepare_data()` reads both (`ground-truth.md`). Whether PAPvault adds a flow plot and an oximetry plot is Z's to say; the prototype does not answer it.

## The palette

The colors are written as names, not as values, and the two files hand those names to different renderers. **This matters, because the same name is not the same color in both.** `app.R` gives its names to plotly, which resolves them as CSS colors in a browser, so those are the colors Z actually saw. `plotting.R` gives its names to ggplot2, which resolves them from R's own palette; nothing sources that file, so it never ran.

Both were resolved rather than recalled: `Rscript -e 'col2rgb(...)'` for R's palette, and a browser reading back `getComputedStyle` for CSS, with each element given a sentinel color first so that a name the browser rejects shows up as the sentinel instead of as a plausible wrong answer.

**What Z saw, from `app.R` through plotly, as CSS colors:**

| Plot | Series | Written as | Is |
|---|---|---|---|
| Pressure | mask pressure | `blue` | `#0000FF` |
| Pressure | pressure | `lightblue` | `#ADD8E6` |
| Pressure | EPR pressure | `darkblue` | `#00008B` |
| Leak Rate | leak | `red` | `#FF0000` |
| Respiratory Rate | respiration rate | `green` | `#008000` |
| Flow Limitation | flow limitation | `orange` | `#FFA500` |
| Snore | snore | `brown` | `#A52A2A` |
| Tidal Volume | tidal volume | `purple` | `#800080` |
| Minute Ventilation | minute ventilation | `blue` | `#0000FF` |

**Where R's palette differs,** for the names `plotting.R` uses: `green` is `#00FF00` in R against `#008000` in CSS, `purple` is `#A020F0` against `#800080`, and `green4`, which `plotting.R` uses for respiratory rate and usage, **is not a CSS color at all** -- the browser rejected it and left the sentinel. `blue`, `lightblue`, `darkblue`, `red`, `orange` and `brown` are the same in both.

So the palette PAPvault carries over is the CSS column above, since that is the one Z looked at. `green4` is not carried: it never rendered, and it has no web spelling.

Two things to notice in it. Minute ventilation reuses `blue`, the same as mask pressure; they never share a plot, so nothing collides. And there is no color for events, because the prototype draws no event plot; `plotting.R` has one in `orange`, which flow limitation already uses on screen.

**Added 2026-09-20.** Flow had no color in the prototype, which draws no flow plot. Z set it after seeing one: *"let's make Flow Dark gray for light background and light gray for dark background"*. So flow is the one plot whose color is neither the prototype's nor the agent's.

## The palette against a dark background

The prototype had one background, white. PAPvault has two. Measured against `--surface` in each theme, as a ratio:

| Series | Hex | On `#ffffff` | On `#181d26` |
|---|---|---|---|
| mask pressure, minute ventilation | `#0000FF` | 8.59 | **1.97** |
| pressure | `#ADD8E6` | **1.53** | 11.06 |
| EPR pressure | `#00008B` | 15.30 | **1.10** |
| leak | `#FF0000` | 4.00 | 4.23 |
| respiratory rate | `#008000` | 5.14 | 3.29 |
| flow limitation | `#FFA500` | **1.97** | 8.56 |
| snore | `#A52A2A` | 7.08 | **2.39** |
| tidal volume | `#800080` | 9.42 | **1.79** |

Five of the eight fall below 3 against the dark surface and two fall below it against the white one, so no single set of values works in both themes. The hues are Z's and are kept; each gets a value per theme, written as custom properties in one block per theme in `src/style.css`, so restoring Z's exact values everywhere is an edit to one block. The `contrast` entry in `dev/CHECKLIST.md` is what checks the result.

## The summary figures

The prototype computes these, and they are worth recording because Z named a different set for PAPvault on the same day.

`app.R` prints, per chosen day, as text: the date, the session start and end, the duration in hours, average and maximum pressure, average and maximum leak, average respiratory rate, and a count of events by the device's own annotation text, most frequent first.

`plotting.R` computes average pressure, maximum pressure, average leak, total events and usage hours per day, and draws three: average pressure by day as a line with points, events by day as columns, and usage hours by day as columns. Nothing sources it.

**What PAPvault does instead**, as Z set it on 2026-09-19 and as `dev/synthetic/resmed-cases.md` records: hours of machine use, the number of sessions, events per hour kept apart by the device's own labels, and the median and 95th percentile of pressure and of leak. Averages and maxima give way to a median and a percentile; a count of events gives way to a rate; and the number of sessions is new, because PAPvault has sessions where the prototype had a folder.

One thing the prototype's version shows by being wrong: it computes usage hours as its row count divided by 3600, noting the assumption that a row is a second. The rows come from `PLD`, which is sampled every two seconds, so that figure would read half the real hours. PAPvault takes usage from session start and end times instead, which is what Z named, and does not count rows.

## The day's window

The prototype sets no x-axis range at all: each plot spans whatever times the chosen folder holds, and the folder comes from a dropdown. So it settles nothing about where a day begins or where a day's axis should start, which agrees with what `R-004` found. Where PAPvault's day starts is Z's separate ruling, in `the-day-boundary.md`.

## What was not taken

How the prototype divides or checks its data, its raw-data tables, and its help text.
