// The CPAP day rule, at the second either side of every edge it has.
//
// Z, 2026-09-20: a session starting at or after 06:00:00 on day X belongs to day X;
// one starting at or before 05:59:59 belongs to day X-1, whenever it ends.
//
// Z, 2026-09-23, on the break: a session that starts within an hour of the end of the
// one before it stays on that session's day; one starting at or after noon takes the
// day the boundary gives it whatever came before.
const fs = require("fs"), path = require("path"), vm = require("vm");
const ROOT = process.argv[2];
const context = { TextDecoder, console, Blob, Map, Set };
vm.createContext(context);
for (const f of ["src/edf.js", "src/card.js"]) {
  vm.runInContext(fs.readFileSync(path.join(ROOT, f), "utf8"), context);
}
const Card = context.PAPvaultCard;

let checks = 0, bad = 0;
function expect(what, got, want) {
  checks++;
  if (got !== want) { bad++; console.log("  MISMATCH " + what + "\n    got  " + got + "\n    want " + want); }
}

const cases = [
  ["2026-03-10 05:59:58", "2026-03-09"],
  ["2026-03-10 05:59:59", "2026-03-09"],
  ["2026-03-10 06:00:00", "2026-03-10"],
  ["2026-03-10 06:00:01", "2026-03-10"],
  ["2026-03-10 00:00:00", "2026-03-09"],
  ["2026-03-10 12:00:00", "2026-03-10"],
  ["2026-03-10 23:59:59", "2026-03-10"],
  // Across a month, a year, and a leap day.
  ["2026-03-01 05:00:00", "2026-02-28"],
  ["2026-01-01 05:00:00", "2025-12-31"],
  ["2024-03-01 05:00:00", "2024-02-29"],
  // The US spring-forward is 2026-03-08, when 02:00 does not exist locally.
  ["2026-03-08 05:59:59", "2026-03-07"],
  ["2026-03-08 06:00:00", "2026-03-08"],
  ["2026-03-09 05:59:59", "2026-03-08"],
  // The autumn fall-back is 2026-11-01, when 01:00 to 02:00 happens twice.
  ["2026-11-01 05:59:59", "2026-10-31"],
  ["2026-11-01 06:00:00", "2026-11-01"],
];

for (const [when, want] of cases) {
  const [date, clock] = when.split(" ");
  const [y, m, d] = date.split("-").map(Number);
  const [hh, mm, ss] = clock.split(":").map(Number);
  const at = new Date(y, m - 1, d, hh, mm, ss);
  expect(when + " belongs to", Card.dayKey(Card.cpapDayOf(at)), want);
}

// And the day a key names starts at 6 in the morning of that date.
const start = Card.cpapDayStart(new Date(2026, 2, 10));
expect("2026-03-10 starts at hour", start.getHours(), 6);
expect("2026-03-10 starts on date", Card.dayKey(start), "2026-03-10");

// A short break in the use does not start a new day.
function at(text) {
  const [date, clock] = text.split(" ");
  const [y, m, d] = date.split("-").map(Number);
  const [hh, mm, ss] = clock.split(":").map(Number);
  return new Date(y, m - 1, d, hh, mm, ss || 0);
}

// The days a night's sessions land on, in the order the sessions ran. Each entry is
// a session written as "start .. end".
function daysFor(spans) {
  const sessions = spans.map(function (span) {
    const [from, to] = span.split(" .. ");
    const end = at(to);
    return { start: at(from), end: end, flowEnd: end };
  });
  return Card.daysOf(sessions).map(function (session) {
    return session.dayKey;
  }).join(" ");
}

