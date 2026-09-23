// The cards the committed cases cannot be, and what the reader must make of them.
//
//     node dev/tests/cards/derived.js <repo root> <where to build them>
//
// Every case in dev/synthetic/out is a night the machine stamped in one go, so one rule
// here has no committed case that can fail on it:
//
//   a session is a stretch of flow      every stamp in the cases is hours from the next
//
// So this builds cards from the committed ones by moving a file's stamp and its header
// start together, and asserts what the reader must then say. The builders beside this
// file do the writing.
//
// It also writes physical zero over the leak of every second record. That rule does now
// have a committed case, on-and-off-leak, whose leak goes on and off in runs of minutes;
// this is the same rule at a finer alternation, half the samples above zero and the
// switch falling on every record boundary.
const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");
const vm = require("vm");

const ROOT = path.resolve(process.argv[2] || ".");
const OUT = path.resolve(process.argv[3] || path.join(ROOT, "dev/tests/out"));

const context = { TextDecoder, console, Blob, Map, Set };
vm.createContext(context);
for (const f of ["src/edf.js", "src/card.js"]) {
  vm.runInContext(fs.readFileSync(path.join(ROOT, f), "utf8"), context);
}
const Card = context.PAPvaultCard;

let checks = 0;
const bad = [];
function expect(what, got, want) {
  checks++;
  const ok = typeof want === "number" && typeof got === "number"
    ? Math.abs(got - want) < 1e-6 : got === want;
  if (!ok) {
    bad.push(what);
    console.log("    FAIL  " + what + "\n      got  " + got + "\n      want " + want);
  }
}

function itemsOf(dir, prefix) {
  const out = [];
  for (const name of fs.readdirSync(dir)) {
    const full = path.join(dir, name);
    if (fs.statSync(full).isDirectory()) {
      out.push(...itemsOf(full, prefix + name + "/"));
    } else if (name !== "answer.json") {
      out.push({ file: new Blob([fs.readFileSync(full)]), path: prefix + name });
    }
  }
  return out;
}

async function read(card) {
  return Card.read(itemsOf(card, path.basename(card) + "/"));
}

function build(script, where) {
  execFileSync("node", [path.join(ROOT, "dev/tests/cards", script), ROOT, where],
    { stdio: ["ignore", "pipe", "pipe"] });
}

(async function () {
  fs.rmSync(OUT, { recursive: true, force: true });
  fs.mkdirSync(OUT, { recursive: true });

  build("make-split-cards.js", OUT);
  build("make-stray-card.js", OUT);
  build("make-gappy-leak.js", OUT);
  build("make-other-units.js", OUT);

  // A session is a stretch of flow. The first two move a file that carries no flow, so
  // they must not add a session however far away it is stamped; the third moves a file
  // that does, three seconds after the flow ended, which is inside the gap.
  for (const [name, want] of [["sad-inside", 1], ["sad-close", 1], ["sad-far", 1],
                              ["pld-twice", 1], ["stray-set", 1]]) {
    const card = path.join(OUT, name);
    const held = await read(card);
    expect(name + ": sessions", held.sessions.length, want);
    expect(name + ": nothing refused", held.refused.length, 0);
  }

  // The stray set is stamped at two in the afternoon, eight hours before the night it
  // belongs to. It must not drag the night's start back to itself, which would move the
  // night across the 6 o'clock cut on a card where it was stamped a little earlier.
  const stray = await read(path.join(OUT, "stray-set"));
  const night = stray.sessions[0];
  expect("stray-set: the night still starts at 22:30", night.start.getHours(), 22);
  expect("stray-set: the night still belongs to the 10th", night.dayKey, "2026-03-10");
  expect("stray-set: it was counted as stamped away from any night", stray.asideCount, 1);
  const strayLoaded = await Card.load(night, ["pressure"]);
  expect("stray-set: the night keeps its events", strayLoaded.events.length > 0, true);

  // Two files of one kind in one session: the second one's samples must be carried on
  // rather than dropped, which is what a machine that pauses for a breath produces.
  const twice = await read(path.join(OUT, "pld-twice"));
  const plain = await read(path.join(ROOT, "dev/synthetic/out/resmed/plain-night"));
  const twiceLoaded = await Card.load(twice.sessions[0], ["pressure"]);
  const plainLoaded = await Card.load(plain.sessions[0], ["pressure"]);
  expect("pld-twice: the second file's samples are kept",
    twiceLoaded.signals.pressure.y.length, plainLoaded.signals.pressure.y.length * 2);

  // Leak duration. The gappy card has physical zero over the leak of every second data
  // record, so exactly half its samples are above zero and the answer is built in.
  const gappy = await read(path.join(OUT, "gappy-leak"));
  const gappyLoaded = await Card.load(gappy.sessions[0], ["leak"]);
  const leak = gappyLoaded.signals.leak;
  let above = 0;
  for (let i = 0; i < leak.y.length; i++) {
    if (leak.y[i] > 0) { above++; }
  }
  expect("gappy-leak: half the leak samples are above zero", above, leak.y.length / 2);
  expect("gappy-leak: that is four hours at two seconds a sample",
    above * leak.interval, 4 * 3600);

  // A leak recorded per second is shown per minute, and a tidal volume recorded in
  // liters is shown in milliliters. The card is on-and-off-leak with three header
  // fields rewritten per signal and not one data byte touched, so the converted
  // figures must be the ones the original card gives, and the units must say so.
  const other = await read(path.join(OUT, "other-units"));
  const original = await read(path.join(ROOT, "dev/synthetic/out/resmed/on-and-off-leak"));
  const otherLoaded = await Card.load(other.sessions[0], ["leak", "tidVol"]);
  const asWrittenLoaded = await Card.load(original.sessions[0], ["leak", "tidVol"]);
  for (const [key, unit, least] of [["leak", "L/min", 60], ["tidVol", "mL", 1000]]) {
    const converted = otherLoaded.signals[key];
    const asWritten = asWrittenLoaded.signals[key];
    expect("other-units: " + key + " is shown in " + unit, converted.unit, unit);
    expect("other-units: the card it came from says " + unit + " too", asWritten.unit, unit);
    expect("other-units: " + key + " keeps its sample count", converted.y.length, asWritten.y.length);
    let apart = 0;
    let highest = 0;
    for (let i = 0; i < converted.y.length; i++) {
      apart = Math.max(apart, Math.abs(converted.y[i] - asWritten.y[i]));
      highest = Math.max(highest, converted.y[i]);
    }
    expect("other-units: every " + key + " sample lands back on the figure it means",
      apart < 1e-6, true);
    // Without the conversion every sample would be low by exactly that factor, so
    // this is the assertion that fails if the conversion is taken out.
    expect("other-units: the highest " + key + " is a figure in " + unit, highest > least, true);
  }

  console.log("\n" + checks + " checks, " + bad.length + " failures");
  process.exitCode = bad.length ? 1 : 0;
})();
