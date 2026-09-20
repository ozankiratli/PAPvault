"use strict";

// Reads EDF and EDF+ files: bytes in, structure out. Nothing here touches the page.
// Every number a file declares is checked against the file's real length before it is
// used, so a file that does not add up is reported rather than read past its end.
var PAPvaultEDF = (function () {
  const HEADER_BYTES = 256;
  const SIGNAL_HEADER_BYTES = 256;
  const BYTES_PER_SAMPLE = 2;
  const ANNOTATION_LABEL = "EDF Annotations";

  // Separators inside a time-stamped annotation list.
  const ONSET_END = 0x14;
  const DURATION_MARK = 0x15;
  const LIST_END = 0x00;

  // Bytes 8 to 167 hold the patient and recording identification. No offset below
  // falls inside that range, and nothing here decodes it.
  const VERSION_AT = 0;
  const START_DATE_AT = 168;
  const START_TIME_AT = 176;
  const HEADER_LENGTH_AT = 184;
  const RESERVED_AT = 192;
  const RECORD_COUNT_AT = 236;
  const RECORD_SECONDS_AT = 244;
  const SIGNAL_COUNT_AT = 252;

  // Per-signal fields, in the order they appear, each repeated for every signal
  // before the next begins. Only the ones this reader uses are named.
  const SIGNAL_FIELDS = [
    { name: "label", width: 16 },
    { name: "transducer", width: 80 },
    { name: "unit", width: 8 },
    { name: "physicalMin", width: 8 },
    { name: "physicalMax", width: 8 },
    { name: "digitalMin", width: 8 },
    { name: "digitalMax", width: 8 },
    { name: "prefiltering", width: 80 },
    { name: "samplesPerRecord", width: 8 },
    { name: "reserved", width: 32 },
  ];

  const decoder = new TextDecoder("utf-8");

  function fail(message) {
    throw new Error(message);
  }

  // Header text is padded with spaces. It is decoded as UTF-8 rather than ASCII
  // because a device may write bytes the specification does not allow.
  function text(bytes, at, width) {
    return decoder.decode(bytes.subarray(at, at + width)).trim();
  }

  function number(bytes, at, width, what) {
    const raw = text(bytes, at, width);
    const value = Number(raw);
    if (raw === "" || !Number.isFinite(value)) {
      fail(what + " is not a number");
    }
    return value;
  }

  function wholeNumber(bytes, at, width, what) {
    const value = number(bytes, at, width, what);
    if (!Number.isInteger(value)) {
      fail(what + " is not a whole number");
    }
    return value;
  }

  // Years 85 to 99 mean 1985 to 1999; 00 to 84 mean 2000 to 2084.
  function startOf(dateText, timeText) {
    const date = /^(\d\d)\.(\d\d)\.(\d\d)$/.exec(dateText);
    const time = /^(\d\d)\.(\d\d)\.(\d\d)$/.exec(timeText);
    if (!date || !time) {
      fail("the start date or start time is not in the form the format requires");
    }
    const twoDigitYear = Number(date[3]);
    const year = twoDigitYear >= 85 ? 1900 + twoDigitYear : 2000 + twoDigitYear;
    const day = Number(date[1]);
    const month = Number(date[2]);
    const start = new Date(year, month - 1, day, Number(time[1]), Number(time[2]), Number(time[3]));
    if (start.getDate() !== day || start.getMonth() !== month - 1) {
      fail("the start date is not a date that exists");
    }
    return start;
  }

  function readSignalHeaders(bytes, signalCount) {
    const signals = [];
    for (let i = 0; i < signalCount; i++) {
      signals.push({ index: i });
    }
    let at = HEADER_BYTES;
    for (const field of SIGNAL_FIELDS) {
      for (const signal of signals) {
        signal[field.name] = text(bytes, at, field.width);
        at += field.width;
      }
    }
    return signals;
  }

  function checkSignal(signal) {
    const where = "signal " + (signal.index + 1);
    for (const field of ["physicalMin", "physicalMax", "digitalMin", "digitalMax", "samplesPerRecord"]) {
      const value = Number(signal[field]);
      if (signal[field] === "" || !Number.isFinite(value)) {
        fail(where + " declares a " + field + " that is not a number");
      }
      signal[field] = value;
    }
    if (!Number.isInteger(signal.samplesPerRecord) || signal.samplesPerRecord < 0) {
      fail(where + " declares a sample count per record that is not a whole number at least zero");
    }
    if (signal.digitalMax <= signal.digitalMin) {
      fail(where + " declares a digital maximum that is not above its digital minimum");
    }
    if (signal.physicalMax === signal.physicalMin) {
      fail(where + " declares a physical maximum equal to its physical minimum");
    }
    signal.isAnnotations = signal.label === ANNOTATION_LABEL;
    signal.bytesPerRecord = signal.samplesPerRecord * BYTES_PER_SAMPLE;
  }

  // The header as the file declares it, checked against how long the file actually is.
  // fileBytes is how long the whole file is, for a buffer holding only its header;
  // leaving it out takes the buffer for the whole file.
  function parseHeader(buffer, fileBytes) {
    const size = fileBytes === undefined ? buffer.byteLength : fileBytes;
    if (buffer.byteLength < HEADER_BYTES || size < HEADER_BYTES) {
      fail("the file is shorter than an EDF header");
    }
    const bytes = new Uint8Array(buffer);

    const signalCount = wholeNumber(bytes, SIGNAL_COUNT_AT, 4, "the number of signals");
    if (signalCount < 1) {
      fail("the file declares no signals");
    }
    const declaredHeaderBytes = wholeNumber(bytes, HEADER_LENGTH_AT, 8, "the header length");
    const headerBytes = HEADER_BYTES + signalCount * SIGNAL_HEADER_BYTES;
    if (declaredHeaderBytes !== headerBytes) {
      fail("the header length, " + declaredHeaderBytes + " bytes, disagrees with the "
        + signalCount + " signals it declares, which need " + headerBytes);
    }
    if (size < headerBytes || buffer.byteLength < headerBytes) {
      fail("the file is shorter than the header it declares");
    }

    const recordSeconds = number(bytes, RECORD_SECONDS_AT, 8, "the duration of a data record");
    if (recordSeconds < 0) {
      fail("the duration of a data record is negative");
    }

    const signals = readSignalHeaders(bytes, signalCount);
    signals.forEach(checkSignal);

    let recordBytes = 0;
    for (const signal of signals) {
      signal.byteOffsetInRecord = recordBytes;
      recordBytes += signal.bytesPerRecord;
    }
    if (recordBytes === 0) {
      fail("the file declares data records that hold no samples");
    }

    const dataBytes = size - headerBytes;
    let recordCount = wholeNumber(bytes, RECORD_COUNT_AT, 8, "the number of data records");
    if (recordCount < 0) {
      // A file still being recorded may declare -1; how long it is then says how many it holds.
      recordCount = Math.floor(dataBytes / recordBytes);
    }
    const needed = recordCount * recordBytes;
    if (needed > dataBytes) {
      fail("the file declares " + recordCount + " data records, which need " + needed
        + " bytes, but only " + dataBytes + " bytes follow its header");
    }

    // In an interrupted file the records are not contiguous, so a sample's offset in
    // the file is not its offset in time. Whoever reads the samples has to know.
    const reserved = text(bytes, RESERVED_AT, 44);

    return {
      version: text(bytes, VERSION_AT, 8),
      start: startOf(text(bytes, START_DATE_AT, 8), text(bytes, START_TIME_AT, 8)),
      reserved: reserved,
      interrupted: reserved.slice(0, 5) === "EDF+D",
      headerBytes: headerBytes,
      recordCount: recordCount,
      recordSeconds: recordSeconds,
      recordBytes: recordBytes,
      signals: signals,
      byteLength: size,
    };
  }

  // How many bytes of a file its header takes up, read from the first 256 of it, so
  // that a waveform file need not be loaded whole to find out when it started.
  function headerBytesOf(buffer) {
    if (buffer.byteLength < HEADER_BYTES) {
      fail("the file is shorter than an EDF header");
    }
    const count = wholeNumber(new Uint8Array(buffer), SIGNAL_COUNT_AT, 4, "the number of signals");
    if (count < 1) {
      fail("the file declares no signals");
    }
    return HEADER_BYTES + count * SIGNAL_HEADER_BYTES;
  }

  // Seconds between one sample of this signal and the next.
  function intervalOf(header, signal) {
    if (signal.samplesPerRecord === 0) {
      fail("signal " + (signal.index + 1) + " holds no samples per record");
    }
    return header.recordSeconds / signal.samplesPerRecord;
  }

  function signalNamed(header, label) {
    return header.signals.find(function (signal) {
      return signal.label === label;
    }) || null;
  }

  // Every sample of one signal, converted to its physical value, in file order.
  function readSignal(buffer, header, signal) {
    if (signal.isAnnotations) {
      fail("signal " + (signal.index + 1) + " holds annotations, not samples");
    }
    const total = header.recordCount * signal.samplesPerRecord;
    const values = new Float64Array(total);
    const view = new DataView(buffer);
    const span = signal.physicalMax - signal.physicalMin;
    const range = signal.digitalMax - signal.digitalMin;
    const gain = span / range;
    let out = 0;
    for (let record = 0; record < header.recordCount; record++) {
      let at = header.headerBytes + record * header.recordBytes + signal.byteOffsetInRecord;
      for (let i = 0; i < signal.samplesPerRecord; i++) {
        values[out++] = signal.physicalMin + (view.getInt16(at, true) - signal.digitalMin) * gain;
        at += BYTES_PER_SAMPLE;
      }
    }
    return values;
  }

  // One time-stamped annotation list: an onset, an optional duration, then its texts.
  function parseList(bytes, from, to, where) {
    const parts = [];
    let start = from;
    for (let at = from; at < to; at++) {
      if (bytes[at] === ONSET_END) {
        parts.push(bytes.subarray(start, at));
        start = at + 1;
      }
    }
    if (parts.length === 0) {
      fail(where + " holds an annotation list with no onset");
    }
    const stamp = decoder.decode(parts[0]);
    const split = stamp.indexOf(String.fromCharCode(DURATION_MARK));
    const onsetText = split === -1 ? stamp : stamp.slice(0, split);
    const durationText = split === -1 ? "" : stamp.slice(split + 1);
    if (!/^[+-]\d+(\.\d+)?$/.test(onsetText)) {
      fail(where + " holds an annotation list whose onset is not a signed number");
    }
    if (durationText !== "" && !/^\d+(\.\d+)?$/.test(durationText)) {
      fail(where + " holds an annotation list whose duration is not a number");
    }
    const onset = Number(onsetText);
    const duration = durationText === "" ? 0 : Number(durationText);
    const events = [];
    for (let i = 1; i < parts.length; i++) {
      const written = decoder.decode(parts[i]);
      if (written !== "") {
        events.push({ onset: onset, duration: duration, text: written });
      }
    }
    return { onset: onset, events: events };
  }

  // Every event in the file, in file order, and the start each record declares.
  //
  // The first list in each data record is time keeping: its onset is that record's
  // start, and in a file with no ordinary signals its text names what begins the
  // record rather than an event at a time. So no event is taken from it.
  function readAnnotations(buffer, header) {
    const bytes = new Uint8Array(buffer);
    const events = [];
    const recordStarts = [];
    for (const signal of header.signals) {
      if (!signal.isAnnotations) {
        continue;
      }
      for (let record = 0; record < header.recordCount; record++) {
        const from = header.headerBytes + record * header.recordBytes + signal.byteOffsetInRecord;
        const to = from + signal.bytesPerRecord;
        const where = "data record " + (record + 1);
        let at = from;
        let first = true;
        while (at < to) {
          if (bytes[at] === LIST_END) {
            at++;
            continue;
          }
          let end = at;
          while (end < to && bytes[end] !== LIST_END) {
            end++;
          }
          if (end === to) {
            fail(where + " holds an annotation list that runs past the end of the record");
          }
          const list = parseList(bytes, at, end, where);
          if (first) {
            recordStarts.push(list.onset);
            first = false;
          } else {
            for (const event of list.events) {
              events.push(event);
            }
          }
          at = end + 1;
        }
        if (first) {
          fail(where + " holds no time-keeping annotation");
        }
      }
    }
    return { events: events, recordStarts: recordStarts };
  }

  return {
    parseHeader: parseHeader,
    headerBytesOf: headerBytesOf,
    readSignal: readSignal,
    readAnnotations: readAnnotations,
    intervalOf: intervalOf,
    signalNamed: signalNamed,
    ANNOTATION_LABEL: ANNOTATION_LABEL,
  };
})();
