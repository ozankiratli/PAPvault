# The product brief

**Written 2026-09-18, against the tree at `4db9efc`.** Nothing had been built. This is the brief as Z first gave it, and what was settled about it later the same day.

Z, 2026-09-18: *"This is going to be a single page view modern design website with dark mode. It will be built as github pages. Top right corner should have a calendar to pick the date or date range to select. Same goes for time range select. Time range selection should be allowed only for a day. When a range is selected it will display summary data. We will not make any conclusions beyond what the PAP machine declares. Again it is a matter of principle. It will just display the data."*

## What it fixes

- One page, in a modern design, with a dark mode.
- Served from GitHub Pages: static files, and no server of PAPvault's own. Whatever a visitor sees is computed in their browser, which is also what the promise in `CLAUDE.md` requires.
- A calendar in the top right corner selects a single date or a range of dates.
- A time range can be selected too, but only within a single day.
- A range of dates shows summary data.
- It displays and does not conclude. The rule is in `CLAUDE.md`, under *It displays; it does not conclude*.

## What a day is

Z: *"A CPAP day is from 12pm to next 12pm. 06/18/21 means from 12:00pm 06/18/21 to 11:59am 06/19/21."*

So a day in PAPvault is the device's day, noon to noon, under the date on which it starts. A night falls inside one day, and a time range selected within a day can cross midnight: 21:00 to 08:00 on the day dated the 18th is one selection.

## Summaries

A summary figure the device declares itself is shown next to the same figure recomputed from the session files, for as long as development lasts. Z: *"Let's have both side by side during development, my experience was they matched but we will see."* Why that is a useful check, and which file the declared figures come from, is in `ground-truth.md`.

## The stack

Z: *"The stack is HTML, CSS, and JavaScript. However, we should be careful with JS. It should be completely open source. We also need to work on the security. I mean JS injection attacks would be terrible. We might also offer the users a static page that they can use on their machines offline. I like the taxtriage html where you can display results. Needs a build, but it's not too hard."*

The TaxTriage report ([github.com/jhuapl-bio/taxtriage](https://github.com/jhuapl-bio/taxtriage)) is a single self-contained HTML file that opens offline in a browser, with its interactivity computed in the page. That is the shape the offline page would take.

## What GitHub Pages brings with it

GitHub's documentation, read on 2026-09-18 (*About GitHub Pages*, under "Data collection"): *"When a GitHub Pages site is visited, the visitor's IP address is logged and stored for security purposes, regardless of whether the visitor has signed into GitHub or not."*

So PAPvault's own code can collect nothing and the host still records that a visit happened. The page cannot change that. What it can do is describe itself accurately: PAPvault collects nothing itself, and its host logs visits.

Z asked whether another host would be better. The agent's answer was that every host sees the request for the page, so changing hosts changes whose logs and not whether there are logs. GitHub Pages also serves the repository as it is, so every deployed version traces to a public commit. Its real cost is that it cannot set response headers, which `security.md` deals with. Z: *"That's why I thought GitHub pages was the right call. It stays."*
