// Reads every synthetic ResMed card with src/edf.js and compares what it finds
// with the answer.json the generator wrote. Nothing here is shipped.
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const ROOT = process.argv[2];
const context = { TextDecoder, console };
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(ROOT, "src/edf.js"), "utf8"), context);
const EDF = context.PAPvaultEDF;

function localIso(d) {
  const p = (n) => String(n).padStart(2, "0");
  return d.getFullYear() + "-" + p(d.getMonth() + 1) + "-" + p(d.getDate())
    + "T" + p(d.getHours()) + ":" + p(d.getMinutes()) + ":" + p(d.getSeconds());
}

function bufferOf(file) {
  const b = fs.readFileSync(file);
  return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength);
}

let checks = 0, bad = 0;
function expect(what, got, want) {
  checks++;
  const ok = Math.abs(want) > 1e-9 && typeof got === "number"
    ? Math.abs(got - want) < 1e-4
    : got === want;
  if (!ok) { bad++; console.log("  MISMATCH " + what + "\n    got  " + got + "\n    want " + want); }
}

for (const caseName of fs.readdirSync(path.join(ROOT, "dev/synthetic/out/resmed")).sort()) {
  const dir = path.join(ROOT, "dev/synthetic/out/resmed", caseName);
  const answer = JSON.parse(fs.readFileSync(path.join(dir, "answer.json"), "utf8"));
  console.log("\n=== " + caseName + " ===");

  for (const session of answer.sessions) {
    const stamp = session.start.replace(/[-:]/g, "").replace("T", "_");
    const files = [];
    for (const day of fs.readdirSync(path.join(dir, "DATALOG"))) {
      for (const f of fs.readdirSync(path.join(dir, "DATALOG", day))) {
        if (f.startsWith(stamp) && f.endsWith(".edf")) {
          files.push(path.join(dir, "DATALOG", day, f));
        }
      }
    }
    expect(session.start + " file count", files.length, session.kinds.length);

    for (const file of files) {
      const kind = path.basename(file).split("_")[2].slice(0, 3);
      const header = EDF.parseHeader(bufferOf(file));
      expect(kind + " start", localIso(header.start), session.start);

      if (kind === "EVE" || kind === "CSL") {
        const want = kind === "EVE" ? session.events : session.csl_events;
        const got = EDF.readAnnotations(bufferOf(file), header).events;
        expect(kind + " event count", got.length, want.length);
        want.forEach((e, i) => {
          if (!got[i]) return;
          expect(kind + " event " + i + " text", got[i].text, e.text);
          expect(kind + " event " + i + " duration", got[i].duration, e.duration);
          const at = new Date(header.start.getTime() + got[i].onset * 1000);
          expect(kind + " event " + i + " start", localIso(at), e.start);
        });
        continue;
      }

      for (const [label, want] of Object.entries(session.signals)) {
        if (want.kind !== kind) continue;
        const signal = EDF.signalNamed(header, label);
        if (!signal) { checks++; bad++; console.log("  MISSING signal " + label); continue; }
        expect(label + " unit", signal.unit, want.unit);
        expect(label + " interval", EDF.intervalOf(header, signal), want.seconds_between_samples);
        const values = EDF.readSignal(bufferOf(file), header, signal);
        expect(label + " samples", values.length, want.samples);
        expect(label + " first", values[0], want.first_value);
        expect(label + " 100th", values[99], want.value_at_100th);
        expect(label + " last", values[values.length - 1], want.last_value);
      }
    }
  }

  // The marker in the identifying fields must never come back out of the reader.
  const marker = answer.identifying_marker;
  for (const day of fs.readdirSync(path.join(dir, "DATALOG"))) {
    for (const f of fs.readdirSync(path.join(dir, "DATALOG", day))) {
      if (!f.endsWith(".edf")) continue;
      const header = EDF.parseHeader(bufferOf(path.join(dir, "DATALOG", day, f)));
      checks++;
      if (JSON.stringify(header).includes(marker)) {
        bad++; console.log("  IDENTIFYING MARKER REACHED THE READER in " + f);
      }
    }
  }
}

console.log("\n" + checks + " checks, " + bad + " mismatches");
process.exit(bad === 0 ? 0 : 1);