const nights = [
  // The defect Z found: a few minutes out of the mask, back on after 6.
  ["a break of five minutes across 6:00",
    ["2026-03-09 23:00:00 .. 2026-03-10 06:02:00", "2026-03-10 06:07:00 .. 2026-03-10 07:30:00"],
    "2026-03-09 2026-03-09"],
  // The edges of the hour, measured end to start.
  ["a break of exactly an hour",
    ["2026-03-09 23:00:00 .. 2026-03-10 06:00:00", "2026-03-10 07:00:00 .. 2026-03-10 07:30:00"],
    "2026-03-09 2026-03-09"],
  ["a break of an hour and one second",
    ["2026-03-09 23:00:00 .. 2026-03-10 06:00:00", "2026-03-10 07:00:01 .. 2026-03-10 07:30:00"],
    "2026-03-09 2026-03-10"],
  ["a break of an hour and a quarter",
    ["2026-03-09 23:00:00 .. 2026-03-10 05:30:00", "2026-03-10 06:45:00 .. 2026-03-10 07:30:00"],
    "2026-03-09 2026-03-10"],
  // Breaks chain: the third session reads the day the second was given, not the clock.
  ["three sessions, each a short break apart",
    ["2026-03-09 23:00:00 .. 2026-03-10 06:05:00", "2026-03-10 06:20:00 .. 2026-03-10 06:50:00",
      "2026-03-10 07:30:00 .. 2026-03-10 08:00:00"],
    "2026-03-09 2026-03-09 2026-03-09"],
  ["a chain broken in the middle",
    ["2026-03-09 23:00:00 .. 2026-03-10 06:05:00", "2026-03-10 06:20:00 .. 2026-03-10 06:50:00",
      "2026-03-10 08:30:00 .. 2026-03-10 09:00:00"],
    "2026-03-09 2026-03-09 2026-03-10"],
  // Noon stops the chain however short the break is.
  ["a chain reaching the middle of the day",
    ["2026-03-09 23:00:00 .. 2026-03-10 11:00:00", "2026-03-10 11:30:00 .. 2026-03-10 11:50:00",
      "2026-03-10 12:10:00 .. 2026-03-10 13:00:00"],
    "2026-03-09 2026-03-09 2026-03-10"],
  ["a session starting at noon exactly",
    ["2026-03-09 23:00:00 .. 2026-03-10 11:45:00", "2026-03-10 12:00:00 .. 2026-03-10 13:00:00"],
    "2026-03-09 2026-03-10"],
  ["a session starting a second before noon",
    ["2026-03-09 23:00:00 .. 2026-03-10 11:45:00", "2026-03-10 11:59:59 .. 2026-03-10 13:00:00"],
    "2026-03-09 2026-03-09"],
  // What the rule must leave alone.
  ["one session, no break at all",
    ["2026-03-09 23:00:00 .. 2026-03-10 06:30:00"], "2026-03-09"],
  ["a mask-off break in the middle of the night",
    ["2026-03-09 23:00:00 .. 2026-03-10 02:00:00", "2026-03-10 02:10:00 .. 2026-03-10 05:00:00"],
    "2026-03-09 2026-03-09"],
  ["a morning nap hours after the night ended",
    ["2026-03-09 23:00:00 .. 2026-03-10 05:00:00", "2026-03-10 09:00:00 .. 2026-03-10 10:00:00"],
    "2026-03-09 2026-03-10"],
  ["two nights running",
    ["2026-03-09 23:00:00 .. 2026-03-10 06:30:00", "2026-03-10 22:00:00 .. 2026-03-11 05:00:00"],
    "2026-03-09 2026-03-10"],
  // An afternoon nap is its own day's, and the night after it joins that same day.
  ["an afternoon nap and the night after it",
    ["2026-03-10 14:00:00 .. 2026-03-10 15:00:00", "2026-03-10 23:00:00 .. 2026-03-11 06:20:00",
      "2026-03-11 06:40:00 .. 2026-03-11 07:00:00"],
    "2026-03-10 2026-03-10 2026-03-10"],
  // The autumn fall-back repeats 01:00 to 02:00, so a break there is measured in real
  // time and not by what the clock reads.
  ["a break across 6:00 on the morning the clocks go back",
    ["2026-10-31 23:00:00 .. 2026-11-01 06:10:00", "2026-11-01 06:40:00 .. 2026-11-01 07:00:00"],
    "2026-10-31 2026-10-31"],
];

for (const [what, spans, want] of nights) {
  expect(what, daysFor(spans), want);
}

// A session with no flow in it is timed by the span of its files instead, and its
// flowEnd is null. The break after it is measured from the same moment either way.
const noFlow = Card.daysOf([
  { start: at("2026-03-09 23:00:00"), end: at("2026-03-10 06:02:00"), flowEnd: null },
  { start: at("2026-03-10 06:07:00"), end: at("2026-03-10 07:30:00"), flowEnd: null },
]).map(function (session) { return session.dayKey; }).join(" ");
expect("a break after a session with no flow", noFlow, "2026-03-09 2026-03-09");

console.log("\n" + checks + " checks, " + bad + " mismatches");
if (bad) { process.exitCode = 1; }
