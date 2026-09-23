#!/usr/bin/env python3
"""Build synthetic ResMed cards, and the answer each one must produce.

Written from dev/formats/resmed.md and dev/synthetic/resmed-cases.md, and from
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
# The labels are the form dev/formats/resmed.md records for the 10 and 11 series;
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
    ("RespRate.2s", "bpm", 0.0, 60.0, 30),
    ("TidVol.2s", "mL", 0.0, 4000.0, 30),
    ("MinVent.2s", "L/min", 0.0, 30.0, 30),
    ("Snore.2s", "", 0.0, 5.0, 30),
    ("FlowLim.2s", "", 0.0, 1.0, 30),
]
SAD_SIGNALS = [
    ("Pulse.1s", "bpm", 0.0, 200.0, 60),
    ("SpO2.1s", "%", 0.0, 100.0, 60),
]

# The signal the leak figures are taken from, which one case builds run by run.
LEAK_LABEL = "Leak.2s"

# What a reader must show, per signal, where a file cannot spell the unit out. EDF
# gives the physical dimension eight bytes (dev/formats/resmed.md, R-001), so
# "breaths/min" does not fit in a header and a device writes "bpm" instead, which
# reads as beats per minute. Z, 2026-09-22: "bpm is understood as beats per minute.
# lets change it to breaths/min". Keyed by label and not by unit, because Pulse.1s
# writes "bpm" as well and there it means exactly what it says. The answer carries
# both, so the parser can be checked against what the file holds and the page against
# what it must put on screen.
SHOWN_UNITS = {"RespRate.2s": "breaths/min"}

# Two annotations a device writes to mark one period, and the one event PAPvault
# draws across it (Z, 2026-09-22: "Let's convert CSR into a single event line, where
# it spans the time between its start and end"). The answer carries both what the
# file holds and what the page must show, so each can be checked against its own.
SPAN_EVENTS = [("CSR Start", "CSR End", "CSR")]


def shown_events(events):
    """The events a correct reader draws, with each pair of marks folded into one."""
    opens = {span[0]: span for span in SPAN_EVENTS}
    closes = {span[1]: span for span in SPAN_EVENTS}
    out = []
    waiting = {}
    for event in sorted(events, key=lambda one: one["start"]):
        if event["text"] in opens:
            span = opens[event["text"]]
            if span[2] in waiting:
                out.append(waiting.pop(span[2]))
            waiting[span[2]] = event
            continue
        if event["text"] in closes:
            span = closes[event["text"]]
            if span[2] not in waiting:
                out.append(event)
                continue
            began = waiting.pop(span[2])
            start = datetime.datetime.fromisoformat(began["start"])
            end = datetime.datetime.fromisoformat(event["start"])
            out.append({"text": span[2], "start": began["start"],
                        "duration": (end - start).total_seconds()})
            continue
        out.append(event)
    out.extend(waiting.values())
    return sorted(out, key=lambda one: one["start"])


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


def build_runs(label, unit, low, high, per_record, records, runs):
    """A signal held at one value for a run at a time: (how many samples, the value)."""
    signal = edf.Signal(label, unit, low, high, DIGITAL_MIN, DIGITAL_MAX, per_record, [])
    samples = []
    for count, value in runs:
        samples.extend([signal.to_digital(value)] * count)
    if len(samples) != per_record * records:
        raise ValueError(f"{label}: the runs give {len(samples)} samples, "
                         f"and {records} records hold {per_record * records}")
    signal.samples = samples
    return signal


def above_zero(signal, runs=None):
    """How long the signal ran above zero, and each run that did, from where it was built.

    The times follow the rule Z set on 2026-09-20: a run lasts from the sample before
    it to the sample after it, less one step, which is its own samples times the step.
    When the runs that built the signal are given, what they asked for and what the
    calibration could carry must agree, or a run asked for above zero that landed on
    zero would go unnoticed.
    """
    step = RECORD_SECONDS / signal.samples_per_record
    physical = [signal.to_physical(sample) for sample in signal.samples]
    counted = sum(1 for value in physical if value > 0)
    stretches = []
    at = 0
    while at < len(physical):
        end = at
        while end < len(physical) and (physical[end] > 0) == (physical[at] > 0):
            end += 1
        if physical[at] > 0:
            stretches.append((at * step, (end - at) * step, round(physical[at], 6)))
        at = end
    if runs is not None:
        asked = sum(count for count, value in runs if value > 0)
        if asked != counted:
            raise ValueError(f"{signal.label}: {asked} samples were asked for above zero "
                             f"and {counted} of them are, so a run rounded to zero")
        if len(stretches) != sum(1 for count, value in runs if value > 0 and count):
            raise ValueError(f"{signal.label}: two runs above zero were asked for with "
                             f"nothing between them, so they came out as one")
    return round(counted * step, 6), stretches


# The hour a CPAP day begins on its own date, and so the hour the next day takes over.
# It was 12 until Z moved it to 6 on 2026-09-19, so that a nap starting after 6 in the
# morning belongs to that morning's day rather than to the night before. Every case
# below has its sessions starting in the evening or between midnight and 6, which both
# rules put in the same day, so no answer.json changed when this moved. A case that
# would tell the two apart needs a session starting between 6 and noon; see
# resmed-cases.md, where morning-nap is proposed for exactly that.
DAY_START_HOUR = 6


def cpap_day(moment):
    """The CPAP day a moment falls in: DAY_START_HOUR to DAY_START_HOUR, named by the date it began."""
    date = moment.date()
    if moment.hour < DAY_START_HOUR:
        date = date - datetime.timedelta(days=1)
    return date


def session_files(folder, start, minutes, events, csl_events, oximetry=True, leak_runs=None):
    """One session: the files a machine would leave for it, and what they hold.

    leak_runs replaces the leak's ramp with runs of one value each, for the case whose
    leak goes on and off.
    """
    records = minutes
    stamp = start.strftime("%Y%m%d_%H%M%S")
    written = {}

    brp = [build_signal(*spec, records, "sine") for spec in BRP_SIGNALS]
    edf.write(folder / f"{stamp}_BRP.edf", start, RECORD_SECONDS, brp,
              patient=PATIENT_FIELD, recording=RECORDING_FIELD)
    written["BRP"] = brp

    pld = []
    for spec in PLD_SIGNALS:
        if leak_runs is not None and spec[0] == LEAK_LABEL:
            pld.append(build_runs(*spec, records, leak_runs))
        else:
            pld.append(build_signal(*spec, records, "ramp"))
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
    answer["shown_events"] = shown_events(answer["events"] + answer["csl_events"])
    for kind, signals in written.items():
        for signal in signals:
            answer["signals"][signal.label] = {
                "kind": kind,
                "unit": signal.dimension,
                "unit_shown": SHOWN_UNITS.get(signal.label, signal.dimension),
                "seconds_between_samples": RECORD_SECONDS / signal.samples_per_record,
                "samples": len(signal.samples),
                "first_value": round(signal.to_physical(signal.samples[0]), 6),
                "value_at_100th": round(signal.to_physical(signal.samples[99]), 6),
                "last_value": round(signal.to_physical(signal.samples[-1]), 6),
            }

    leak = next(signal for signal in pld if signal.label == LEAK_LABEL)
    seconds, stretches = above_zero(leak, leak_runs)
    answer["leak_above_zero_seconds"] = seconds
    if leak_runs is not None:
        answer["leak_runs"] = [
            {"start": (start + datetime.timedelta(seconds=at)).isoformat(),
             "seconds": length, "value": value} for at, length, value in stretches]
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
    # A period marked by two annotations, which the page draws as one event spanning
    # the 600 seconds between them.
    csl = [(1800.0, "CSR Start", 0.0), (2400.0, "CSR End", 0.0)]
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


# The leak of on-and-off-leak, run by run, as (how long in seconds, L/min). The runs
# differ in length and in level, so a wrong reading cannot land on the right total; one
# is low enough to catch a threshold nobody asked for; the night begins at zero; and
# the last run reaches the end of the recording, where there is no sample after it.
ON_AND_OFF_LEAK = [
    (600, 0.0), (300, 30.0), (90, 0.0), (1200, 60.0), (2400, 0.0), (180, 0.5),
    (1770, 0.0), (4500, 90.0), (60, 0.0), (60, 45.0), (6000, 0.0), (840, 75.0),
]


def case_on_and_off_leak(card):
    """One night whose leak goes on and off, so its total is not the recorded time."""
    start = datetime.datetime(2026, 4, 2, 22, 0, 0)
    folder = card / "DATALOG" / cpap_day(start).strftime("%Y%m%d")
    events = [(1200.0, "Synthetic event one", 15.0), (9000.0, "Synthetic event two", 22.0)]
    csl = [(600.0, "Synthetic marker start", 0.0)]

    step = RECORD_SECONDS / dict((spec[0], spec[4]) for spec in PLD_SIGNALS)[LEAK_LABEL]
    runs = []
    for seconds, value in ON_AND_OFF_LEAK:
        if seconds % step:
            raise ValueError(f"a run of {seconds} seconds is not a whole number of "
                             f"samples {step} seconds apart")
        runs.append((int(seconds / step), value))

    session = session_files(folder, start, sum(s for s, _ in ON_AND_OFF_LEAK) // RECORD_SECONDS,
                            events, csl, leak_runs=runs)
    filler(card, [folder])
    return {
        "case": "on-and-off-leak",
        "what_it_exercises": "a leak that goes on and off, so the time it ran above zero "
                             "is not the time the machine ran",
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
    "on-and-off-leak": case_on_and_off_leak,
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
