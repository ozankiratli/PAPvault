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

## 2026-09-23: a break of up to an hour does not cross the boundary

**Appended 2026-09-23, against the tree at `0957202`.** The note above is left as it was written.

Z found the defect by describing a night rather than reading the code:

> I found a defect in my design. If someone uses the bathroom for a few mins and come back after 6am, the system records it in the next day. Even though it should be in the same day. We should make a rule or something allowing up to an hour break in the use. But with 12pm cutoff any session that starts after 12pm regardless of the cutoff times belong to that day.

The defect is real and it was in the page from the first day it drew anything. A session is one unbroken stretch of flow, and a cut of more than five seconds begins a new one, so five minutes off the mask is always two sessions. Every session was dated on its own start. Off at 05:55 and back on at 06:05 therefore split one night down the middle: the first half on the night's date, the second on the next, each with its own hours, its own event counts and its own row in a range. Nothing about the sleep was different; the clock had crossed 6 while the mask was off.

**The rule, as it is now in `src/card.js`:** a session that begins within `DAY_BREAK_MINUTES` of the end of the one before it takes that session's day instead of the day the boundary would give it. The break is measured from the end of the previous session -- its flow end, or its files' span where it has no flow -- to the start of the next, which is the same measure `sessionsFrom()` already used to decide where one session ends and the next begins, and both now read it from `endOf()`.

**It carries on down a chain.** The third session of a broken morning reads the day the second was *given*, not the day its own clock would give it. That is what makes the noon limit necessary rather than decorative, and it is the part a check has to aim at specifically: replacing `before.day` with `cpapDayOf(before.start)` leaves a rule that still works for one break and fails for two.

**The limit Z set is `DAY_BREAK_BEFORE_HOUR`,** and it is a floor under the chain rather than a second boundary. A session beginning at noon or later is its own day's whatever came before it, so no run of short breaks can walk a morning into an afternoon and file a nap under the night before. Everything before noon is unchanged by it, because before noon the chain is what decides.

Two readings of Z's words that would have produced different code, decided here and stated to Z rather than asked:

- **The chain is unlimited, not one hop.** Z wrote *"up to an hour break in the use"*, and the use is what continues across it. A one-hop rule would also make the noon limit almost unreachable, which is an argument that Z was describing something that can reach noon.
- **Noon is `>=`, not `>`.** A session beginning at 12:00:00 exactly starts its own day. The other reading differs for one second of the day.

## What this changed, and what it did not

**Nothing else in the page.** Membership is carried entirely by `session.dayKey`: the calendar's dots, `sessionsInSelection()`, the per-day figures and the plots all read it, so setting it differently was the whole change. `cpapDayOf()` is untouched and still answers for a moment on its own, which is what the preselected day and `cpapDayStart()` need.

**No synthetic card.** Every case this repository holds starts its sessions in the evening or between midnight and 6, so none of them has a break that crosses the cut and no `answer.json` moved -- the generator wrote identical bytes before and after. That is the same gap the note above recorded for the boundary itself, and it is recorded again here: **the break rule is checked by `dev/tests/day-boundary.js` and by nothing that comes off a card.** A case is proposed in `dev/synthetic/resmed-cases.md` as `bathroom-break`, not built, because a case is agreed with Z before it is written. Building it also means the rule goes into `dev/synthetic/resmed.py`, whose `cpap_day()` is today a function of one moment and would have to become a function of the sessions in order.

**The R prototype does not have this rule.** `prepare_data()` is the ground truth for reading a card, and the day rule has never come from it; Z set the days in `CLAUDE.md` and set this. A comparison against the prototype on a card with a break across 6 would disagree, and the disagreement would be the prototype's.

## How the checks were shown to be able to fail

`dev/tests/day-boundary.js` grew fifteen nights and a sixteenth session with no flow, driven through the exported `daysOf()`. Three deliberate breaks, each run against a copy of `src/` in a scratch directory:

| The break | What failed |
|---|---|
| `DAY_BREAK_MINUTES` 60 -> 0 | 9 of 33, and every one of the nights the rule must leave alone still passed |
| `DAY_BREAK_BEFORE_HOUR` 12 -> 24 | 2 of 33, both of them the noon cases and nothing else |
| `before.day` -> `cpapDayOf(before.start)` | 9 of 33, including the three-session chain, which is the check that tells a chain from one hop |

The second is the one worth keeping in mind: it fails exactly two checks, so if either of those two nights is ever dropped the noon limit becomes unprotected without any other check noticing.
