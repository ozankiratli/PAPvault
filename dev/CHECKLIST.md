# Checklist

**Z runs this list before each release.** Each entry says what to check, how, and what a failure looks like; a check with no stated failure is not a check. The agent proposes an entry with the change that adds the behavior it protects, and the entry joins the list when Z commits it. What a run of the list found is written in `VERIFICATION.md`, in Z's words.

Entries are named, not numbered, so a record can point at one and keep pointing at it.

## `headers` -- what GitHub Pages sends

**Protects:** the design assumption that the page arrives with no security header of its own, so the `<meta>` policy is the one in force.

**How:** `curl -sSI <PAPvault URL>`, and compare with the headers recorded at the previous run.

**Failure:** `content-type` is anything but `text/html; charset=utf-8`. A header that was not there at the previous run is recorded and raised, whether or not it looks harmful.

## `policy-blocks` -- the policy is in force

**Protects:** the promise that nothing leaves the page.

**How:** open the deployed page, and in the browser console run `fetch('https://example.com')`.

**Failure:** the request goes out, or fails for any reason other than a Content-Security-Policy violation reported in the console.

## `no-outbound` -- nothing leaves the page

**Protects:** the promise that nothing leaves the page, and that the site collects nothing.

**How:** open the deployed page in a fresh private window with the developer tools' network panel open, reload, and use every control on the page.

**Failure:** any request other than the page itself, apart from a link the tester follows on purpose.

## `framed` -- the page refuses to run inside a frame

**Protects:** the one gap a `<meta>` policy leaves, since it cannot forbid framing.

**How:** save `<iframe src="<PAPvault URL>" width="900" height="300"></iframe>` as a local HTML file and open it.

**Failure:** anything of PAPvault's interface appears in the frame, rather than the notice that it does not run inside one.

## `no-markup` -- nothing from a file becomes markup or code

**Protects:** the rule that text read from a file reaches the page only as text.

**How:** `grep -rnE 'innerHTML|outerHTML|insertAdjacentHTML|document\.write|\beval\(|new Function' src`

**Failure:** any line printed.

## `rebuild` -- the served file is the one the source builds

**Protects:** the claim that anyone can rebuild the page and get the file that is served.

**How:** in a clean checkout of the release commit, run `python3 build.py` twice, then `curl -sS <PAPvault URL> | sha256sum`.

**Failure:** the two builds print different checksums, or the served file's checksum differs from the build's.

## `calendar-select` -- the calendar selects the days it says

**Protects:** that the period the summary describes is the period that was chosen, with a day running noon to noon.

**How:** open the page and note the preselected day and the time; click a day other than the preselected one; click a later day in the same month; click once more; then go back a month and click a day there; then select a range that contains the Sunday in early November when daylight saving time ends. Open the month picker from the month name, step back a year, and choose a month.

**Failure:** the preselected day is not the CPAP day containing the current time, so before noon it is not yesterday's date, and from noon it is not today's; the first click selects a range rather than that one day at 12:00 to the next day at 12:00; after the second click, the shaded days, the two ends or the day count disagree with the days clicked; the third click does not start over; the range picked in reverse across the month boundary is wrong; the range across the time change shows a day count that is not a whole number or is off by one; or the month picker does not move the calendar to the month chosen.

## `time-format` -- times follow the reader's choice

**Protects:** that every time on the page is shown the way the reader chose, and that the choice lasts.

**How:** in a fresh private window, open the page and note the time format it starts in; open Settings and switch to the other format; reload.

**Failure:** the page does not start in the format the browser's language uses, 12-hour for United States English and 24-hour for most others; after switching, any time on the page is still in the old format; or after the reload the choice is lost. A private window that blocks storage may lose it on reload, which is not a failure.

## `narrow-calendar` -- the calendar is reachable on a narrow screen

**Protects:** that below 650 pixels wide the calendar moves into a dialog rather than disappearing, and keeps its selection.

**How:** select a range on a wide window; narrow the window below 650 pixels; open Calendar from the top bar; widen the window again.

**Failure:** below 650 pixels the Calendar button is missing or the calendar still shows in the card; the dialog's calendar does not show the range selected before; or after widening, the calendar is not back in the card.
