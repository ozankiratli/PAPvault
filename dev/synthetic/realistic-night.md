# What a realistic night is made of

**Written 2026-09-22.** This file is to the sample card what `dev/formats/resmed.md` is to the other cases: the only input the generator is written from, besides the case description. Every fact here cites the reading-log entry it came from. **Z reviews this file before any code is written**, which is step 3 of *How synthetic data is made* in `CLAUDE.md`.

**Why it exists.** Z, 2026-09-22, on what the card is for: *"Provide a test data for potential users to test the website before using it. They will be able to download it and use it on the website to test it."* Every other synthetic case is deliberately unrealistic, on Z's instruction of 2026-09-19 that generated data need not look real, because Z tests realism against a real card. A card that strangers download is a different thing: it is published, so what it shows has to be defensible, and the only alternative to a source is the agent's recollection, which `CLAUDE.md` forbids for what a device value means.

**Two kinds of statement, and they are marked apart.**

- **Sourced.** A fact with a citation to `dev/READING-LOG.md`. It is what a document says.
- **The generator's choice.** A number no source gives, picked so the card can be built. `CLAUDE.md` already requires these to be marked: *"A value no source gives, such as a calibration range, is marked as the generator's choice. A reader must not depend on it."* Nothing in PAPvault may be built to expect one.

## How the night is built, and why in that order

The night is a **script** first: a timeline of what happened and when -- normal breathing, an apnea of eighteen seconds at 23:14:02, a stretch of flow limitation, a mask that shifts and leaks for four minutes, a period of Cheyne-Stokes respiration. Every signal is then a rendering of that one script, and `answer.json` is written from the script rather than from the samples.

That ordering is what lets a card be realistic and still carry an answer known by construction. It also makes the events agree with the signals beneath them, which no case has today: open any current case and the flow under an apnea annotation is a sine wave.

## The machine (R-022)

From ResMed's *Clinical guide* for the AirSense 10 AutoSet, AutoSet for Her, Elite and CPAP, document `378519/6 2020-10`.

| Fact | What the guide says |
|---|---|
| What moves the pressure | AutoSet "adjusts treatment pressure as a function of three parameters: inspiratory flow limitation, snore, and apnoea", breath by breath |
| After an obstructive apnea | the device "will respond by increasing pressure" |
| After a central apnea | the airway is open and there is no flow, and the device responds "by not increasing pressure" |
| EPR | lowers the delivered mask pressure **on exhalation only**, at `1`, `2` or `3 cm H2O`, `Full Time` or `Ramp Only` |
| The floor | with EPR on, "the delivered pressure will not drop below a minimum pressure of 4 cm H2O regardless of the settings" |
| Mask pressure | displayed over `4-20 cm H2O`, resolution `0.1 cm H2O` |
| During an apnea | detection adds "small oscillations in pressure [1 cm H2O peak-to-peak at 4 Hz] ... to the current device pressure" |
| Leak | displayed range `0-120 L/min`, resolution `1 L/min` |
| Stored intervals | flow and pressure at "25 Hz - every 40 ms"; flow limitation, leak, minute ventilation, pressure and snore at "1/2 Hz (2 sec)"; pulse rate and SpO2 at "1 Hz (1 sec)"; apnea and hypopnea events, CSR and RERA "aperiodic" |

**How fast pressure rises is not in the guide.** It names `Response: Standard / Soft` and says nothing in cm H2O per minute. So the rate of rise, and how pressure decays afterwards, are **the generator's choices**.

## A breath (R-022, R-024)

- **Its shape is the device's own description, and it is qualitative:** "the inspiratory flow measured by the device as a function of time shows a typically rounded curve for each breath" (R-022). As the airway begins to collapse, "the shape of the inspiratory flow-time curve changes" -- the guide shows figures and gives no measure.
- **Tidal volume, asleep: 415 mL, SD 114** (R-024), measured in nine healthy males by calibrated respiratory inductance plethysmography.
- **The three numbers R-024 failed to find are Z's** (2026-09-22), which is where a gap goes:
  - **respiratory rate: 10 to 20 a minute** "in normal times";
  - **the ratio of inspiratory to expiratory time: 1**, so a breath's two halves are the same length;
  - **flow swings between about +/-0.25 and +/-0.5**. **Read as liters per second**, which is 15 to 30 L/min and is the reading that makes sense of the figure and of the unit the stored signals use; if that is wrong it is one word to correct and every breath in the card changes with it.
- **The derived channels are arithmetic over the flow, not signals of their own:** breaths counted give the rate, inspiratory flow integrated gives the tidal volume, and their product gives minute ventilation. Rendering them any other way would let four signals disagree with the flow they came from, which is the hardest kind of wrong to notice.

## The events

**The card's events were written by the machine, under the machine's rules, so those are the rules the generator follows** (R-022, from *Sleep Report screen parameters*):

- **an apnea** is "when the respiratory flow decreases by more than 75% for at least 10 sec";
- **a hypopnea** is "when the respiratory flow decreases to 50% for at least 10 sec".

