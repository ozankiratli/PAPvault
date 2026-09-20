#!/usr/bin/env python3
"""Build synthetic ResMed cards, and the answer each one must produce.

Written from formats/resmed.md and dev/synthetic/resmed-cases.md, and from
nothing else. Every fact about the card comes from the format file, which
cites the read it came from in dev/READING-LOG.md.

Run it:

    python3 dev/synthetic/resmed.py            # every case
    python3 dev/synthetic/resmed.py plain-night

Each case lands in dev/synthetic/out/resmed/<case>/, which git ignores,
holding a card and an answer.json. The answer is written from the values
used to build the card, never read back out of it: a check that compares
the generator with itself is not a check.

The data is not meant to look like a real night. Z tests realism against a
real card; these cases exist to exercise a reader and to carry an answer
that is known by construction.
"""

import argparse
import datetime
import json
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import edf

OUT = pathlib.Path(__file__).resolve().parents[2] / "dev" / "synthetic" / "out" / "resmed"

# The patient and recording fields carry this, so a check can fail if it ever
# reaches the page. Nothing in PAPvault may read, show or keep these fields.
MARKER = "SYNTHETIC-DO-NOT-DISPLAY-7Q4Z"
PATIENT_FIELD = f"{MARKER} X X {MARKER}_NAME"
RECORDING_FIELD = "Startdate X X X SRN={0}".format(MARKER)

RECORD_SECONDS = 60

# label, unit, physical range, and how many samples fall in one record.
# The labels are the form formats/resmed.md records for the 10 and 11 series;
# the units and the ranges are the generator's own choices.
BRP_SIGNALS = [
    ("Flow.40ms", "L/min", -120.0, 120.0, 1500),
    ("Press.40ms", "cmH2O", 0.0, 30.0, 1500),
]
PLD_SIGNALS = [
    ("MaskPress.2s", "cmH2O", 0.0, 30.0, 30),
    ("Press.2s", "cmH2O", 0.0, 30.0, 30),
    ("EprPress.2s", "cmH2O", 0.0, 30.0, 30),
    ("Leak.2s", "L/min", 0.0, 120.0, 30),
    ("RespRate.2s", "1/min", 0.0, 60.0, 30),
    ("TidVol.2s", "L", 0.0, 4.0, 30),
    ("MinVent.2s", "L/min", 0.0, 30.0, 30),
    ("Snore.2s", "", 0.0, 5.0, 30),
    ("FlowLim.2s", "", 0.0, 1.0, 30),
]
SAD_SIGNALS = [
    ("Pulse.1s", "bpm", 0.0, 200.0, 60),
    ("SpO2.1s", "%", 0.0, 100.0, 60),
]

DIGITAL_MIN = -32768
DIGITAL_MAX = 32767


