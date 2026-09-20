// A card with a file set the machine wrote when it was not recording a night: no
// flow in it, and stamped at an hour of its own. It must not become a session, must
// not move the night it attaches to across the 6 o'clock cut, and must not take the
// night's events away with it.
//
//     node dev/tests/cards/make-stray-card.js <repo root> <out dir>
const fs = require("fs"), path = require("path");
const ROOT = process.argv[2], OUT = process.argv[3];
const START_DATE_AT = 168, START_TIME_AT = 176;
const CASE = path.join(ROOT, "dev/synthetic/out/resmed/plain-night");

function copyTree(from, to) {
  fs.mkdirSync(to, { recursive: true });
  for (const name of fs.readdirSync(from)) {
    const source = path.join(from, name), target = path.join(to, name);
    if (fs.statSync(source).isDirectory()) { copyTree(source, target); }
    else { fs.copyFileSync(source, target); }
  }
}
function findFile(dir, ending, found) {
  for (const name of fs.readdirSync(dir)) {
    const full = path.join(dir, name);
    if (fs.statSync(full).isDirectory()) { findFile(full, ending, found); }
    else if (name.endsWith(ending)) { found.push(full); }
  }
  return found;
}
const two = (v) => String(v).padStart(2, "0");

const target = path.join(OUT, "stray-set");
fs.rmSync(target, { recursive: true, force: true });
copyTree(CASE, target);

// plain-night runs 22:30 on the 10th to 06:30 on the 11th, which is CPAP day the
// 10th. The stray set is stamped at 14:00 on the 10th: earlier than the night's
// start, and on the far side of nothing, so if it drags the start the day stays the
// 10th but the hours balloon; if it were stamped before 06:00 the day would move.
const eve = findFile(target, "_EVE.edf", [])[0];
const copy = Buffer.from(fs.readFileSync(eve));
const when = new Date(2026, 2, 10, 14, 0, 0);
copy.write(two(when.getDate()) + "." + two(when.getMonth() + 1) + "." + two(when.getFullYear() % 100), START_DATE_AT, 8, "ascii");
copy.write(two(when.getHours()) + "." + two(when.getMinutes()) + "." + two(when.getSeconds()), START_TIME_AT, 8, "ascii");
fs.writeFileSync(path.join(path.dirname(eve), "20260310_140000_EVE.edf"), copy);
console.log("stray-set written: one extra EVE at 14:00, no flow in it");
console.log("must read as 1 session, day 2026-03-10, 22:30 to 06:30, events kept");
