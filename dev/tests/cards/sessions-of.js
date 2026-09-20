// What src/card.js makes of a card: how many recordings it found, how many sessions
// those became, and what each session is made of.
//
//     node dev/tests/cards/sessions-of.js <repo root> <card dir> [expected session count]
//
// Built for the split cards, whose whole point is a card where the two counts differ.
const fs = require("fs"), path = require("path"), vm = require("vm");
const ROOT = process.argv[2], CARD = process.argv[3];
const WANT = process.argv[4] === undefined ? null : Number(process.argv[4]);

const context = { TextDecoder, console, Blob, Map, Set };
vm.createContext(context);
for (const f of ["src/edf.js", "src/card.js"]) {
  vm.runInContext(fs.readFileSync(path.join(ROOT, f), "utf8"), context);
}
const Card = context.PAPvaultCard;

const p = (n) => String(n).padStart(2, "0");
const clock = (d) => p(d.getHours()) + ":" + p(d.getMinutes()) + ":" + p(d.getSeconds());

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

(async function () {
  const read = await Card.read(itemsOf(CARD, path.basename(CARD) + "/"));
  console.log(path.basename(CARD) + ": " + read.recordingCount + " recording(s) -> "
    + read.sessions.length + " session(s), " + read.refused.length + " refused");
  for (const session of read.sessions) {
    console.log("  " + session.dayKey + "  " + clock(session.start) + " to " + clock(session.end)
      + "  kinds " + session.kinds.join(",") + "  from stamp(s) " + session.stamps.join(" + "));
  }
  if (WANT !== null) {
    const ok = read.sessions.length === WANT;
    console.log("  " + (ok ? "OK" : "WRONG") + ": wanted " + WANT + " session(s)");
    if (!ok) { process.exitCode = 1; }
  }
})();
