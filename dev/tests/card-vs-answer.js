// Reads every synthetic card through src/card.js exactly as the page does, and
// compares sessions, CPAP days and loaded signals with the generator's answer.json.
const fs = require("fs"), path = require("path"), vm = require("vm");
const ROOT = process.argv[2];
const context = { TextDecoder, console, Blob, Map, Set };
vm.createContext(context);
for (const f of ["src/edf.js", "src/card.js"]) {
  vm.runInContext(fs.readFileSync(path.join(ROOT, f), "utf8"), context);
}
const Card = context.PAPvaultCard;

const p = (n) => String(n).padStart(2, "0");
const iso = (d) => d.getFullYear() + "-" + p(d.getMonth() + 1) + "-" + p(d.getDate())
  + "T" + p(d.getHours()) + ":" + p(d.getMinutes()) + ":" + p(d.getSeconds());

let checks = 0, bad = 0;
function expect(what, got, want) {
  checks++;
  const ok = typeof want === "number" && typeof got === "number"
    ? Math.abs(got - want) < 1e-4 : got === want;
  if (!ok) { bad++; console.log("  MISMATCH " + what + "\n    got  " + got + "\n    want " + want); }
}

// Every file under the card, as the folder picker hands them over.
function itemsOf(dir, prefix) {
  const out = [];
  for (const name of fs.readdirSync(dir)) {
    const full = path.join(dir, name);
    if (fs.statSync(full).isDirectory()) { out.push(...itemsOf(full, prefix + name + "/")); }
    else { out.push({ file: new Blob([fs.readFileSync(full)]), path: prefix + name }); }
  }
  return out;
}

(async function () {
for (const caseName of fs.readdirSync(path.join(ROOT, "dev/synthetic/out/resmed")).sort()) {
  const dir = path.join(ROOT, "dev/synthetic/out/resmed", caseName);
  const answer = JSON.parse(fs.readFileSync(path.join(dir, "answer.json"), "utf8"));
  console.log("\n=== " + caseName + " ===");

  const read = await Card.read(itemsOf(dir, caseName + "/"));
  expect("sessions found", read.sessions.length, answer.sessions.length);
  expect("files refused", read.refused.length, 0);

  const days = Card.byDay(read.sessions);
  expect("days found", days.size, Object.keys(answer.cpap_days).length);
  for (const [day, starts] of Object.entries(answer.cpap_days)) {
    const held = days.get(day) || [];
    expect("day " + day + " session count", held.length, starts.length);
    starts.forEach((s, i) => held[i] && expect("day " + day + " session " + i, iso(held[i].start), s));
  }

  for (let i = 0; i < answer.sessions.length; i++) {
    const want = answer.sessions[i], got = read.sessions[i];
    if (!got) continue;
    expect("session " + i + " start", iso(got.start), want.start);
    expect("session " + i + " end", iso(got.end), want.end);
    expect("session " + i + " cpap day", got.dayKey, want.cpap_day);
    expect("session " + i + " kinds", got.kinds.join(","), want.kinds.slice().sort().join(","));

    // Load every signal the card offers, and check the ones the answer names.
    const keys = Card.signals.map((s) => s.key);
    const data = await Card.load(got, keys);
    expect("session " + i + " load refused", data.refused.length, 0);

    const byLabel = {};
    for (const key of Object.keys(data.signals)) { byLabel[data.signals[key].label] = data.signals[key]; }
    for (const [label, spec] of Object.entries(want.signals)) {
      const s = byLabel[label];
      checks++;
      if (!s) { bad++; console.log("  MISSING loaded signal " + label); continue; }
      expect(label + " unit", s.unit, spec.unit);
      expect(label + " interval", s.interval, spec.seconds_between_samples);
      expect(label + " samples", s.y.length, spec.samples);
      expect(label + " first", s.y[0], spec.first_value);
      expect(label + " last", s.y[s.y.length - 1], spec.last_value);
      // A sample's time is its file's start plus its offset in the file.
      expect(label + " first time", iso(new Date(s.x[0] * 1000)), want.start);
      expect(label + " last time", iso(new Date(s.x[s.x.length - 1] * 1000)),
        iso(new Date(new Date(want.start).getTime() + (spec.samples - 1) * spec.seconds_between_samples * 1000)));
    }

    const wantEvents = [...(want.events || []), ...(want.csl_events || [])]
      .sort((a, b) => new Date(a.start) - new Date(b.start));
    expect("session " + i + " event count", data.events.length, wantEvents.length);
    wantEvents.forEach((e, j) => {
      if (!data.events[j]) return;
      expect("event " + j + " text", data.events[j].text, e.text);
      expect("event " + j + " start", iso(data.events[j].start), e.start);
      expect("event " + j + " duration", data.events[j].duration, e.duration);
    });

    checks++;
    if (JSON.stringify(data.signals) .includes(answer.identifying_marker)
      || JSON.stringify(data.events).includes(answer.identifying_marker)) {
      bad++; console.log("  IDENTIFYING MARKER REACHED THE LOADED DATA");
    }
  }
}
console.log("\n" + checks + " checks, " + bad + " mismatches");
process.exit(bad === 0 ? 0 : 1);
})();