**The AASM's rules are the general standard and are recorded for context, not followed here** (R-023): an apnea is a drop of at least 90% for at least 10 seconds, and a hypopnea a drop of at least 30% for at least 10 seconds with either a 3% desaturation or an arousal. Both are written against the PAP device's own flow signal, which the AASM names as the recommended sensor during titration -- so they are rules about exactly the signal a card carries.

**Obstructive and central cannot be told apart in the flow** (R-023). The distinction is the presence or absence of inspiratory effort, a card has no effort channel, and so the generated flow is the same for both and only the annotation differs. That is not a shortcut; showing a difference would be inventing one. R-022 says what the machine does instead: it adds a 4 Hz, 1 cm H2O oscillation to the pressure and watches how the airway answers, which is why that oscillation belongs in the pressure trace during an apnea.

**Cheyne-Stokes respiration has numbers, and they agree across both sources.** R-022: "a periodic waxing and waning of respiration. The waxing periods (hyperpneas, typically 40 seconds in length) ... while the waning periods (hypopnoeas or apnoeas, typically 20 seconds in length) cause blood oxygen desaturations." R-023: a cycle length "of at least 40 seconds (typically 45 to 90 seconds)", over episodes of at least three consecutive central events. A 60-second cycle of 40 seconds waxing and 20 seconds waning satisfies both.

**`CSR Start` and `CSR End` bracket a period of time**, which is what the device reports: "The AirSense 10 device reports the time during therapy in which it detected breathing patterns indicative of CSR" (R-022). That is why the page draws the pair as one event spanning the period rather than as two moments, which `docs/manual.md` explains to a reader.

**An arousal ends a period of rising effort** (R-022): a RERA is "periods of increasing respiratory effort which are terminated by an arousal. Increasing respiratory effort will be seen as airflow limitation." So an `Arousal` in the card follows a stretch of flow limitation rather than standing alone.

The words themselves -- `Arousal`, `Apnea`, `Central Apnea`, `Hypopnea`, `Obstructive Apnea`, `CSR Start`, `CSR End` -- are Z's, 2026-09-22, and are recorded in `dev/formats/resmed.md`.

## Leak

- Displayed range `0-120 L/min` at `1 L/min` (R-022), which is what `dev/synthetic/resmed.py` already writes for `Leak.2s` -- until now that range was the generator's choice and it now has a source.
- **The page converts liters per second to liters per minute**, by Z's decision above, and a signal already recorded in liters per minute is left alone. Which one a file holds is read from its own header, never assumed.
- **The sample card should record its leak in liters per second**, which is what ResMed's detailed-data table names (R-022) and which means the card people download exercises that conversion rather than avoiding it. The committed cases stay in liters per minute, so both paths are covered. This is a choice, not a fact: only a real card's header says what a real card holds.
- **A leak that comes and goes** is what `on-and-off-leak` already exercises, and the realistic night should leak the way a mask does: near zero, with excursions when something shifts.
- **The device declares a figure of its own about leak** -- mask seal is "Good" when "the 70th percentile leak is less than 24 L/min" (R-022). It is recorded because it is the device's, and **PAPvault does not adopt it**. The page applies no threshold to any reading and this does not give it one. The generator may use it to decide what counts as a bad night for the card's *own* purposes, and nothing about that reaches the page.

## No oximetry

**The card carries no oximetry at all: no `SAD` files, no `Pulse.1s`, no `SpO2.1s`.** Z, 2026-09-22: *"No oximeter data is needed. I told you before, we MUST treat oxymeter as an undeveloped feature."* Oximetry is off in the page until Z has a card to test it against, and a sample card that carried it would be handing people a feature that does not exist. An earlier draft of this file described how to shape a desaturation; that was the agent writing toward a feature this project has deliberately parked, and it is gone.

## What was open, and how Z settled it on 2026-09-22

1. **The numbers R-024 did not find.** Supplied by Z, above. Oximetry's two are not needed, because the card has none.
2. **The unit of the stored leak signal.** Z: *"It does not matter. We should convert our leak signal to L/min -> it is more readable. That's what people can understand. 60 x L/s simple math."* So the question stops being which unit a card holds: **the page converts a leak recorded in liters per second to liters per minute and shows it that way.** What the card holds is then read from its own header, as it always was. This is the page changing a number it displays, so it is written in `docs/manual.md`, where anything that changes what a displayed figure means belongs.
3. **`CSR Start` and `CSR End` go in `CSL`.** Z, 2026-09-22. And the page now draws the pair as **one event spanning the time between them** -- Z, the same day: *"Let's convert CSR into a single event line, where it spans the time between its start and end."* That agrees with what the device itself reports (R-022): *"the time during therapy in which it detected breathing patterns indicative of CSR"*. A period, not two moments. So the generated night writes the two marks and the page draws the one event, and `docs/manual.md` says so.
4. **The manual carries no rule.** Z: *"Manual should not carry a rule. It should say 'This is what the machine reported.'"* So the device's own definitions -- more than 75% for ten seconds, to 50% for ten seconds -- stay here, in development documentation, where they tell the generator what to draw. They do not go to a reader, because telling a reader what counted as an apnea is one step from telling them what their night meant, and the page does not take that step.
