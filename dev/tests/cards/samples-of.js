// How many samples a session ends up with, which is what a session made of two
// recordings puts at risk: the second file's samples must be carried on, not dropped.
//
//     node dev/tests/cards/samples-of.js <repo root> <card dir>
const fs = require("fs"), path = require("path"), vm = require("vm");
const ROOT = process.argv[2], CARD = process.argv[3];
const context = { TextDecoder, console, Blob, Map, Set };
vm.createContext(context);
for (const f of ["src/edf.js", "src/card.js"]) {
  vm.runInContext(fs.readFileSync(path.join(ROOT, f), "utf8"), context);
}
const Card = context.PAPvaultCard;
function itemsOf(dir, prefix) {
  const out = [];
  for (const name of fs.readdirSync(dir)) {
    const full = path.join(dir, name);
    if (fs.statSync(full).isDirectory()) { out.push(...itemsOf(full, prefix + name + "/")); }
    else if (name !== "answer.json") { out.push({ file: new Blob([fs.readFileSync(full)]), path: prefix + name }); }
  }
  return out;
}
(async function () {
  const read = await Card.read(itemsOf(CARD, path.basename(CARD) + "/"));
  console.log(path.basename(CARD) + ": " + read.sessions.length + " session(s)");
  for (const session of read.sessions) {
    const loaded = await Card.load(session, ["pressure", "leak", "flow"]);
    const bits = [];
    for (const key of ["pressure", "leak", "flow"]) {
      const held = loaded.signals[key];
      bits.push(key + " " + (held ? held.y.length + " samples, " + (held.x[held.x.length - 1] - held.x[0]).toFixed(0) + "s span" : "none"));
    }
    console.log("  files " + session.files.length + ", events " + loaded.events.length + ", " + bits.join("; "));
  }
})();
