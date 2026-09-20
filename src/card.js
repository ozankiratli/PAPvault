"use strict";

// Reads a chosen folder as a PAP card: which of its files hold a night's recording,
// what session each belongs to, and which CPAP day that session began in. A file that
// is not matched here is never opened.
var PAPvaultCard = (function () {
  const DATA_FOLDER = "DATALOG";

  // yyyyMMdd_HHmmss_KIND.edf, two folders below the card's root: DATALOG/<day>/<file>.
  const NIGHT_FILE = /^(\d{8})_(\d{6})_([A-Za-z0-9]{3})\.edf$/;
  const FOLDERS_BELOW_DATALOG = 2;

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

  // A CPAP day runs from 6:00 on its date to 6:00 on the next calendar day. Every
  // other part of the page takes the boundary from here.
  const DAY_START_HOUR = 6;

  // A session is a stretch of flow, and a cut in the flow longer than this begins a
  // new one. The file names say nothing about it: a machine writes a file for each
  // thing it records and does not stamp them all at one second.
  const SESSION_GAP_SECONDS = 5;
  // The kind of file the flow is in. Where a recording has none, its own span stands
  // in for the flow's.
  const FLOW_KIND = "BRP";

  // What each plot needs, and the labels a file may give it. The dotted forms are the
  // ones synthetic cards are written with and checked against. The short and translated
  // forms come from OSCAR's table of labels, cited in formats/resmed.md, and no card
  // here has carried one. "Mask Pres" names different signals in BRP and in PLD, so a
  // label is only ever looked for inside its own kind of file.
  const SIGNALS = [
    { key: "flow", kind: "BRP", name: "Flow", labels: ["Flow.40ms", "Flow"] },
    { key: "flowPressure", kind: "BRP", name: "Mask Pressure", labels: ["Press.40ms", "Mask Pres"] },
    { key: "maskPressure", kind: "PLD", name: "Mask Pressure", labels: ["MaskPress.2s", "Mask Pres"] },
    { key: "pressure", kind: "PLD", name: "Pressure", labels: ["Press.2s", "Therapy Pres"] },
    { key: "eprPressure", kind: "PLD", name: "EPR Pressure", labels: ["EprPress.2s", "EPRPress.2s", "Exp Pres"] },
    { key: "leak", kind: "PLD", name: "Leak", labels: ["Leak.2s", "Leak", "Leck", "Fuites", "Fuite", "Fuga", "Lekk"] },
    { key: "respRate", kind: "PLD", name: "Respiratory Rate", labels: ["RespRate.2s", "RR", "AF", "FR"] },
    { key: "minVent", kind: "PLD", name: "Minute Ventilation", labels: ["MinVent.2s", "MV", "VM"] },
    { key: "tidVol", kind: "PLD", name: "Tidal Volume", labels: ["TidVol.2s", "Vt", "VC"] },
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

  // The files of a chosen folder that hold a night's recording, and nothing else.
  function nightFiles(items) {
    const found = [];
    for (const item of items) {
      const parts = item.path.split("/");
      const at = parts.lastIndexOf(DATA_FOLDER);
      if (at === -1 || at !== parts.length - 1 - FOLDERS_BELOW_DATALOG) {
        continue;
      }
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

  async function headerOf(entry) {
    const probe = await entry.file.slice(0, 256).arrayBuffer();
    const need = PAPvaultEDF.headerBytesOf(probe);
    const head = await entry.file.slice(0, need).arrayBuffer();
    return PAPvaultEDF.parseHeader(head, entry.file.size);
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
      const from = open && (open.flowEnd || open.end);
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
    // session it is nearest to in time, so nothing it holds -- its events above all --
    // is lost because the machine stamped it apart from the night it belongs to. An
    // event file declares no duration, so it stands at an instant and cannot be
    // placed by overlap.
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

    for (let i = 0; i < entries.length; i++) {
      const entry = entries[i];
      if (onProgress) {
        onProgress(i, entries.length);
      }
      let header;
      try {
        header = await headerOf(entry);
      } catch (error) {
        refused.push({ path: entry.path, why: error.message });
        continue;
      }
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
    for (const session of built.sessions) {
      session.day = cpapDayOf(session.start);
      session.dayKey = dayKey(session.day);
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

  // One session's data: only the signals asked for, so a file no plot needs is
  // never opened. Times are in seconds, which is what the plots take.
  async function load(session, keys) {
    const kinds = wantedKinds(keys);
    const out = { signals: {}, events: [], missing: [], refused: [] };

    for (const held of session.files) {
      const kind = held.entry.kind;
      const isEvents = EVENT_KINDS.indexOf(kind) !== -1;
      if (!isEvents && kinds.indexOf(kind) === -1) {
        continue;
      }
      let buffer;
      try {
        buffer = await held.entry.file.arrayBuffer();
      } catch (error) {
        out.refused.push({ path: held.entry.path, why: "it could not be read" });
        continue;
      }

      if (isEvents) {
        try {
          const read = PAPvaultEDF.readAnnotations(buffer, held.header);
          for (const event of read.events) {
            if (RECORDING_MARKERS.indexOf(event.text) !== -1) {
              continue;
            }
            const at = new Date(held.header.start.getTime() + event.onset * 1000);
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
          const values = PAPvaultEDF.readSignal(buffer, held.header, signal);
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
            unit: signal.unit,
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
    return out;
  }

  return {
    read: read,
    load: load,
    byDay: byDay,
    cpapDayOf: cpapDayOf,
    cpapDayStart: cpapDayStart,
    dayKey: dayKey,
    signals: SIGNALS,
    DAY_START_HOUR: DAY_START_HOUR,
    RECORDING_MARKERS: RECORDING_MARKERS,
  };
})();
