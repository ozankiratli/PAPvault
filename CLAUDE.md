# Working on PAPvault

PAPvault is a web platform for viewing PAP therapy data (CPAP, APAP, BiPAP) interactively, where **the data never leaves the user's machine**. It revives an abandoned R/Shiny prototype, which sits untracked in `CPAP_old/`. It is a single page in HTML, CSS and JavaScript, served from GitHub Pages and possibly also offered as one file that runs offline (Z, 2026-09-18). A day is the device's day, noon to noon, under the date on which it starts.

PAPvault is also a showcase. Z calls the method **human-in-the-steering-wheel** development, as opposed to human-in-the-loop: the human drives, rather than approving what the agent drives. Z, 2026-09-18: *"I want the reviewer to look at this and say, 'yeah AI agents can be used responsibly, when developing a health related app.'"* So the record of how PAPvault is built is part of what it delivers. Write every rule, note and commit message for a reviewer who arrives skeptical and checks.

## The promise is the product

Z, 2026-09-18: *"build a web platform that people can view their data interactively without uploading their data to internet."*

Z, 2026-09-18: *"We won't have any telemetry allowed on this website, it is a trust issue, so no analytics no collection of any data."*

These are the requirements the rest of the design answers to, and they are two different things:

- **No network request the application makes may carry user data, or anything derived from it.**
- **The site collects nothing about the people who use it.** No analytics, no telemetry, no error reporting, no usage counts. The reason is trust, so "anonymized" and "aggregated" are not exceptions.

Both are invariants, and an invariant held by care is not held, so the page enforces them itself (the first point under *How to know a change works*). Until it does, **any network request the application makes is a finding to raise with Z, not a detail to settle in passing** -- a fetched font, a CDN script, a request to any host that is not the one serving the page. Even with nothing attached, a request to a third party tells it that someone is using PAPvault, and deciding whether that is acceptable is Z's call.

The page governs only what the page sends. The host is GitHub Pages, and GitHub's documentation says every visitor's IP address *"is logged and stored for security purposes"* (read 2026-09-18). The page cannot prevent that, so PAPvault is described as collecting nothing itself, never as nothing being collected at all.

## It displays; it does not conclude

Z, 2026-09-18: *"We will not make any conclusions beyond what the PAP machine declares. Again it is a matter of principle. It will just display the data."*

PAPvault shows what the device recorded and what the device itself declares, and adds no judgment of its own. However helpful it looks, that rules out a severity band or a "normal range", a good or bad color on a value, a goal line, a trend verdict, a score, and any advice. Where the device declares something -- an event, a flag, a figure of its own -- PAPvault shows it as the device's.

## Real device data never enters the agent's context

**The agent's context is not local.** Reading a file sends its contents to Anthropic's servers. A project whose whole promise is that health data stays on its owner's machine cannot be built by sending anyone's health data somewhere else, so the rule the application keeps, the development keeps too.

Real data is anything from a device's SD card or an export of one, and anything computed from it: `CPAP_old/AirSense10/`, `CPAP_old/Archive/`, and any path Z names. File names and sizes are not the problem; the contents are. The headers carry identifiers and the signals are the therapy record.

- **Never read it into the conversation.** No `Read`, `cat`, `head`, `strings` or `hexdump`, and no `grep` or script whose output prints its contents.
- **A local script over real data needs Z's go-ahead first**, and its output carries neither an identifier nor a per-night value. Signal labels, sampling rates, record counts and durations are structure; a pressure, a leak rate or an event count is the record.
- **The ground truth for reading a real card is the R prototype**, `prepare_data()` in `CPAP_old/data_prep.R` (Z, 2026-09-18). A comparison against it runs on Z's machine, and what reaches the conversation is a verdict, never a value. It reaches only the files that function reads; the rest of a card has no ground truth yet.
- **Format knowledge comes from published specifications and open-source readers**, cited, not from inspecting a real card.
- **Data for development and checking is synthetic.** A committed generator builds it, with Z's help, and nothing in it is derived from real data.
- **Nothing derived from real data goes into the repository, a development note, a commit message, a published artifact or a screenshot** unless Z has approved that item by name.
- `CPAP_old/` stays gitignored, and nothing under it is ever staged. `.gitignore` also ignores every EDF file and the folders and files of a ResMed card, wherever they appear, synthetic output included; nothing it ignores is ever added with `git add -f`.

## Security

Z, 2026-09-18: *"we should be careful with JS. It should be completely open source. We also need to work on the security. I mean JS injection attacks would be terrible."*

