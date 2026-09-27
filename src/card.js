"use strict";

// Reads a chosen folder as a PAP card: which of its files hold a night's recording,
// what session each belongs to, and which CPAP day that session began in. A file that
// is not matched here is never opened.
var PAPvaultCard = (function () {
  // yyyyMMdd_HHmmss_KIND.edf. A file is a night file by this name alone, wherever it
  // was handed over from: a whole card, one day's folder inside it, or a selection of
  // files with no folder at all.
  const NIGHT_FILE = /^(\d{8})_(\d{6})_([A-Za-z0-9]{3})\.edf$/;

  const SIGNAL_KINDS = ["BRP", "PLD", "SAD"];
  // The kinds a session's length is measured from. Oximetry is left out while it is
  // disabled, so an untested signal cannot decide how long a night was.
  const TIMING_KINDS = ["BRP", "PLD"];
  const EVENT_KINDS = ["EVE", "CSL"];

  // Annotations that mark where a recording begins or ends rather than something the
  // machine observed. PAPvault already knows both from each signal file's header, so
  // showing them again would put a session's own edges among its events. Matched on
  // the exact text, which a device set to another language would not write.
  const RECORDING_MARKERS = ["Recording starts", "Recording stops", "Recording ends"];

  // Two annotations that mark the two ends of one period, and the name the period
  // carries. The machine reports the time it saw the pattern rather than two moments,
  // so the pair is how a file writes one span, and the page draws one event across it.
  // Matched on the exact text a device set to another language would not write.
  const SPAN_EVENTS = [{ from: "CSR Start", to: "CSR End", text: "CSR" }];

  // A CPAP day runs from 6:00 on its date to 6:00 on the next calendar day. Every
  // other part of the page takes the boundary from here.
  const DAY_START_HOUR = 6;

  // A session that begins within this of the end of the one before it takes that
  // session's day rather than the day the boundary would give it.
  const DAY_BREAK_MINUTES = 60;

  // A session that begins at or after this hour takes the day the boundary gives it,
  // whatever came before it.
  const DAY_BREAK_BEFORE_HOUR = 12;

  // A session is a stretch of flow, and a cut in the flow longer than this begins a
  // new one. The file names say nothing about it: a machine writes a file for each
  // thing it records and does not stamp them all at one second.
  const SESSION_GAP_SECONDS = 5;
  // The kind of file the flow is in. Where a recording has none, its own span stands
  // in for the flow's.
  const FLOW_KIND = "BRP";

  // What each plot needs, and the labels a file may give it. The dotted forms are the
  // ones synthetic cards are written with and checked against. The short and translated
  // forms come from OSCAR's table of labels, cited in dev/formats/resmed.md, and no card
  // here has carried one. "Mask Pres" names different signals in BRP and in PLD, so a
  // label is only ever looked for inside its own kind of file.
  const SIGNALS = [
    { key: "flow", kind: "BRP", name: "Flow", labels: ["Flow.40ms", "Flow"] },
    { key: "flowPressure", kind: "BRP", name: "Mask Pressure", labels: ["Press.40ms", "Mask Pres"] },
    { key: "maskPressure", kind: "PLD", name: "Mask Pressure", labels: ["MaskPress.2s", "Mask Pres"] },
    { key: "pressure", kind: "PLD", name: "Pressure", labels: ["Press.2s", "Therapy Pres"] },
    { key: "eprPressure", kind: "PLD", name: "EPR Pressure", labels: ["EprPress.2s", "EPRPress.2s", "Exp Pres"] },
    { key: "leak", kind: "PLD", name: "Leak", perMinute: true, labels: ["Leak.2s", "Leak", "Leck", "Fuites", "Fuite", "Fuga", "Lekk"] },
    { key: "respRate", kind: "PLD", name: "Respiratory Rate", breaths: true, labels: ["RespRate.2s", "RR", "AF", "FR"] },
    { key: "minVent", kind: "PLD", name: "Minute Ventilation", labels: ["MinVent.2s", "MV", "VM"] },
    { key: "tidVol", kind: "PLD", name: "Tidal Volume", milliliters: true, labels: ["TidVol.2s", "Vt", "VC"] },
    { key: "snore", kind: "PLD", name: "Snore", labels: ["Snore.2s", "Snore"] },
    { key: "flowLim", kind: "PLD", name: "Flow Limitation", labels: ["FlowLim.2s", "FFL Index"] },
    { key: "pulse", kind: "SAD", name: "Pulse", labels: ["Pulse.1s", "Pulse", "Puls", "Pouls", "Pols", "Nabiz"] },
    { key: "spo2", kind: "SAD", name: "SpO2", labels: ["SpO2.1s", "SpO2"] },
  ];

  const SIGNAL_BY_KEY = new Map(SIGNALS.map(function (signal) {
    return [signal.key, signal];
  }));

  function cpapDayOf(instant) {
    const date = new Date(instant.getFullYear(), instant.getMonth(), instant.getDate());
    return instant.getHours() < DAY_START_HOUR
      ? new Date(date.getFullYear(), date.getMonth(), date.getDate() - 1)
      : date;
  }

  function cpapDayStart(day) {
    return new Date(day.getFullYear(), day.getMonth(), day.getDate(), DAY_START_HOUR);
  }

  function dayKey(day) {
    const pad = function (n) {
      return String(n).padStart(2, "0");
    };
    return day.getFullYear() + "-" + pad(day.getMonth() + 1) + "-" + pad(day.getDate());
  }

  // The moment a session stopped recording, which is where the break before the next
  // one is measured from. A session with no flow in it is timed by its files' span.
  function endOf(session) {
    return session.flowEnd || session.end;
  }

  // Whether a session takes the day of the one before it rather than the day the
  // boundary gives it.
  function carriesOn(session, before) {
    if (!before || session.start.getHours() >= DAY_BREAK_BEFORE_HOUR) {
      return false;
    }
    return session.start - endOf(before) <= DAY_BREAK_MINUTES * 60 * 1000;
  }

  // The day of every session, set in the order they ran, each one reading the day the
  // one before it was given.
  function daysOf(sessions) {
    let before = null;
    for (const session of sessions) {
      session.day = carriesOn(session, before) ? before.day : cpapDayOf(session.start);
      session.dayKey = dayKey(session.day);
      before = session;
    }
    return sessions;
  }

  // Whether a file holds a night's recording, by its name alone. Anything else on a
  // card -- its settings, its identification, its checksums -- fails this and is never
  // opened, so a folder can be listed and sorted before a single file is opened.
  function isNightFile(name) {
    return NIGHT_FILE.test(name);
  }

  // The files of a chosen folder that hold a night's recording, and nothing else.
  function nightFiles(items) {
    const found = [];
    for (const item of items) {
      const parts = item.path.split("/");
      const match = NIGHT_FILE.exec(parts[parts.length - 1]);
      if (!match) {
        continue;
      }
      found.push({
        file: item.file,
        path: item.path,
        stamp: match[1] + "_" + match[2],
        kind: match[3].toUpperCase(),
      });
    }
    return found;
  }

  // Enough of a file to hold the header of one declaring up to thirty-one signals,
  // which every file a supported machine writes is well inside. A file declaring more
  // is read a second time for the rest of its header.
  const HEADER_GUESS = 8192;

  async function headerOf(entry) {
    const guess = await entry.file.slice(0, HEADER_GUESS).arrayBuffer();
    const need = PAPvaultEDF.headerBytesOf(guess);
    const head = need <= guess.byteLength
      ? guess
      : await entry.file.slice(0, need).arrayBuffer();
    return PAPvaultEDF.parseHeader(head, entry.file.size);
  }

  // How many files are opened at once.
  const OPEN_AT_ONCE = 32;

  // Runs the work over every entry, OPEN_AT_ONCE of them in flight, and hands back
  // what each gave in the order the entries came in. An entry whose work threw carries
  // the reason instead, so one unreadable file does not take the rest with it.
  async function eachAtOnce(entries, work, onProgress) {
    const out = new Array(entries.length);
    let next = 0;
    let done = 0;
    if (onProgress) {
      onProgress(0, entries.length);
    }
    async function lane() {
      while (next < entries.length) {
        const mine = next;
        next += 1;
        try {
          out[mine] = { value: await work(entries[mine]) };
        } catch (error) {
          out[mine] = { why: error.message };
        }
        done += 1;
        if (onProgress) {
          onProgress(done, entries.length);
        }
      }
    }
    const lanes = [];
    for (let open = 0; open < Math.min(OPEN_AT_ONCE, entries.length); open++) {
      lanes.push(lane());
    }
    await Promise.all(lanes);
    return out;
  }

  // A session's times come from its flow and from nothing else, so a file the machine
  // stamped at some other hour cannot drag the session's start across the 6 o'clock
  // cut and move the whole night to the day before.
  function takeInto(session, recording) {
    session.stamps.push(recording.stamp);
    for (const file of recording.files) {
      session.files.push(file);
    }
    for (const kind of recording.kinds) {
      if (session.kinds.indexOf(kind) === -1) {
        session.kinds.push(kind);
      }
    }
    if (recording.flowStart === null) {
      return;
    }
    if (recording.start < session.start) {
      session.start = recording.start;
    }
    if (recording.end > session.end) {
      session.end = recording.end;
    }
    if (recording.flowEnd > session.flowEnd) {
      session.flowEnd = recording.flowEnd;
    }
  }

  // One session per stretch of flow, earliest first, and nothing else is a session.
  // A machine writes files when it is doing something other than recording a night --
  // being unplugged and plugged back in, sending its data somewhere -- and those
  // carry no flow. They join the session they fall inside, and are otherwise set
  // aside rather than counted as nights of their own.
  //
  // A card with no flow anywhere has nothing to measure against, so there every set
  // of files the machine stamped stands as its own session, as it did before.
  function sessionsFrom(recordings) {
    const order = recordings.slice().sort(function (a, b) {
      return a.start - b.start;
    });
    const flowing = order.filter(function (recording) {
      return recording.flowStart !== null;
    });
    const sessions = [];
    const aside = [];

    for (const recording of flowing.length ? flowing : order) {
      const open = sessions[sessions.length - 1];
      const from = open && endOf(open);
      const to = recording.flowStart || recording.start;
      if (open && to - from <= SESSION_GAP_SECONDS * 1000) {
        takeInto(open, recording);
        continue;
      }
      sessions.push({
        stamps: [recording.stamp],
        start: recording.start,
        end: recording.end,
        flowEnd: recording.flowEnd,
        files: recording.files.slice(),
        kinds: recording.kinds.slice(),
      });
    }

    // A set of files with no flow never makes a session of its own. It joins the
    // session it is nearest to in time, carrying whatever it holds, its events above
    // all. An event file declares no duration, so it stands at an instant and cannot
    // be placed by overlap.
    for (const recording of flowing.length ? order : []) {
      if (recording.flowStart !== null) {
        continue;
      }
      let home = null;
      let nearest = Infinity;
      for (const session of sessions) {
        const away = recording.start < session.start ? session.start - recording.start
          : (recording.start > session.end ? recording.start - session.end : 0);
        if (away < nearest) {
          nearest = away;
          home = session;
        }
      }
      takeInto(home, recording);
      if (nearest > SESSION_GAP_SECONDS * 1000) {
        aside.push(recording);
      }
    }

    // A session's files are read in the order its recordings ran, which is what lets
    // two files of one kind be carried on from one to the next.
    for (const session of sessions) {
      session.files.sort(function (a, b) {
        return a.header.start - b.header.start;
      });
    }
    sessions.sort(function (a, b) {
      return a.start - b.start;
    });
    return { sessions: sessions, aside: aside };
  }

  // Every session the card holds, earliest first. Which folder a file sits in decides
  // nothing: each file's own header says when it began.
  async function read(items, onProgress) {
    const entries = nightFiles(items);
    const recordings = new Map();
    const refused = [];

    const heads = await eachAtOnce(entries, headerOf, onProgress);

    for (let i = 0; i < entries.length; i++) {
      const entry = entries[i];
      if (heads[i].why) {
        refused.push({ path: entry.path, why: heads[i].why });
        continue;
      }
      const header = heads[i].value;
      if (header.interrupted && SIGNAL_KINDS.indexOf(entry.kind) !== -1) {
        refused.push({ path: entry.path, why: "its records are not continuous, which this page cannot time" });
        continue;
      }

      let recording = recordings.get(entry.stamp);
      if (!recording) {
        recording = { stamp: entry.stamp, start: header.start, end: header.start,
          flowStart: null, flowEnd: null, files: [], kinds: [] };
        recordings.set(entry.stamp, recording);
      }
      recording.files.push({ entry: entry, header: header });
      if (recording.kinds.indexOf(entry.kind) === -1) {
        recording.kinds.push(entry.kind);
      }
      if (header.start < recording.start) {
        recording.start = header.start;
      }
      // A signal file's header gives the recording's start, and its records give its stop.
      if (TIMING_KINDS.indexOf(entry.kind) !== -1) {
        const stop = new Date(header.start.getTime() + header.recordCount * header.recordSeconds * 1000);
        if (stop > recording.end) {
          recording.end = stop;
        }
        if (entry.kind === FLOW_KIND) {
          if (recording.flowStart === null || header.start < recording.flowStart) {
            recording.flowStart = header.start;
          }
          if (recording.flowEnd === null || stop > recording.flowEnd) {
            recording.flowEnd = stop;
          }
        }
      }
    }
    if (onProgress) {
      onProgress(entries.length, entries.length);
    }

    const built = sessionsFrom(Array.from(recordings.values()));
    daysOf(built.sessions);
    for (const session of built.sessions) {
      session.kinds.sort();
    }
    let asideFiles = 0;
    for (const recording of built.aside) {
      asideFiles += recording.files.length;
    }
    return { sessions: built.sessions, refused: refused, fileCount: entries.length,
      recordingCount: recordings.size, asideCount: built.aside.length, asideFiles: asideFiles };
  }

  // The sessions of each CPAP day, keyed by that day's date.
  function byDay(sessions) {
    const days = new Map();
    for (const session of sessions) {
      if (!days.has(session.dayKey)) {
        days.set(session.dayKey, []);
      }
      days.get(session.dayKey).push(session);
    }
    return days;
  }

  function wantedKinds(keys) {
    const kinds = [];
    for (const key of keys) {
      const signal = SIGNAL_BY_KEY.get(key);
      if (signal && kinds.indexOf(signal.kind) === -1) {
        kinds.push(signal.kind);
      }
    }
    return kinds;
  }

  // A unit written as liters per second, in the spellings a header may carry.
  const PER_SECOND = /^l\s*[\/p]?\s*(s|sec|second|sek)$/i;

  // EDF gives a signal's physical dimension eight bytes, so "breaths/min" cannot be
  // written in a header and a device writes "bpm", which reads as beats per minute.
  // A signal marked breaths is spelled out; only the spelling changes.
  const BREATHS = new Map([["bpm", "breaths/min"], ["1/min", "breaths/min"],
    ["b/min", "breaths/min"], ["br/min", "breaths/min"]]);

  function spelledOut(unit) {
    return BREATHS.get(String(unit).trim().toLowerCase()) || unit;
  }

  // A unit written as liters, in the spellings a header may carry.
  const LITERS = /^(l|lt|liter|litre|liters|litres)$/i;

  function scaledBy(factor, unit, values) {
    const scaled = new Float64Array(values.length);
    for (let i = 0; i < values.length; i++) {
      scaled[i] = values[i] * factor;
    }
    return { unit: unit, values: scaled };
  }

  // What a signal is shown in, which is not always what its file wrote it in. Each
  // rule reads the file's own unit and converts only from the one it names, so a file
  // already written in the unit shown is left alone. Nothing here changes a value's
  // meaning; a scale and a spelling are all that move.
  function asShown(wanted, unit, values) {
    const written = String(unit).trim();
    if (wanted.perMinute && PER_SECOND.test(written)) {
      return scaledBy(60, "L/min", values);
    }
    if (wanted.milliliters && LITERS.test(written)) {
      return scaledBy(1000, "mL", values);
    }
    if (wanted.breaths) {
      return { unit: spelledOut(unit), values: values };
    }
    return { unit: unit, values: values };
  }

  // A signal carried on across another file of the same kind. One session can hold
  // several recordings, and each writes its own file for the same signal; the files
  // are loaded in time order, so their samples follow one another.
  function joinSamples(held, times, values) {
    const x = new Float64Array(held.x.length + times.length);
    x.set(held.x, 0);
    x.set(times, held.x.length);
    const y = new Float64Array(held.y.length + values.length);
    y.set(held.y, 0);
    y.set(values, held.y.length);
    return {
      key: held.key,
      name: held.name,
      label: held.label,
      unit: held.unit,
      interval: held.interval,
      x: x,
      y: y,
    };
  }

  // Every event name anywhere on the card, in the order the sessions were read. The
  // annotation files are the small ones, so they are all opened when the card is
  // read rather than a name being discovered on whichever night happens to hold it.
  async function eventNames(sessions, onProgress) {
    const seen = [];
    const loaded = await eachAtOnce(sessions, function (session) {
      return load(session, []);
    }, onProgress);
    for (const one of loaded) {
      if (!one.value) {
        continue;
      }
      for (const event of one.value.events) {
        if (seen.indexOf(event.text) === -1) {
          seen.push(event.text);
        }
      }
    }
    return seen;
  }

  // One session's data: only the signals asked for, so a file no plot needs is
  // never opened. Times are in seconds, which is what the plots take.
  async function load(session, keys) {
    const kinds = wantedKinds(keys);
    const out = { signals: {}, events: [], missing: [], refused: [] };

    // The files this call needs, read together and taken in order afterwards.
    const needed = session.files.filter(function (held) {
      return EVENT_KINDS.indexOf(held.entry.kind) !== -1
        || kinds.indexOf(held.entry.kind) !== -1;
    });
    const buffers = await eachAtOnce(needed, function (held) {
      return held.entry.file.arrayBuffer();
    });

    for (let at = 0; at < needed.length; at++) {
      const held = needed[at];
      const kind = held.entry.kind;
      const isEvents = EVENT_KINDS.indexOf(kind) !== -1;
      if (buffers[at].why) {
        out.refused.push({ path: held.entry.path, why: "it could not be read" });
        continue;
      }
      const buffer = buffers[at].value;

      if (isEvents) {
        try {
          const read = PAPvaultEDF.readAnnotations(buffer, held.header);
          for (const event of read.events) {
            if (RECORDING_MARKERS.indexOf(event.text) !== -1) {
              continue;
            }
            // The onset is where the span stops, and the span reaches back its own
            // duration from there. A mark carrying no duration stands where it is.
            const ended = held.header.start.getTime() + event.onset * 1000;
            const at = new Date(ended - event.duration * 1000);
            out.events.push({
              text: event.text,
              start: at,
              seconds: at.getTime() / 1000,
              duration: event.duration,
              kind: kind,
            });
          }
        } catch (error) {
          out.refused.push({ path: held.entry.path, why: error.message });
        }
        continue;
      }

      for (const key of keys) {
        const wanted = SIGNAL_BY_KEY.get(key);
        if (!wanted || wanted.kind !== kind) {
          continue;
        }
        let signal = null;
        for (const label of wanted.labels) {
          signal = PAPvaultEDF.signalNamed(held.header, label);
          if (signal) {
            break;
          }
        }
        if (!signal) {
          continue;
        }
        try {
          const read = PAPvaultEDF.readSignal(buffer, held.header, signal);
          const shown = asShown(wanted, signal.unit, read);
          const values = shown.values;
          const interval = PAPvaultEDF.intervalOf(held.header, signal);
          const from = held.header.start.getTime() / 1000;
          const times = new Float64Array(values.length);
          for (let i = 0; i < values.length; i++) {
            times[i] = from + i * interval;
          }
          const already = out.signals[key];
          out.signals[key] = already ? joinSamples(already, times, values) : {
            key: key,
            name: wanted.name,
            label: signal.label,
            unit: shown.unit,
            interval: interval,
            x: times,
            y: values,
          };
        } catch (error) {
          out.refused.push({ path: held.entry.path, why: error.message });
        }
      }
    }

    for (const key of keys) {
      if (!out.signals[key]) {
        out.missing.push(key);
      }
    }
    out.events.sort(function (a, b) {
      return a.seconds - b.seconds;
    });
    out.events = foldSpans(out.events);
    return out;
  }

  // Each pair of marks becomes one event lasting from the first to the second. A mark
  // whose partner is missing -- a period still open when the recording stopped, or an
  // end with nothing before it -- is left exactly as the file wrote it.
  function foldSpans(events) {
    const opens = new Map();
    const closes = new Map();
    for (const span of SPAN_EVENTS) {
      opens.set(span.from, span);
      closes.set(span.to, span);
    }
    const out = [];
    const waiting = new Map();
    for (const event of events) {
      const opening = opens.get(event.text);
      if (opening) {
        if (waiting.has(opening.text)) {
          out.push(waiting.get(opening.text));
        }
        waiting.set(opening.text, event);
        continue;
      }
      const closing = closes.get(event.text);
      if (!closing) {
        out.push(event);
        continue;
      }
      const opened = waiting.get(closing.text);
      if (!opened) {
        out.push(event);
        continue;
      }
      waiting.delete(closing.text);
      out.push({
        text: closing.text,
        start: opened.start,
        seconds: opened.seconds,
        duration: Math.max(0, event.seconds - opened.seconds),
        kind: opened.kind,
        // The words the file actually carried, kept so nothing the device wrote is lost.
        wrote: [opened.text, event.text],
      });
    }
    for (const unclosed of waiting.values()) {
      out.push(unclosed);
    }
    out.sort(function (a, b) {
      return a.seconds - b.seconds;
    });
    return out;
  }

  return {
    read: read,
    load: load,
    isNightFile: isNightFile,
    eachAtOnce: eachAtOnce,
    eventNames: eventNames,
    byDay: byDay,
    cpapDayOf: cpapDayOf,
    cpapDayStart: cpapDayStart,
    daysOf: daysOf,
    dayKey: dayKey,
    signals: SIGNALS,
    DAY_START_HOUR: DAY_START_HOUR,
    DAY_BREAK_MINUTES: DAY_BREAK_MINUTES,
    DAY_BREAK_BEFORE_HOUR: DAY_BREAK_BEFORE_HOUR,
    RECORDING_MARKERS: RECORDING_MARKERS,
  };
})();
