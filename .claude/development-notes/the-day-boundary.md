# Where one day ends and the next begins

**Written 2026-09-19, against the tree at `e4fad7e`.** The page could draw nothing yet: uPlot had just been vendored, and nothing read a file. The boundary had been at noon since the brief, and this note records the day it moved.

## What it was, and why it was not a calendar day

Z set it with the first brief, on 2026-09-18: *"A CPAP day is from 12pm to next 12pm. 06/18/21 means from 12:00pm 06/18/21 to 11:59am 06/19/21."* The words are in `product-brief.md`.

The reason is that a night crosses midnight. A calendar day cuts a single night in two and files half of it under each date, which makes every figure about that night wrong in both halves. Any cut during the waking hours avoids that, and noon is the conventional one: ResMed's own machines divide there, which is where the convention comes from even though PAPvault does not take its rules from a machine.

On 2026-09-19 Z made it apply to every machine, not only ResMed: *"The day decision is final, not just for ResMed. We will treat the days as from noon to noon."* That ruling came while Z was stopping the agent from letting OSCAR decide such things (`other-projects.md`), and its force was that PAPvault decides its own days whatever a device does. That part has not changed.

## Why it moved to 6 in the morning

Later on 2026-09-19, while the interface was being planned, Z described what a selected day should show: *"When a day is selected, it will show the machine use that starts between noon of that day and 6am of the next day, end of the sleep event might differ."*

The agent asked whether 6 was the plot's window or the day's membership. Z: *"Noon to noon gets a small change. If a session starts before 6am and ends at 2pm or even later on that day, it is still shown fully."*

That left one case undecided, and it is the whole of the change: a session starting between 6 in the morning and noon. Under noon to noon it belonged to the day before. Under the window as Z first described it -- starts between noon and 6 -- it belonged to no day at all, which would have hidden recorded use. The agent put the three ways out to Z with the consequences of each, including that "noon to noon" would stop being true in the manual, the calendar and `CLAUDE.md`. Z chose to move the cut:

**A CPAP day runs from 6:00 on its date to 6:00 on the next calendar day.**

So a morning nap belongs to the morning it happened on, rather than to the night before. What did not change: a session belongs whole to the day it began in, and its samples and events go with it however late it ends. A session that starts at 5 in the morning and ends at 2 in the afternoon is one session, in the day before, shown entire.

## What the change touched

The boundary was stated in nine places, found with `git grep -nEi 'noon|12:00|getHours\(\) < 12'`. Two things now derive it from one name rather than repeating the number: `DAY_START_HOUR` in `src/app.js`, which both `cpapDayOf()` and `cpapDayStart()` read, and `DAY_START_HOUR` in `dev/synthetic/resmed.py`.

The rest were prose: `CLAUDE.md` twice, the calendar's hint in `src/index.html`, `docs/manual.md`, `formats/resmed.md`, the `calendar-select` entry in `dev/CHECKLIST.md`, and the `crosses-noon` case in `dev/synthetic/resmed-cases.md`, which became `crosses-the-cut`.

`CLAUDE.md`'s house-style rule kept Z's attribution but lost its example. It had read *words over notation where both work, so "noon to noon", not "12:00 to 12:00"*, and the example was the day boundary. The rule is about prose, not about days, so the example was replaced and the note about where it came from kept beside it.

The notes written before today still say noon, and they are not corrected: `product-brief.md` and `page-layout.md` describe the tree as it stood when they were written, which is what a dated note is for.

## What is checked, and what is not

**The page.** Headless Chromium with the clock pinned and `TZ=America/New_York`, reading the selection label:

| The moment the page opens | The day it preselects |
|---|---|
| 05:59 on 2026-09-19 | `2026-09-18 6:00 AM to 2026-09-19 6:00 AM` |
| 06:00 on 2026-09-19 | `2026-09-19 6:00 AM to 2026-09-20 6:00 AM` |
| 11:00 on 2026-09-19 | `2026-09-19 6:00 AM to 2026-09-20 6:00 AM` |
| 13:00 on 2026-09-19 | `2026-09-19 6:00 AM to 2026-09-20 6:00 AM` |

The 11:00 row is the one that can fail: under the old rule it would have read `2026-09-18`. A range from 2026-11-01 to 2026-11-04, over the Sunday daylight saving time ends, still counted 4 days with 2 shaded and 2 ends, so the 25-hour night is still one day.

**The synthetic data, and this is the gap.** Regenerating both cards after the change produced the same bytes, and the same aggregate checksum as before it: `diff -r` over the two cards reported nothing. That is the right answer, because every session in them starts either in the evening or between midnight and 6, and both rules put those in the same day. It also means **nothing in the synthetic data would fail if the cut moved back to noon.** The case that would tell the two rules apart is one session starting between 6 and noon. It is proposed in `dev/synthetic/resmed-cases.md` as `morning-nap` and waits for Z; until it exists, the boundary is checked only through the page's calendar and not through a card.

## What the reader gets from this

The first framing -- "show the use that starts between noon and 6" -- was a rule about display that quietly implied a rule about membership, and the two came apart on one case out of the whole day. Writing the case down as data, rather than settling it in prose, is what showed that some recorded use would have had nowhere to appear. The same question is worth asking of any window the page draws: which recording falls outside it, and where does that recording go.