def shape(name, index, count):
    """A plain, repeatable shape. Nothing here imitates a real signal."""
    turn = index / max(count, 1)
    if name == "sine":
        return math.sin(2 * math.pi * turn * 8)
    if name == "ramp":
        return turn
    if name == "square":
        return 1.0 if (index // 25) % 2 else 0.0
    return 0.0


def build_signal(label, unit, low, high, per_record, records, kind):
    count = per_record * records
    signal = edf.Signal(label, unit, low, high, DIGITAL_MIN, DIGITAL_MAX, per_record, [])
    middle = (low + high) / 2
    reach = (high - low) / 2 * 0.6
    samples = []
    for index in range(count):
        samples.append(signal.to_digital(middle + reach * shape(kind, index, per_record)))
    signal.samples = samples
    return signal


def cpap_day(moment):
    """The CPAP day a moment falls in: noon to noon, named by the date it began."""
    date = moment.date()
    if moment.hour < 12:
        date = date - datetime.timedelta(days=1)
    return date


def session_files(folder, start, minutes, events, csl_events, oximetry=True):
    """One session: the files a machine would leave for it, and what they hold."""
    records = minutes
    stamp = start.strftime("%Y%m%d_%H%M%S")
    written = {}

    brp = [build_signal(*spec, records, "sine") for spec in BRP_SIGNALS]
    edf.write(folder / f"{stamp}_BRP.edf", start, RECORD_SECONDS, brp,
              patient=PATIENT_FIELD, recording=RECORDING_FIELD)
    written["BRP"] = brp

    pld = [build_signal(*spec, records, "ramp") for spec in PLD_SIGNALS]
    edf.write(folder / f"{stamp}_PLD.edf", start, RECORD_SECONDS, pld,
              patient=PATIENT_FIELD, recording=RECORDING_FIELD)
    written["PLD"] = pld

    if oximetry:
        sad = [build_signal(*spec, records, "square") for spec in SAD_SIGNALS]
        edf.write(folder / f"{stamp}_SAD.edf", start, RECORD_SECONDS, sad,
                  patient=PATIENT_FIELD, recording=RECORDING_FIELD)
        written["SAD"] = sad

    edf.write(folder / f"{stamp}_EVE.edf", start, 0,
              annotations=[edf.Annotation(o, t, d) for o, t, d in events],
              n_records=1, record_event="Recording starts",
              patient=PATIENT_FIELD, recording=RECORDING_FIELD)
    edf.write(folder / f"{stamp}_CSL.edf", start, 0,
              annotations=[edf.Annotation(o, t, d) for o, t, d in csl_events],
              n_records=1, record_event="Recording starts",
              patient=PATIENT_FIELD, recording=RECORDING_FIELD)

    end = edf.ends_at(start, RECORD_SECONDS, records)
    answer = {
        "start": start.isoformat(),
        "end": end.isoformat(),
        "cpap_day": cpap_day(start).isoformat(),
        "kinds": sorted(list(written) + ["EVE", "CSL"]),
        "signals": {},
        "events": [{"text": t, "start": (start + datetime.timedelta(seconds=o)).isoformat(),
                    "duration": d} for o, t, d in events],
        "csl_events": [{"text": t, "start": (start + datetime.timedelta(seconds=o)).isoformat(),
                        "duration": d} for o, t, d in csl_events],
    }
    for kind, signals in written.items():
        for signal in signals:
            answer["signals"][signal.label] = {
                "kind": kind,
                "unit": signal.dimension,
                "seconds_between_samples": RECORD_SECONDS / signal.samples_per_record,
                "samples": len(signal.samples),
                "first_value": round(signal.to_physical(signal.samples[0]), 6),
                "value_at_100th": round(signal.to_physical(signal.samples[99]), 6),
                "last_value": round(signal.to_physical(signal.samples[-1]), 6),
            }
    return answer


def filler(card, day_folders):
    """The files PAPvault must never open. Their contents are meaningless."""
    (card / "STR.edf").write_bytes(b"not a real STR file, and nothing reads it\n")
    (card / "Journal.dat").write_bytes(b"not a real journal\n")
    (card / "Identification.tgt").write_text(f"#SRN {MARKER}\n", encoding="ascii")
    (card / "Identification.crc").write_text("0000\n", encoding="ascii")
    settings = card / "SETTINGS"
    settings.mkdir(exist_ok=True)
    (settings / "SET1.tgt").write_text("#SETTINGS not read\n", encoding="ascii")
    for folder in day_folders:
        for path in sorted(folder.glob("*.edf")):
            path.with_suffix(".crc").write_text("0000\n", encoding="ascii")


def case_plain_night(card):
    """One session, every kind of file, a few events at known times."""
    start = datetime.datetime(2026, 3, 10, 22, 30, 0)
    folder = card / "DATALOG" / cpap_day(start).strftime("%Y%m%d")
    events = [(600.0, "Synthetic event one", 12.0), (3600.0, "Synthetic event two", 25.5)]
    csl = [(1800.0, "Synthetic marker start", 0.0), (2400.0, "Synthetic marker end", 0.0)]
    session = session_files(folder, start, 480, events, csl)
    filler(card, [folder])
    return {
        "case": "plain-night",
        "what_it_exercises": "one session, all five kinds of file, events at known times",
        "cpap_days": {session["cpap_day"]: [session["start"]]},
        "sessions": [session],
        "identifying_marker": MARKER,
        "files_never_to_open": ["STR.edf", "Journal.dat", "Identification.tgt",
                                "Identification.crc", "SETTINGS/SET1.tgt", "*.crc"],
    }


def case_five_days(card):
    """Five CPAP days in a row, for a range selection and its summaries.

    The nights differ in when they start, how long they run, and what they
    hold, so a range is not five copies of one night. The third night has no
    oximetry, and the fourth is two sessions with a break between them.
    """
    nights = [
        # start, minutes, oximetry, events, csl markers
        (datetime.datetime(2026, 3, 10, 22, 30), 480, True,
         [(600.0, "Synthetic event one", 12.0), (7200.0, "Synthetic event two", 20.0)],
         [(3600.0, "Synthetic marker start", 0.0), (4500.0, "Synthetic marker end", 0.0)]),
        (datetime.datetime(2026, 3, 11, 23, 15), 390, True,
         [(1500.0, "Synthetic event one", 18.5)], []),
        (datetime.datetime(2026, 3, 12, 21, 50), 420, False,
         [(300.0, "Synthetic event two", 9.0), (5400.0, "Synthetic event one", 31.0)], []),
        (datetime.datetime(2026, 3, 13, 22, 5), 120, True, [], []),
        (datetime.datetime(2026, 3, 14, 1, 40), 300, True,
         [(2400.0, "Synthetic event one", 14.0)],
         [(60.0, "Synthetic marker start", 0.0)]),
        (datetime.datetime(2026, 3, 14, 23, 0), 450, True,
         [(900.0, "Synthetic event two", 22.0)], []),
    ]

    sessions = []
    folders = []
    for start, minutes, oximetry, events, csl in nights:
        folder = card / "DATALOG" / cpap_day(start).strftime("%Y%m%d")
        folders.append(folder)
        sessions.append(session_files(folder, start, minutes, events, csl, oximetry))

    days = {}
    for session in sessions:
        days.setdefault(session["cpap_day"], []).append(session["start"])

    filler(card, sorted(set(folders)))
    return {
        "case": "five-days",
        "what_it_exercises": "five CPAP days in a row, of different lengths, one without "
                             "oximetry, one made of two sessions, and one session that starts "
                             "after midnight and belongs to the day before",
        "cpap_days": days,
        "sessions": sessions,
        "identifying_marker": MARKER,
        "files_never_to_open": ["STR.edf", "Journal.dat", "Identification.tgt",
                                "Identification.crc", "SETTINGS/SET1.tgt", "*.crc"],
    }


CASES = {
    "plain-night": case_plain_night,
    "five-days": case_five_days,
}


def main():
    parser = argparse.ArgumentParser(description="Build synthetic ResMed cards.")
    parser.add_argument("cases", nargs="*", default=sorted(CASES), help="which cases to build")
    args = parser.parse_args()

    for name in args.cases:
        if name not in CASES:
            sys.exit(f"resmed: no case named {name!r}; known cases: {', '.join(sorted(CASES))}")
        card = OUT / name
        if card.exists():
            for path in sorted(card.rglob("*"), reverse=True):
                path.rmdir() if path.is_dir() else path.unlink()
        card.mkdir(parents=True, exist_ok=True)
        answer = CASES[name](card)
        (card / "answer.json").write_text(json.dumps(answer, indent=2, sort_keys=True) + "\n",
                                          encoding="utf-8")
        files = sum(1 for path in card.rglob("*") if path.is_file())
        print(f"{name}: {files} files in {card}")


if __name__ == "__main__":
    main()
