// Builds a card whose leak signal goes on and off, so "how long the leak was above
// zero" has an answer that is not simply the whole recording.
//
// The synthetic cards carry a constant leak of 120 L/min, so every sample is above
// zero and the total necessarily equals the recorded time: a reader that ignored the
// values entirely would pass. This takes plain-night's PLD file and writes physical
// zero over a known set of leak samples, leaving a total known by construction.
//
//     node dev/tests/cards/make-gappy-leak.js <repo root> <out dir>
//
// It prints what it wrote and the total the page must then show.
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const ROOT = process.argv[2];
const OUT = process.argv[3];

const context = { TextDecoder, console };
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(ROOT, "src/edf.js"), "utf8"), context);
const EDF = context.PAPvaultEDF;

const CASE = path.join(ROOT, "dev/synthetic/out/resmed/plain-night");
// Every second run of samples is flattened, so the leak is on for one stretch and
// off for the next, and the answer is not one unbroken block either.
const KEEP_EVERY = 2;

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

const target = path.join(OUT, "gappy-leak");
fs.rmSync(target, { recursive: true, force: true });
copyTree(CASE, target);

let leakingSeconds = 0;
let flattened = 0;
for (const file of pldFiles(target, [])) {
  const bytes = fs.readFileSync(file);
  const buffer = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
  const header = EDF.parseHeader(buffer, bytes.length);
  const leak = EDF.signalNamed(header, "Leak.2s");
  if (!leak) {
    throw new Error("no Leak.2s in " + file);
  }
  const interval = EDF.intervalOf(header, leak);
  // Where this signal's samples sit inside one data record.
  let before = 0;
  for (const signal of header.signals) {
    if (signal.index === leak.index) {
      break;
    }
    before += signal.samplesPerRecord;
  }
  let recordSamples = 0;
  for (const signal of header.signals) {
    recordSamples += signal.samplesPerRecord;
  }
  const headerBytes = EDF.headerBytesOf(buffer);
  // The digital value that reads back as physical zero, through the file's own
  // calibration, rounded to the integer the file can actually hold.
  const span = (leak.physicalMax - leak.physicalMin) / (leak.digitalMax - leak.digitalMin);
  const zero = Math.round(leak.digitalMin + (0 - leak.physicalMin) / span);
  const view = new DataView(buffer);

  for (let record = 0; record < header.recordCount; record++) {
    for (let i = 0; i < leak.samplesPerRecord; i++) {
      const at = headerBytes + (record * recordSamples + before + i) * 2;
      if (record % KEEP_EVERY === 0) {
        leakingSeconds += interval;
      } else {
        view.setInt16(at, zero, true);
        flattened++;
      }
    }
  }
  fs.writeFileSync(file, Buffer.from(new Uint8Array(buffer)));
  const check = EDF.readSignal(buffer, header, leak);
  let above = 0;
  for (let i = 0; i < check.length; i++) {
    if (check[i] > 0) {
      above++;
    }
  }
  console.log(path.basename(file), "samples", check.length, "flattened", flattened,
    "still above zero", above, "interval", interval);
}

const minutes = Math.round(leakingSeconds / 60);
console.log("card written to", target);
console.log("leaking seconds by construction:", leakingSeconds,
  "-> the page must show", String(Math.floor(minutes / 60)).padStart(2, "0") + "h "
  + String(minutes % 60).padStart(2, "0") + "m");
