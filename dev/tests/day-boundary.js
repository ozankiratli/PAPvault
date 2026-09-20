// The CPAP day rule, at the second either side of every edge it has.
//
// Z, 2026-09-20: a session starting at or after 06:00:00 on day X belongs to day X;
// one starting at or before 05:59:59 belongs to day X-1, whenever it ends.
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

console.log("\n" + checks + " checks, " + bad + " mismatches");
if (bad) { process.exitCode = 1; }
