# Development notes

**This file is kept current.** It is the index, and one of the two exceptions to the dating rule below.

These notes record why PAPvault is built the way it is: decisions and who made them, what was tried and dropped, what a choice was measured against, and the traps that produced a wrong answer once already. They are not user documentation, and they do not explain what the code does -- that stays in the code. They are the reasoning a person needs before they *change* something.

They are public (Z, 2026-09-18), and so is `CLAUDE.md` at the repository root, the file the agent reads at the start of every session. How PAPvault is built should be as readable as what it does.

## These notes are dated

**Every note records the tree as it stood when it was written, and says so in its first line:**

```
**Written <date>, against the tree at <hash>.**
```

A note is never rewritten to follow the code. It may gain a new finding at the end, dated; an old description is never corrected to match today's code, because a note that has been kept in step can no longer be dated. So a present-tense sentence inside a note describes the code at that note's date. Where a note and the user documentation disagree, the documentation is right and the note is history.

**Two files are exceptions, and each says so at the top:** this index, and `platform-traps.md`, which is appended to as traps are found, with a date on each entry, because a trap does not expire. Both are kept current.

**A note hands its reader the command that would falsify it**, rather than asserting a count or a mechanism in prose. When PoolSeqFlow audited its own notes, the stale ones were those that asserted a mechanism with no way to check it from the page.

## What never goes in a note

**No value from real data.** Not a pressure, not an event count, not the date a recording was made -- nothing read from a device's card, however aggregated. The notes are public, and the promise of the project is that health data stays on its owner's machine. A measurement a decision rests on is made on synthetic data, and the generator that made it is committed.

**Nothing a source file points to.** No source file references these notes: a note is dated, so a pointer to one imports a description of the code as it used to be. A note names the source it applies to; the source does not point back.

## The three destinations

The rule lives in `CLAUDE.md`, which loads into every session; this file does not. In short:

| Where | What |
|---|---|
| **the source** | what the code below does, what it returns, a coupling or constraint invisible from where it is read |
| **the user documentation** | anything that changes what a displayed number means, or that a person reading their own data needs |
| **here** | how it got here: design churn, alternatives tried and dropped, measurements, who decided what and when |

A decision that changed five times belongs here and nowhere else.

## Layout

One file per subject, not per source file: the reasoning crosses file boundaries far more than the code does.

| File | Subject |
|---|---|
| `ground-rules.md` | how the working rules in `CLAUDE.md` were set: what came across from PoolSeqFlow, what was left behind, and what PAPvault added |
| `ground-truth.md` | the R prototype as the reference for reading a real card: what it covers, and what agreement with it can and cannot show |
| `product-brief.md` | the brief as Z first gave it and what was settled that day: one page on GitHub Pages, the date and time selection, a day as noon to noon, display without conclusions, and the stack |
| `security.md` | what is protected and from what, why the page is one file with a hashed `<meta>` policy, and what the design does not cover |
| `empty-page.md` | the page, the build and the local server as first built, and what the agent checked before handing them over |
| `page-layout.md` | the card layout and the calendar, the decisions in them, and the charting libraries measured before the choice |
| `platform-traps.md` | kept current: the shell and tooling traps that produced a wrong result once |
