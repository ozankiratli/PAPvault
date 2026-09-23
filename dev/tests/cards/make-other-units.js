// Builds a card that records two signals in the other unit a machine might use: the
// leak in liters per second rather than per minute, and the tidal volume in liters
// rather than milliliters. The page converts both, so both conversions need a card
// that can fail on them.
//
//     node dev/tests/cards/make-other-units.js <repo root> <out dir>
//
// It takes on-and-off-leak and rewrites three header fields per signal: the unit, and
// the two ends of the physical range, divided by the same factor the page multiplies
// by. Not one data byte changes. So every sample means the same quantity in the other
// unit, and a reader that converts must arrive back at the numbers the original card
// holds, while a reader that does not will be low by exactly that factor.
//
// Z, 2026-09-22, on why the page converts at all: "We should convert our leak signal
// to L/min -> it is more readable. That's what people can understand", and then
// "Tidal volume: Card should display mL instead of L."
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const ROOT = process.argv[2];
const OUT = process.argv[3];

const context = { TextDecoder, console };
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(ROOT, "src/edf.js"), "utf8"), context);
const EDF = context.PAPvaultEDF;

const CASE = path.join(ROOT, "dev/synthetic/out/resmed/on-and-off-leak");
// The signal, the unit to write on it, and what its physical range is divided by.
const REWRITE = [
  { label: "Leak.2s", unit: "L/s", divide: 60 },
  { label: "TidVol.2s", unit: "L", divide: 1000 },
];

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

function pldFiles(dir, found) {
  for (const name of fs.readdirSync(dir)) {
    const full = path.join(dir, name);
    if (fs.statSync(full).isDirectory()) {
      pldFiles(full, found);
    } else if (name.endsWith("_PLD.edf")) {
      found.push(full);
    }
  }
  return found;
}

// Where a per-signal header field sits: 256 global bytes, then each field in turn,
// all of one field's values before the next begins.
function fieldAt(signals, index, before, width) {
  return 256 + before * signals + width * index;
}

function writeField(bytes, at, width, text) {
  if (text.length > width) {
    throw new Error("field too long: " + text);
  }
  bytes.write(text.padEnd(width, " "), at, width, "ascii");
}

const target = path.join(OUT, "other-units");
fs.rmSync(target, { recursive: true, force: true });
copyTree(CASE, target);

for (const file of pldFiles(target, [])) {
  const bytes = fs.readFileSync(file);
  const buffer = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
  const header = EDF.parseHeader(buffer, bytes.length);
  const signals = header.signals.length;
  for (const spec of REWRITE) {
    const signal = EDF.signalNamed(header, spec.label);
    if (!signal) {
      throw new Error("no " + spec.label + " in " + file);
    }
    const i = signal.index;
    writeField(bytes, fieldAt(signals, i, 96, 8), 8, spec.unit);
    writeField(bytes, fieldAt(signals, i, 104, 8), 8, String(signal.physicalMin / spec.divide));
    writeField(bytes, fieldAt(signals, i, 112, 8), 8, String(signal.physicalMax / spec.divide));
  }
  fs.writeFileSync(file, bytes);

  // Read it back through the parser, which is what the page will do.
  const again = fs.readFileSync(file);
  const check = EDF.parseHeader(again.buffer.slice(again.byteOffset,
    again.byteOffset + again.byteLength), again.length);
  for (const spec of REWRITE) {
    const changed = EDF.signalNamed(check, spec.label);
    console.log(path.basename(file), spec.label, "unit", JSON.stringify(changed.unit),
      "range", changed.physicalMin, "to", changed.physicalMax);
  }
}

console.log("card written to", target);
console.log("the page must show the same figures as on-and-off-leak, in L/min and mL");
