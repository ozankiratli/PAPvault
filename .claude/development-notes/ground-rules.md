# How the working rules were set

**Written 2026-09-18, against the tree at `a201834`**, the initial commit. `CLAUDE.md` and these notes were uncommitted and under review, and no stack had been chosen.

PAPvault's `CLAUDE.md` did not start from nothing. Z asked for it to be adapted from the framework built for PoolSeqFlow ([github.com/ozankiratli/PoolSeqFlow](https://github.com/ozankiratli/PoolSeqFlow)) while that project was developed with Claude Code in August and September 2026. That framework is three things: the repository's `CLAUDE.md`, which is the rules as given to the agent; its `.claude/development-notes/`, the dated record this directory copies; and the *Involvement of Claude Code* page of its manual, the public account of why each rule exists. The manual page is the one to read for the reasoning. This note records only what changed on the way across.

## What came across

What came across is whatever does not depend on what is being built. Each rule was produced in PoolSeqFlow by a specific failure, and none is about AI as such: every one would improve a project with no agent anywhere near it. What the agent did there was make them load-bearing, by supplying a steady stream of the mistakes each one prevents.

**The comment rule and its three destinations**, including the clause-level test and the inverted rule for test and development tooling. Its origin is quoted in `CLAUDE.md`: design decisions left in comments were read back as current constraints and argued from against what Z was asking for.

**The dated-notes convention.** PoolSeqFlow's notes were audited and stamped on 2026-09-05, and every stale claim found was one of four kinds: a prediction that did not come true, a claim inverted by later work, a rename, or an open item that had since closed. None of those is prevented by writing more carefully. What prevents them is not letting a note pretend to be current.

**The review loop**: never push, commit only what was reviewed, change files with `Edit`, one change at a time, and do not overstate severity. Each is on record in PoolSeqFlow as a correction. The agent committed work Z had not reviewed, against a standing instruction. It rewrote files with Python scripts until Z said, on 2026-08-28, *"Can you make changes easier for me to review, you are doing a lot of python changes it's really hard to review."*

**The verification rules, in part.** In PoolSeqFlow the agent ran the full suite after being asked not to, costing the better part of an hour, and reported a run as passing when twelve cases had failed, because it read the output through `tail`. Six times on one day, 2026-09-10, a check kept exiting 0 after a change had moved what it was aimed at. The first draft carried PoolSeqFlow's verification rules across whole. The same day, the ones that assume an automated suite came out, for the reason under *What PAPvault added*. What stayed is reading the whole output of anything run, deriving what a case should show from how it was built, and asking what pointed at a thing that moved.

**How decisions are made**: fail loudly or document, and settle a question with data where data can settle it.

## What was left behind

Everything tied to PoolSeqFlow's stack or its release process: the Nextflow lint command and its traps, the table of test suites and their cost classes, the exemption for configuration templates that ship to users, the semver declaration, and the changelog convention. PAPvault had no stack on this date. Each comes back, reworded, when there is something for it to govern. A rule about a tool that is not in use is a rule nobody can check, and it reads to a later session as a constraint on a choice that has not been made.

PoolSeqFlow's rule that nothing may point at its real-data directory did not come across as it was. PAPvault's version is stronger, for a different reason, below.

## What PAPvault added

Four rules have no direct counterpart in PoolSeqFlow, and all four come from what the product is.

**The promise, as two invariants.** Z stated the goal when the revival began -- *"build a web platform that people can view their data interactively without uploading their data to internet"* -- and later the same day ruled out telemetry entirely: *"We won't have any telemetry allowed on this website, it is a trust issue, so no analytics no collection of any data."* These are separate requirements. The first is about the data a person brings; the second is about the person. A site could keep the first perfectly and still count its visitors. Both are to be enforced by a failing check built with the stack, and until those checks exist any network request the application makes is raised with Z rather than decided in passing.

**The agent's context is not local.** In PoolSeqFlow the real data was off limits because of its cost: tens of gigabytes and hours of compute. Here the reason is different in kind. When the agent reads a file, the file's contents go to Anthropic's servers, so a development process that inspects real device data would break, during development, the promise the application exists to keep. Hence the rules that the agent never reads real data, that data for development and checking is synthetic and built by a committed generator, that format knowledge comes from published specifications and open-source readers, and that nothing derived from real data enters the repository unless Z approves that item. Z confirmed the strict form the same day: *"For now, let's not touch the data."*

**A clinical number needs a checked source.** PoolSeqFlow's version of this was about method citations, one of which was attributed to the wrong source twice before it was right. PAPvault's is about thresholds and meanings -- a severity band, a leak limit, what a device flag means -- because a plausible wrong threshold looks exactly like a right one, and nothing in the code can tell them apart.

**Verification by a person, not by a suite.** Z leaned toward no test suite, with every test done personally, for a reason that is the project's purpose: a suite the agent writes and runs is the agent vouching for itself, and the claim PAPvault exists to make is that a human holds the authority. The agent agreed with the principle and raised one gap, regression. A person can check each change as it lands, but cannot re-check everything checked before after every change, and an agent produces changes faster than anyone can; PoolSeqFlow's own account says failures of process are caught only afterwards. Three things were proposed to cover it without moving the testing off Z: the privacy promise enforced by the page itself, through a Content-Security-Policy; a written checklist, with the failure each item looks for, run by Z before each release; and a record of every verification in Z's words, because testing that is not written down is invisible to the reviewer the project is for. Z: *"You're right. Once we have enough synthetic data we might start building a test suite too. 3 points are correct. We'll keep the second as is for now."*

## The rulings of 2026-09-18

- PAPvault is a showcase of what Z calls human-in-the-steering-wheel development, as opposed to human-in-the-loop: *"I want the reviewer to look at this and say, 'yeah AI agents can be used responsibly, when developing a health related app.'"* That is why the rules and the notes are written for a reader outside the project.
- The rules and the notes are public: *"The rules will be public"*, then *"The notes too."*
- No telemetry and no collection of any data, as quoted above.
- Z tests every change personally, and there is no automated test suite for now. Regression is covered by the three measures above.
- Real data is not touched for now, and the R prototype's reading of it is the ground truth. What that covers is in `ground-truth.md`.