- **A file is untrusted input.** Anyone can craft a card, or share one. Text read from a file -- a header field, an event annotation -- reaches the page only as text, never as markup, and nothing read from a file is ever run as code. `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`, `eval` and `new Function` appear nowhere in the source; grep for them, and the check is that it finds nothing.
- **The parser trusts no number a file declares.** Every size, count and offset in a header is checked against the real size of the file before it is used. A file that does not add up is reported, never read past its end.
- **The Content-Security-Policy is the second wall.** It is a `<meta>` tag, because GitHub Pages cannot set response headers. Scripts and styles run only if their hash is in the policy, and the build computes the hashes from the files it inlines. No inline event handlers, no `eval`, and no outbound connection of any kind. An injection that got past the first rule would still not run, and could send nothing. Any change to the policy is raised with Z by name. Alongside it, `<meta name="referrer" content="no-referrer">`.
- **The page refuses to run inside a frame.** A `<meta>` policy cannot forbid framing, so the page checks for itself.
- **Nothing may need a header GitHub Pages cannot send.** Cross-origin isolation above all: no `SharedArrayBuffer`, no threaded WebAssembly, and no service worker to add headers back, which would also break the offline file. A feature that would need one is raised with Z, not worked around.
- **Every line of JavaScript is open source and readable.** Libraries are few, each approved by Z by name, stored in the repository unminified and pinned to a version, under a license compatible with GPL-3.0. Nothing is loaded from a CDN or any other host.
- **The build is one short script on the Python standard library.** No package manager, so no dependency tree stands behind what ships. It inlines everything into one self-contained HTML file, and that file is both what the site serves and the offline download. The same input gives the same bytes, and each release publishes the file's checksum, so anyone can rebuild it and compare.
- **Only Z publishes.** Z is the sole maintainer, with two-factor authentication on the account, and the agent never pushes (Z, 2026-09-18).

## Building and running it

- `python3 build.py` writes `dist/index.html` and prints its SHA-256. `dist/` is build output and is not tracked.
- Opening `dist/index.html` straight from disk is the offline page, and needs no server.
- **When the agent needs a server, it uses port 8765** (Z, 2026-09-18): `python3 -m http.server 8765 --bind 127.0.0.1 --directory dist`. It records the PID when it starts one, stops only that PID, and never touches a server it did not start.
- **A browser the agent starts for a check is headless, with its own temporary profile directory, and exits on its own.** It never attaches to a browser Z is using.

## Comments: what the code does, never why we chose it

**Every comment clause is either a description of the code below it or a design decision. Descriptions stay, in one line. Decisions move to `.claude/development-notes/` and leave the source.**

The unit is the clause, not the comment. The usual failure is a comment that opens with a real description and smuggles a justification in after it. Write what the code does, stop, and check whether what you were about to add next is a decision.

**Why:** a design decision left in a comment reads to a later session as a current constraint, and gets argued from against what is actually being asked. Z, on PoolSeqFlow, 2026-08-30: *"In multiple occasions, the previous design decisions have skewed your interpretation of my asks, we had to spend way too much time on simple tasks."*

Not every "why" is a decision. The cut is whether the code becomes **inexplicable** without the line, or merely **unjustified**. A constraint that makes an otherwise pointless line explicable is what the code does, and stays. A constraint that defends one working choice over another is a decision, and goes.

Before calling a file done, grep for `on purpose | deliberately | rather than | because | would otherwise | so that | which is why`. Each hit is a candidate, not a verdict, and the grep is never made a pass/fail gate: a hard failure trains the next session to reword around the words instead of removing the decision.

| Where | What |
|---|---|
| the source | what the code below does, what it returns, a coupling or constraint invisible from here |
| the user documentation | anything that changes what a displayed number **means**, or that a person reading their own data needs. It is authoritative, and nothing in it is repeated in the source. Where it lives has not been decided. |
| `.claude/development-notes/` | how it got here: design churn, alternatives dropped, measurements, who decided what and when |

**No source file references the notes.** A note is dated and not updated to follow the code, so a pointer to one imports a description of the code as it used to be.

**Mid-feature is not the deadline, but the feature has one.** A comment may carry more than the code needs while a stage is open; every stage ends with a pass over the comments it added. Put that pass in the stage's checklist when the stage starts, or it is the thing that gets skipped.

**Development tooling, the synthetic data generator among it, follows the opposite rule: keep everything but abandoned ideas.** There the reasoning is the content. A measurement with no account of what it measured cannot be acted on, and a synthetic case with no record of what it was built to exercise gets deleted as arbitrary. The one thing to cut is an approach that was dropped, described as though it were still how things work.

## Development notes

`.claude/development-notes/` is the record of how PAPvault got here, one file per subject rather than per source file.

