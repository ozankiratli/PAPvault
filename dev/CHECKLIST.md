# Checklist

**Run before each release, on a real card, after `dev/tests/run.sh` has passed.** Everything a machine can answer has been moved into that suite; what is left here needs eyes, or a card no check in this repository has ever seen. Write what was checked into `VERIFICATION.md`.

Entries are named so a record can point at one and keep pointing at it.

1. **`oximetry-off`** -- Oximetry is not among the plots offered for a day. The suite checks this too; it stays here because a checkbox that appears is a thing you see before any check runs.

2. **`card-read`** -- open a real card. What the folder box reports -- files, nights, sessions, the first and last recording -- matches the card. Any file it refused is named, with why.

3. **`sessions`** -- on a night you slept through, the session count matches the `_EVE.edf` files in that night's folder, and the hours match what the machine says.

4. **`day-break`** -- on a night where the mask came off and went back on within the hour after 6 in the morning, the whole night is on one day, not two.

5. **`event-timing`** -- zoom into one apnea of ten seconds or more. The shading sits over the flow that stopped, not after it.

6. **`flow-detail`** -- zoom from the whole night down to a few seconds of flow. Individual breaths appear; the line does not stay a smooth summary of itself.

7. **`sample-card`** -- build `realistic` and read it as a stranger would. It looks like therapy: flow stops under an apnea, pressure answers an obstructive one and not a central one, and the nights differ from each other.

8. **`manual-truth`** -- read every section of the Manual against the page as it stands. Anything it claims that is no longer true is a release blocker.

9. **`drag-and-drop`** -- drag a card's folder onto the box instead of using the button. It reads the same way. No check covers this route.

10. **`looks-right`** -- in both themes, on a wide window and on a phone: the plots, the calendar, the manual and the top bar read well. Colors, spacing and wrapping are yours to judge; the suite only measures that they are legible and where they should be.

11. **`feels-right`** -- on a phone, pinch, drag and tap the plots; on a trackpad, swipe and pinch. Nothing here is a measurement: the suite proves the arithmetic, and only a hand says whether the rate is right.

**After the release is published**, `dev/RELEASING.md` step 10 runs the one check that needs a live site.

Why the division falls where it does, and what each of these used to be, is in `.claude/development-notes/what-a-person-checks.md`.
