// Cards whose days the break rule decides, which no committed case has.
//
//     node dev/tests/cards/make-break-cards.js <repo root> <out dir>
//
// A session that begins within an hour of the end of the one before it takes that
// session's CPAP day however far past 6 in the morning it begins, down a chain, and
// never once it begins at noon. `dev/tests/day-boundary.js` exercises that rule at 33
// points, but it calls the reader's daysOf() with sessions it makes up in JavaScript:
// it opens no file, and it hands in the flowEnd the rule measures from. So two things
// stay out of its reach, and these two cards are those two things.
//
//   bathroom-break    five sessions, one 120-minute night's files stamped five times.
//                     Every one of them past the first is decided by the rule rather
//                     than by the 6 o'clock cut: three carry, the fourth carries at a
//                     minute to noon, and the fifth is stopped by having begun after
//                     it. Take the rule out and three of the five move to another day.
//                     The minute noon falls on is pinned to the second in
//                     day-boundary.js; what these prove is that both sides of it come
//                     out of real files.
//
//   break-from-flow   two sessions, the first with its flow stopping twelve minutes
//                     before its other files do. The second begins 64 minutes after
//                     the flow stopped and 52 after the files did, so the two moments
//                     give different days and the card says which one the rule uses.
//                     Nothing else here can tell them apart, because in every card the
//                     generator writes, the flow runs to the end of the session.
//
// What each session must land on is written below by construction, not worked out by
// a second copy of the rule. A check that computed the answer the way the reader does
// would agree with the reader whatever both of them did.
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
const RECORD_COUNT_AT = 236;
const HEADER_BYTES = 256;
const SIGNAL_HEADER_BYTES = 256;
const BYTES_PER_SAMPLE = 2;

const CASE = path.join(ROOT, "dev/synthetic/out/resmed/five-days");
// The shortest night five-days holds, and the only one carrying no events, so four
// copies of it do not put four copies of one event list on the card.
const SOURCE = { folder: "20260313", stamp: "20260313_220500", minutes: 120 };
const KINDS = ["BRP", "PLD", "SAD", "EVE", "CSL"];

const two = (value) => String(value).padStart(2, "0");

function stampOf(when) {
  return String(when.getFullYear()) + two(when.getMonth() + 1) + two(when.getDate())
    + "_" + two(when.getHours()) + two(when.getMinutes()) + two(when.getSeconds());
}

// The EDF start date and time, which are fixed-width ASCII fields.
function restamp(bytes, when) {
  bytes.write(two(when.getDate()) + "." + two(when.getMonth() + 1)
    + "." + two(when.getFullYear() % 100), START_DATE_AT, 8, "ascii");
  bytes.write(two(when.getHours()) + "." + two(when.getMinutes())
    + "." + two(when.getSeconds()), START_TIME_AT, 8, "ascii");
}

// Cuts a file down to the first `records` of its data, header and bytes together, so
// the file still adds up and the reader has no reason to refuse it.
function shorten(bytes, records) {
  const buffer = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
  const header = EDF.parseHeader(buffer, bytes.length);
  let perRecord = 0;
  for (const signal of header.signals) {
    perRecord += signal.samplesPerRecord * BYTES_PER_SAMPLE;
  }
  const headerBytes = HEADER_BYTES + header.signals.length * SIGNAL_HEADER_BYTES;
  bytes.write(String(records).padEnd(8, " "), RECORD_COUNT_AT, 8, "ascii");
  return bytes.subarray(0, headerBytes + records * perRecord);
}

// One session's files, copied from the source set and stamped at `when`. `flowRecords`
// cuts the flow file short; everything else keeps its whole length.
function writeSession(into, when, flowRecords) {
  const folder = path.join(into, "DATALOG", stampOf(when).slice(0, 8));
  fs.mkdirSync(folder, { recursive: true });
  for (const kind of KINDS) {
    const from = path.join(CASE, "DATALOG", SOURCE.folder, SOURCE.stamp + "_" + kind + ".edf");
    let bytes = fs.readFileSync(from);
    restamp(bytes, when);
    if (kind === "BRP" && flowRecords) {
      bytes = shorten(bytes, flowRecords);
    }
    fs.writeFileSync(path.join(folder, stampOf(when) + "_" + kind + ".edf"), bytes);
  }
}

function card(name, sessions) {
  const into = path.join(OUT, name);
  fs.rmSync(into, { recursive: true, force: true });
  fs.mkdirSync(into, { recursive: true });
  for (const one of sessions) {
    writeSession(into, one.start, one.flowRecords);
  }
  // The files PAPvault must never open, carried over so the card is a card.
  for (const spare of ["STR.edf", "Journal.dat", "Identification.tgt", "Identification.crc"]) {
    fs.copyFileSync(path.join(CASE, spare), path.join(into, spare));
  }
  return sessions;
}

const at = (text) => new Date(text.replace(" ", "T"));

// Every session is the same 120 minutes of recording, so each one ends two hours after
// it begins, and the gap named is measured from the end of the one before it.
const BATHROOM_BREAK = [
  // Begins before 6, so the cut alone puts it on the 13th. Ends 05:58.
  { start: at("2026-03-14 03:58:00"), day: "2026-03-13", why: "it began before 6" },
  // 22 minutes after that, and past 6. The break rule is the only thing that keeps it
  // on the 13th; the cut on its own would call it the 14th.
  { start: at("2026-03-14 06:20:00"), day: "2026-03-13", why: "a 22 minute break past 6" },
  // 45 minutes after the one before, at five past nine in the morning. It takes the
  // day the session before it was given, not the day its own clock reading gives.
  { start: at("2026-03-14 09:05:00"), day: "2026-03-13", why: "the chain, three deep" },
  // 54 minutes after the one before, and one minute short of the limit, so it carries
  // like the rest. This is the side of noon the rule exists for: a chain that began
  // the evening before is still the same day at a minute to twelve.
  { start: at("2026-03-14 11:59:00"), day: "2026-03-13", why: "a minute before noon, so the limit does not reach it" },
  // 31 minutes after the one before, which is well inside the hour. It begins in the
  // afternoon, and nothing carries once a session begins at noon or later.
  { start: at("2026-03-14 14:30:00"), day: "2026-03-14", why: "past noon, so the chain stops" },
];

// 120 minutes of files with 108 minutes of flow in them, so the session ends at 05:58
// and its flow stops at 05:46.
const FLOW_RECORDS = 108;
const BREAK_FROM_FLOW = [
  { start: at("2026-03-14 03:58:00"), day: "2026-03-13", flowRecords: FLOW_RECORDS,
    why: "it began before 6" },
  // 64 minutes after the flow stopped and 52 after the files did. Measured from the
  // flow it is too long a break to carry, so this session begins its own day.
  { start: at("2026-03-14 06:50:00"), day: "2026-03-14",
    why: "measured from the flow the break is 64 minutes, which is too long" },
];

card("bathroom-break", BATHROOM_BREAK);
card("break-from-flow", BREAK_FROM_FLOW);

fs.writeFileSync(path.join(OUT, "break-cards.json"), JSON.stringify({
  "bathroom-break": BATHROOM_BREAK.map((one) => ({ start: one.start.toISOString(),
    day: one.day, why: one.why })),
  "break-from-flow": BREAK_FROM_FLOW.map((one) => ({ start: one.start.toISOString(),
    day: one.day, why: one.why })),
  flowMinutes: FLOW_RECORDS,
  sessionMinutes: SOURCE.minutes,
}, null, 2) + "\n");