- **Every note opens with `**Written <date>, against the tree at <hash>.**`** and is never rewritten to follow the code. Appending a new, dated finding is allowed; correcting an old description to match today's code is not. Where a note and the user documentation disagree, the documentation is right and the note is history.
- **Two files are exceptions and say so at the top:** the index, `README.md`, and a file of platform traps that is appended to as they are found. Both are kept current.
- **Durable knowledge goes here, not only into the agent's memory.** Memory is private to one account and nobody can review it; a note is a reviewable artifact that travels with the checkout. The memory entry is a one-line pointer to the note.
- **A note hands its reader the command that would falsify it**, rather than asserting a count or a mechanism in prose.
- **This file and the notes are public** (Z, 2026-09-18). Write both for a reader outside the project, and never put a value from real data in either.

## How work is reviewed

- **Never `git push`**, or anything else outward-facing: no `gh pr create`, no release, no remote branch. Z publishes. `git stash push` reads as a push in a command line, so say beforehand that it is local, or avoid it.
- **Never `git commit` unless asked, and a commit instruction covers only the work that existed when it was given.** Do the work, leave it uncommitted, say what changed in prose, stop. The uncommitted tree is the review surface; a diff artifact or a summary page is not a substitute.
- **Use the `Edit` tool for changes to an existing file, never a script that rewrites it.** Z reviews side by side in the IDE diff view as each edit lands, and a rewritten file gives that view nothing to show. An announced mechanical rename with `sed` is the one exception. Reaching for a script is a sign the change is too big to review in one go.
- **One change at a time.** Finish one item, say exactly what changed, what the agent checked and what is left for Z to check, then stop. Keep a list of deferred items and restate it at the end of each turn.
- **Do not overstate severity.** "Bug" is for behavior that is wrong, not behavior that is non-deterministic, unidiomatic or different from before. Describe what was measured and let Z judge; a preference is offered as a preference.

## How decisions are made

- **Fail loudly, or document -- never automate away a decision.** Where the right answer depends on something the application cannot know, it says so and stops. A computed default never removes the knob. Something done for the user as a side effect of something else is not the same as the user asking for it by name.
- **Settle a design question with data rather than argument, where data can settle it.** Build the case that would distinguish the two claims, run it, read what comes back. The data then becomes part of the repository, so anyone who disagrees can re-run it. Here that data is synthetic.
- **What a device value means -- its unit, what a flag or an event code stands for -- comes from a cited source Z has checked**, never from the agent's recollection. The agent's expensive errors are the plausible ones, and a mislabeled value is where a plausible error hides.

## How to know a change works

**Z tests every change personally, and there is no automated test suite.** Whether a change is right is Z's call, and a suite the agent writes and runs is the agent vouching for itself. A suite may come once there is enough synthetic data to build one on (Z, 2026-09-18); until then nothing here assumes one.

What a person cannot do is re-check, after every change, everything that was checked before, and an agent produces changes faster than anyone can. Three things cover that, and none of them takes the testing away from Z:

1. **The promise is enforced by the page, not by care.** The Content-Security-Policy described under *Security* makes the browser refuse any outbound connection. It is in place before the first feature that reads a file.
2. **A written checklist, run by Z before each release**, in `CHECKLIST.md` at the repository root: what to check, and what a failure looks like. A check with no stated failure is not a check. When a change adds behavior worth protecting, propose its checklist entry with the change.
3. **A record of every verification, in Z's words**, in `VERIFICATION.md` at the repository root: what was checked, on what data, at which commit. Testing that is not written down is invisible to the reviewer this project is for. **The agent never writes that Z verified something**, and never presents its own checks as Z's.

What the agent does before handing a change over:

- **Say what it checked itself, and show the output**, separately from what is left for Z to check, and name what it did not check.
- **Read the whole output of anything it runs.** In PoolSeqFlow the tail of a failure summary was read as a list of passes.
- **Two things that must agree are derived from one source, never kept in step by hand.** A pair kept in step by care drifts silently and produces a wrong result rather than a failure.
- **After any move, rename or filter, ask what was pointed at the old thing**, and grep for it. A check aimed at something that moved keeps passing over nothing.
- **Synthetic data carries its own answer.** What a case should show is derived from how it was built, and the generator is committed rather than its output. An expectation read off what the code produced is a check that cannot fail.

## House style

American English everywhere. ASCII only in the text we write -- `--`, `...`, `->`, straight quotes -- except data we did not author, a character that is the subject of the sentence, a glyph the application renders, and a literal whose other half a text tool cannot reach. No hard wrapping in markdown: one line per paragraph and per list item.
