// Builds cards where one night's files are stamped at different moments, which is
// what a real machine does and what no committed case carries.
//
//     node dev/tests/cards/make-split-cards.js <repo root> <out dir>
//
// Each card is plain-night with its SAD file moved to a stamp of its own, its header
// start moved with it so the two agree. Three of them, either side of the gap that
// decides whether two recordings are one session:
//
//   sad-inside  the oximeter joins 40s after the machine started   -> 1 session
//   sad-close   it starts 3s after the recording ended             -> 1 session
//   sad-far     it starts 40s after the recording ended            -> 2 sessions
//
// Grouping by the file-name stamp alone gives 2 sessions for all three.
//
// Only the header's start is moved, not the samples behind it, which is enough for
// a count of sessions and is not a card to read any figure off.
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const ROOT = process.argv[2];
const OUT = process.argv[3];

const context = { TextDecoder, console };
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(ROOT, "src/edf.js"), "utf8"), context);
const EDF = context.PAPvaultEDF;

const START_DATE_AT = 168;
const START_TIME_AT = 176;
const CASE = path.join(ROOT, "dev/synthetic/out/resmed/plain-night");

function copyTree(from, to) {
  fs.mkdirSync(to, { recursive: true });
  for (const name of fs.readdirSync(from)) {
    const source = path.join(from, name);
    const target = path.join(to, name);
    if (fs.statSync(source).isDirectory()) {
      copyTree(source, target);
    } else {
      fs.copyFileSync(source, target);
    }
  }
}

function findFile(dir, ending, found) {
  for (const name of fs.readdirSync(dir)) {
    const full = path.join(dir, name);
    if (fs.statSync(full).isDirectory()) {
      findFile(full, ending, found);
    } else if (name.endsWith(ending)) {
      found.push(full);
    }
  }
  return found;
}

function two(value) {
  return String(value).padStart(2, "0");
}

function headerOf(file) {
  const bytes = fs.readFileSync(file);
  const buffer = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
  return { bytes: bytes, header: EDF.parseHeader(buffer, bytes.length) };
}

// Writes the EDF start date and time, which are fixed-width ASCII fields.
function restamp(file, when, kind) {
  const bytes = fs.readFileSync(file);
  const date = two(when.getDate()) + "." + two(when.getMonth() + 1) + "." + two(when.getFullYear() % 100);
  const clock = two(when.getHours()) + "." + two(when.getMinutes()) + "." + two(when.getSeconds());
  bytes.write(date, START_DATE_AT, 8, "ascii");
  bytes.write(clock, START_TIME_AT, 8, "ascii");
  const stamp = String(when.getFullYear()) + two(when.getMonth() + 1) + two(when.getDate())
    + "_" + two(when.getHours()) + two(when.getMinutes()) + two(when.getSeconds());
  const moved = path.join(path.dirname(file), stamp + "_" + kind + ".edf");
  fs.writeFileSync(moved, bytes);
  if (moved !== file) {
    fs.unlinkSync(file);
  }
  return { moved: moved, stamp: stamp };
}

const cases = [
  { name: "sad-inside", from: "start", seconds: 40, sessions: 1 },
  { name: "sad-close", from: "end", seconds: 3, sessions: 1 },
  { name: "sad-far", from: "end", seconds: 40, sessions: 2 },
  // A second recording of the SAME kind three seconds on: one session holding two
  // PLD files, which is what a machine that pauses for a breath writes.
  { name: "pld-twice", from: "end", seconds: 3, sessions: 1, copyPld: true },
];

for (const one of cases) {
  const target = path.join(OUT, one.name);
  fs.rmSync(target, { recursive: true, force: true });
  copyTree(CASE, target);

  const pld = findFile(target, "_PLD.edf", [])[0];
  const held = headerOf(pld);
  const begins = held.header.start;
  const ends = new Date(begins.getTime() + held.header.recordCount * held.header.recordSeconds * 1000);
  const anchor = one.from === "start" ? begins : ends;
  const when = new Date(anchor.getTime() + one.seconds * 1000);

  if (one.copyPld) {
    const copy = path.join(path.dirname(pld), "copy_PLD.edf");
    fs.copyFileSync(pld, copy);
    const moved = restamp(copy, when, "PLD");
    const check = headerOf(moved.moved);
    console.log("%s: a second PLD stamped %s, header start %s, must read as %d session(s)"
      + " whose PLD signals hold twice the samples",
      one.name, moved.stamp, check.header.start.toISOString(), one.sessions);
    continue;
  }

  const sad = findFile(target, "_SAD.edf", [])[0];
  const moved = restamp(sad, when, "SAD");
  const check = headerOf(moved.moved);
  console.log("%s: SAD now stamped %s, header start %s, must read as %d session(s)",
    one.name, moved.stamp, check.header.start.toISOString(), one.sessions);
}
