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
import random
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

# Two signals the page converts rather than relabels, because the figure a reader
# recognises is not the one every card records (Z, 2026-09-22). Which it did depends
# on the unit the file itself carries, so the answer works it out the same way.
PER_SECOND_UNITS = ("L/s", "L/sec", "l/s")
LITRE_UNITS = ("L", "l", "liter", "litre")
TIDVOL_LABEL = "TidVol.2s"


def shown_unit(label, unit):
    """What a reader must put on a signal, which is not always what its file says."""
    if label == LEAK_LABEL and unit in PER_SECOND_UNITS:
        return "L/min"
    if label == TIDVOL_LABEL and unit in LITRE_UNITS:
        return "mL"
    return SHOWN_UNITS.get(label, unit)

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

    return session_answer(start, records, written, events, csl_events, leak_runs)


def session_answer(start, records, written, events, csl_events, leak_runs=None):
    """What a session must produce, from the values it was built with."""
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
                "unit_shown": shown_unit(signal.label, signal.dimension),
                "seconds_between_samples": RECORD_SECONDS / signal.samples_per_record,
                "samples": len(signal.samples),
                "first_value": round(signal.to_physical(signal.samples[0]), 6),
                "value_at_100th": round(signal.to_physical(signal.samples[99]), 6),
                "last_value": round(signal.to_physical(signal.samples[-1]), 6),
            }

    leak = next(signal for signal in written["PLD"] if signal.label == LEAK_LABEL)
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



# ===== A night that looks like a night ======================================
#
# Built from dev/synthetic/realistic-night.md, which cites the source of every fact
# it rests on and marks every number that has none as a choice made here. Nothing in
# this section is guessed quietly: where a value is the generator's own, it says so.
#
# The night is a script first -- a list of what happened and when -- and every signal
# is a rendering of that one script. That is what makes the events agree with the
# flow beneath them, which no other case here does, and it is what lets answer.json
# be written from the script rather than read back out of the samples.

REALISTIC_SEED = 20260504

# Z, 2026-09-22: breathing "generally between 10-20" a minute, a ratio of inspiration
# to expiration of 1, and a flow that "is generally between +-0.25 to +-0.5", read as
# liters a second. Z narrowed it on 2026-09-23, having looked at a night of therapy
# that was going well: the rate sits around fifteen and the flow around a third of a
# liter a second, with the wider ranges above as the room either side of that.
BREATHS_A_MINUTE = (10.0, 20.0)
PEAK_FLOW = (0.25, 0.5)
BREATH_RATE = (15.0, 1.1)      # the middle of it, and how far a breath strays
BREATH_DEPTH = (0.29, 0.035)
INSPIRATION_SHARE = 0.5

# Every so often a deeper, slower breath. It is what puts the occasional spike well
# above the rest on the tidal volume, which a night of real breathing shows and a
# night of drawn breathing does not.
SIGH_EVERY = 45
SIGH_DEPTH = (1.7, 2.6)

# What follows an event: a run of faster, deeper breaths while the breathing catches
# up. Z, 2026-09-23, showed it as the spikes that sit on the rate, the tidal volume
# and the minute ventilation right where an event is marked.
RECOVERY_SECONDS = 22.0
RECOVERY_QUICKER = 1.35
RECOVERY_DEEPER = 1.55

# The machine, from ResMed's clinical guide (R-022) except where noted.
# Z, 2026-09-23, from a night that was going well: the pressure lives between about
# four and ten, starting low and coming back down over an hour or more rather than
# over minutes. A night with few events does not need much more than its floor.
START_PRESSURE = 6.0
MAX_PRESSURE = 12.0
EPR_LEVEL = 2.0                # the guide offers 1, 2 or 3
EPR_FLOOR = 4.0                # "will not drop below a minimum pressure of 4 cm H2O"
FOT_HZ = 4.0                   # "1 cm H2O peak-to-peak at 4 Hz" while detecting
FOT_SWING = 0.5

# Z, 2026-09-22: "Following an OA event the machine immediately increases the pressure
# by ~1-2 then slowly decreases. After HA it raises slightly."
OA_RISE = (1.0, 2.0)
HA_RISE = (0.3, 0.6)
PRESSURE_FALL = 0.035 / 60.0   # cm H2O a second. Z's "slowly decreases" is slower than
                               # it sounds: a rise of four takes the better part of two
                               # hours to come back, which is what a night of it looks
                               # like. It can be this slow only because the events below
                               # are few; a noisy night would ratchet to the ceiling

# The device calls an apnea at a fall of more than 75% and a hypopnea at a fall to
# 50%, both for at least ten seconds (R-022). The depths here sit either side of
# those lines on purpose, so an event the card annotates is an event the flow shows.
APNEA_LEFT = 0.04
HYPOPNEA_LEFT = 0.45
FLOW_LIMIT_FLATTENS_AT = 0.6

# Cheyne-Stokes: waxing periods "typically 40 seconds in length", waning "typically
# 20 seconds" (R-022), over at least three consecutive central events (R-023).
CSR_WAX = 40.0
CSR_WANE = 20.0
CSR_CYCLES = 6

# The five nights, and what each one holds. Z, 2026-09-23: "Your numbers are quite
# high, can be cut, the data I show you is successful therapy", and then "Generate 5
# different days, some without CSR." So a night of therapy that is working holds a
# handful of events rather than a hundred, and the five differ in when they begin,
# how long they run and what happens in them -- a quiet one, a busier one, a short
# one -- because five copies of one night would show a reader nothing a single night
# does not.
#
# Each begins in the evening, so each is its own CPAP day.
REALISTIC_NIGHTS = [
    {"start": datetime.datetime(2026, 5, 4, 23, 10), "minutes": 440, "csr": True,
     "events": {"OA": 4, "HA": 3, "CA": 3, "A": 2, "Ar": 3}},
    {"start": datetime.datetime(2026, 5, 5, 22, 40), "minutes": 395, "csr": False,
     "events": {"OA": 2, "HA": 2, "CA": 1, "A": 1, "Ar": 2}},
    {"start": datetime.datetime(2026, 5, 6, 23, 55), "minutes": 350, "csr": False,
     "events": {"OA": 6, "HA": 5, "CA": 2, "A": 3, "Ar": 4}},
    {"start": datetime.datetime(2026, 5, 7, 22, 20), "minutes": 470, "csr": True,
     "events": {"OA": 3, "HA": 4, "CA": 4, "A": 2, "Ar": 2}},
    {"start": datetime.datetime(2026, 5, 8, 23, 30), "minutes": 300, "csr": False,
     "events": {"OA": 1, "HA": 2, "CA": 0, "A": 1, "Ar": 1}},
]

# Flow limitation is not a few long stretches but many short ones, most of them
# small; snore is all but silent on a night that is going well.
FLOW_LIMIT_SPIKES = 180
SNORE_SPIKES = 14

# What the leak does. Near nothing, with a few excursions where a mask shifts. In
# liters a second, which is what ResMed's own detailed-data table names (R-022) and
# which the page turns into liters a minute.
LEAK_BASE = 0.0                # ResMed reports unintentional leak, which is nothing at
                               # all on a mask that is sitting right. The generator's
                               # reading of it, and what keeps Dur. worth showing
LEAK_SHIFTS = 7


def realistic_script(rng, seconds, counts, with_csr):
    """What happened in the night, in time order, before any signal is drawn.

    A counted handful rather than whatever a random walk produces: a night of therapy
    that is working holds few events, and how many of each is set in EVENTS_A_NIGHT.
    Nothing is allowed to overlap anything else, so every annotation has flow of its
    own beneath it.
    """
    episodes = []
    taken = []
    if with_csr:
        csr_at = float(round(seconds * 0.22))
        csr_length = CSR_CYCLES * (CSR_WAX + CSR_WANE)
        episodes.append({"kind": "CSR", "at": csr_at, "length": csr_length})
        taken.append((csr_at - 120.0, csr_at + csr_length + 120.0))

    for kind in ("OA", "HA", "CA", "A", "Ar"):
        for _ in range(counts.get(kind, 0)):
            length = float(round({
                "OA": rng.uniform(12.0, 26.0),
                "CA": rng.uniform(11.0, 19.0),
                # An apnea the device could not put in either box. It looks like any
                # other in the flow, since what separates them is effort and a card
                # carries no effort channel (R-023).
                "A": rng.uniform(11.0, 24.0),
                "HA": rng.uniform(12.0, 38.0),
                # An arousal ends a stretch of rising effort, which is seen as flow
                # limitation (R-022), so the stretch is the episode and the arousal
                # is the moment it ends.
                "Ar": rng.uniform(25.0, 70.0),
            }[kind]))
            for _try in range(200):
                at = float(round(rng.uniform(9 * 60, seconds - 9 * 60)))
                clear = all(at > late or at + length + 90.0 < early
                            for early, late in taken)
                if clear:
                    episodes.append({"kind": kind, "at": at, "length": length})
                    taken.append((at - 90.0, at + length + 90.0))
                    break

    episodes.sort(key=lambda one: one["at"])
    return episodes


def csr_factor(into):
    """Where the flow is through one Cheyne-Stokes cycle, as a share of an ordinary breath.

    It waxes to a peak and wanes to nearly nothing, which is the "periodic waxing and
    waning" the guide describes, and the waning part is deep enough and long enough to
    be an apnea by the device's own rule.
    """
    cycle = into % (CSR_WAX + CSR_WANE)
    if cycle < CSR_WAX:
        # A crescendo and decrescendo across the waxing part.
        return 0.15 + 0.85 * math.sin(math.pi * cycle / CSR_WAX)
    return APNEA_LEFT


def realistic_states(script, samples, step):
    """Per flow sample: how much of an ordinary breath there is, and what shape it is.

    Filled a range at a time rather than asked per sample, because a night holds
    hundreds of thousands of samples and this is the loop that would be felt.

    Four things come back. How much of a breath there is; whether its inspiratory
    half is flattened; and how much quicker and deeper the breathing is, which is
    what it does for a few breaths after an event has passed.
    """
    factor = [1.0] * samples
    flat = [False] * samples
    quicker = [1.0] * samples
    deeper = [1.0] * samples

    def fill(where, first, last, value):
        if last > first:
            where[first:last] = [value] * (last - first)

    for one in script:
        first = max(0, int(one["at"] / step))
        last = min(samples, int((one["at"] + one["length"]) / step))
        if one["kind"] in ("OA", "CA", "A"):
            fill(factor, first, last, APNEA_LEFT)
        elif one["kind"] == "HA":
            fill(factor, first, last, HYPOPNEA_LEFT)
        elif one["kind"] == "Ar":
            fill(flat, first, last, True)
        elif one["kind"] == "CSR":
            factor[first:last] = [csr_factor((i - first) * step) for i in range(first, last)]
            continue
        # Catching up afterwards, which is what puts a spike on the rate, the tidal
        # volume and the minute ventilation just after an event is marked.
        after = min(samples, last + int(RECOVERY_SECONDS / step))
        fill(quicker, last, after, RECOVERY_QUICKER)
        fill(deeper, last, after, RECOVERY_DEEPER)
    return factor, flat, quicker, deeper


def breath_shape(phase, flat):
    """One breath: inspiration then expiration, each the same length (Z's ratio of 1).

    A rounded curve for each breath is the device's own description of normal
    breathing (R-022); flow limitation is that curve's shape changing, which here is
    its inspiratory half flattening off.
    """
    if phase < INSPIRATION_SHARE:
        value = math.sin(math.pi * phase / INSPIRATION_SHARE)
        return min(value, FLOW_LIMIT_FLATTENS_AT) if flat else value
    return -math.sin(math.pi * (phase - INSPIRATION_SHARE) / (1 - INSPIRATION_SHARE))


def realistic_flow(rng, script, seconds, per_second):
    """Every flow sample of the night, and the breaths it turned out to be made of.

    The breaths come back because the rate, the tidal volume and the minute
    ventilation are arithmetic over this flow rather than signals of their own. A
    breath's volume is its inspiratory flow added up, which is what a volume is.
    """
    step = 1.0 / per_second
    samples = int(round(seconds * per_second))
    factor, flat, quicker, deeper = realistic_states(script, samples, step)

    flow = [0.0] * samples
    exhaling = [False] * samples
    breaths = []
    counted = 0

    def a_breath(at):
        """The next breath's length and depth, around the middle of Z's ranges."""
        rate = min(BREATHS_A_MINUTE[1], max(BREATHS_A_MINUTE[0], rng.gauss(*BREATH_RATE)))
        depth = min(PEAK_FLOW[1], max(PEAK_FLOW[0], rng.gauss(*BREATH_DEPTH)))
        if counted % SIGH_EVERY == SIGH_EVERY - 1:
            depth *= rng.uniform(*SIGH_DEPTH)
        return 60.0 / (rate * quicker[at]), depth * deeper[at]

    period, peak = a_breath(0)
    phase = 0.0
    began = 0.0
    volume = 0.0

    for i in range(samples):
        phase += step / period
        if phase >= 1.0:
            breaths.append({"at": began, "period": period, "liters": volume})
            counted += 1
            phase -= 1.0
            began = i * step
            volume = 0.0
            period, peak = a_breath(i)
        value = factor[i] * peak * breath_shape(phase, flat[i])
        flow[i] = value
        exhaling[i] = value < 0
        if value > 0:
            volume += value * step
    breaths.append({"at": began, "period": period, "liters": volume})
    return flow, exhaling, breaths


def realistic_pressure(rng, script, seconds, per_second, exhaling):
    """The therapy pressure through the night, and the mask pressure over it.

    The therapy pressure answers events the way Z described: up at once after an
    obstructive apnea, a little after a hypopnea, and never after a central one,
    which is the guide's own. Between events it falls back slowly.
    """
    step = 1.0 / per_second
    samples = len(exhaling)
    rises = []
    for one in script:
        # An apnea the device did not classify is answered like an obstructive one.
        # The guide has AutoSet adjusting "as a function of ... apnoea" and names the
        # central case as the exception that moves nothing (R-022), so raising is the
        # rule and not raising is the special case. That reading is the generator's,
        # and it is the one thing here that no source states outright.
        if one["kind"] in ("OA", "A"):
            rises.append((one["at"] + one["length"], rng.uniform(*OA_RISE)))
        elif one["kind"] == "HA":
            rises.append((one["at"] + one["length"], rng.uniform(*HA_RISE)))
    rises.sort()

    # Where the device is testing an airway, and so adding its oscillation.
    testing = [False] * samples
    for one in script:
        if one["kind"] in ("OA", "CA", "A"):
            first = max(0, int(one["at"] / step))
            last = min(samples, int((one["at"] + one["length"]) / step))
            testing[first:last] = [True] * (last - first)

    therapy = [0.0] * samples
    mask = [0.0] * samples
    at = START_PRESSURE
    next_rise = 0
    for i in range(samples):
        now = i * step
        while next_rise < len(rises) and rises[next_rise][0] <= now:
            at = min(MAX_PRESSURE, at + rises[next_rise][1])
            next_rise += 1
        at = max(START_PRESSURE, at - PRESSURE_FALL * step)
        therapy[i] = at
        over = at - (EPR_LEVEL if exhaling[i] else 0.0)
        if testing[i]:
            over += FOT_SWING * math.sin(2 * math.pi * FOT_HZ * now)
        mask[i] = max(EPR_FLOOR, over)
    return therapy, mask


def realistic_leak(rng, seconds, per_sample, samples):
    """A leak that sits near nothing and lifts where a mask shifts, in liters a second."""
    leak = [LEAK_BASE] * samples
    for _ in range(LEAK_SHIFTS):
        at = rng.uniform(0.05, 0.9) * seconds
        length = rng.uniform(240.0, 900.0)
        height = rng.uniform(0.15, 0.55)
        first = max(0, int(at / per_sample))
        last = min(samples, int((at + length) / per_sample))
        edge = max(1, (last - first) // 6)
        for i in range(first, last):
            into = i - first
            if into < edge:
                shape = into / edge
            elif into > (last - first) - edge:
                shape = ((last - first) - into) / edge
            else:
                shape = 1.0
            # Not steady while it lasts: a mask that has moved leaks unevenly.
            leak[i] = max(leak[i], LEAK_BASE + height * shape * rng.uniform(0.8, 1.05))
    return leak


def realistic_derived(breaths, seconds, per_sample, samples):
    """Rate, tidal volume and minute ventilation, worked out from the breaths.

    Breath by breath, not averaged over the minute before: each sample reports the
    breath it falls in. That is what Z's own night looks like -- the rate spikes
    where an event is marked, because the breathing that follows one is quicker, and
    it never falls to nothing, because a breath is always in progress even where
    almost no air moves. A minute-long window smooths both of those away.

    So an apnea shows here as the tidal volume and the minute ventilation collapsing
    while the rate holds, which is the shape of the thing: the breathing continued
    and carried nothing.
    """
    rate = [0.0] * samples
    volume = [0.0] * samples
    minute = [0.0] * samples
    cover = 0
    for i in range(samples):
        now = i * per_sample
        while cover + 1 < len(breaths) and breaths[cover + 1]["at"] <= now:
            cover += 1
        one = breaths[cover]
        rate[i] = 60.0 / one["period"]
        volume[i] = one["liters"] * 1000.0
        minute[i] = one["liters"] * rate[i]
    return rate, volume, minute


def realistic_extras(rng, script, seconds, per_sample, samples):
    """Snore and flow limitation.

    Z, 2026-09-23: on a night that is going well, flow limitation is many short
    spikes rather than a few long stretches, most of them small, and snore is all but
    silent. The stretches that end in an arousal still lift both, since that is what
    an arousal is the end of (R-022), but they are no longer the only thing there.
    """
    snore = [0.0] * samples
    limit = [0.0] * samples

    for one in script:
        if one["kind"] != "Ar":
            continue
        first = max(0, int(one["at"] / per_sample))
        last = min(samples, int((one["at"] + one["length"]) / per_sample))
        for i in range(first, last):
            into = (i - first) / max(1, last - first)
            shape = math.sin(math.pi * into)
            limit[i] = max(limit[i], round(0.42 * shape, 4))
            snore[i] = max(snore[i], round(0.5 * shape, 4))

    for _ in range(FLOW_LIMIT_SPIKES):
        at = int(rng.uniform(0.02, 0.98) * samples)
        wide = rng.randint(1, 4)
        height = rng.uniform(0.03, 0.25)
        for i in range(at, min(samples, at + wide)):
            limit[i] = max(limit[i], round(height, 4))

    for _ in range(SNORE_SPIKES):
        at = int(rng.uniform(0.02, 0.98) * samples)
        wide = rng.randint(1, 3)
        height = rng.uniform(0.04, 0.55)
        for i in range(at, min(samples, at + wide)):
            snore[i] = max(snore[i], round(height, 4))
    return snore, limit


def carried(label, unit, low, high, per_record, records, values):
    """One signal from values already worked out, rather than from a shape."""
    signal = edf.Signal(label, unit, low, high, DIGITAL_MIN, DIGITAL_MAX, per_record, [])
    wanted = per_record * records
    if len(values) != wanted:
        raise ValueError(f"{label}: {len(values)} values for {wanted} samples")
    signal.samples = [signal.to_digital(value) for value in values]
    return signal


def realistic_events(script):
    """The annotations the machine would have written, from the same script.

    The words are the ones Z reported a card carries, in dev/formats/resmed.md. A
    central apnea inside a Cheyne-Stokes stretch is annotated like any other, since
    it meets the device's rule for one; the stretch itself is bracketed in the CSL
    file by the pair that marks where it began and ended.
    """
    events = []
    csl = []
    for one in script:
        if one["kind"] == "OA":
            events.append((one["at"], "Obstructive Apnea", round(one["length"], 2)))
        elif one["kind"] == "CA":
            events.append((one["at"], "Central Apnea", round(one["length"], 2)))
        elif one["kind"] == "HA":
            events.append((one["at"], "Hypopnea", round(one["length"], 2)))
        elif one["kind"] == "A":
            events.append((one["at"], "Apnea", round(one["length"], 2)))
        elif one["kind"] == "Ar":
            # The arousal is the moment the stretch of rising effort ends.
            events.append((round(one["at"] + one["length"], 2), "Arousal", 3.0))
        elif one["kind"] == "CSR":
            csl.append((one["at"], "CSR Start", 0.0))
            csl.append((round(one["at"] + one["length"], 2), "CSR End", 0.0))
            for cycle in range(CSR_CYCLES):
                began = one["at"] + cycle * (CSR_WAX + CSR_WANE) + CSR_WAX
                events.append((round(began, 2), "Central Apnea", CSR_WANE))
    events.sort()
    return events, csl


def realistic_session(folder, night, seed):
    """One night, rendered from one script, with the files a machine would leave.

    Its own seed, so each night of the card differs from the others and each stays
    the same from one run to the next.
    """
    rng = random.Random(seed)
    start = night["start"]
    records = night["minutes"]
    seconds = records * RECORD_SECONDS
    stamp = start.strftime("%Y%m%d_%H%M%S")

    script = realistic_script(rng, seconds, night["events"], night["csr"])
    fast = 1500 // RECORD_SECONDS                 # 25 a second, as the guide states
    slow = RECORD_SECONDS / 30.0                  # one every two seconds
    flow, exhaling, breaths = realistic_flow(rng, script, seconds, fast)
    therapy, mask = realistic_pressure(rng, script, seconds, fast, exhaling)

    slow_samples = 30 * records
    every = round(fast * slow)
    therapy_slow = [therapy[i * every] for i in range(slow_samples)]
    # Over a breath rather than over the two seconds the sample stands for. The mask
    # pressure swings by the whole of EPR every breath, and a breath is about four
    # seconds, so a two-second mean lands on the inhale or the exhale by turns and
    # draws a band across the whole swing instead of a line inside it. A breath-long
    # mean is what the channel looks like on a card.
    mask_slow = []
    for i in range(slow_samples):
        first = max(0, (i - 1) * every)
        last = (i + 1) * every
        mask_slow.append(sum(mask[first:last]) / (last - first))
    leak = realistic_leak(rng, seconds, slow, slow_samples)
    rate, volume, minute = realistic_derived(breaths, seconds, slow, slow_samples)
    snore, limit = realistic_extras(rng, script, seconds, slow, slow_samples)

    brp = [
        carried("Flow.40ms", "L/s", -1.0, 1.0, 1500, records, flow),
        carried("Press.40ms", "cmH2O", 0.0, 30.0, 1500, records, mask),
    ]
    edf.write(folder / f"{stamp}_BRP.edf", start, RECORD_SECONDS, brp,
              patient=PATIENT_FIELD, recording=RECORDING_FIELD)

    pld = [
        carried("MaskPress.2s", "cmH2O", 0.0, 30.0, 30, records, mask_slow),
        carried("Press.2s", "cmH2O", 0.0, 30.0, 30, records, therapy_slow),
        carried("EprPress.2s", "cmH2O", 0.0, 30.0, 30, records,
                [max(EPR_FLOOR, one - EPR_LEVEL) for one in therapy_slow]),
        carried("Leak.2s", "L/s", 0.0, 2.0, 30, records, leak),
        carried("RespRate.2s", "bpm", 0.0, 60.0, 30, records, rate),
        carried("TidVol.2s", "mL", 0.0, 4000.0, 30, records, volume),
        carried("MinVent.2s", "L/min", 0.0, 30.0, 30, records, minute),
        carried("Snore.2s", "", 0.0, 5.0, 30, records, snore),
        carried("FlowLim.2s", "", 0.0, 1.0, 30, records, limit),
    ]
    edf.write(folder / f"{stamp}_PLD.edf", start, RECORD_SECONDS, pld,
              patient=PATIENT_FIELD, recording=RECORDING_FIELD)

    events, csl = realistic_events(script)
    edf.write(folder / f"{stamp}_EVE.edf", start, 0,
              annotations=[edf.Annotation(o, t, d) for o, t, d in events],
              n_records=1, record_event="Recording starts",
              patient=PATIENT_FIELD, recording=RECORDING_FIELD)
    edf.write(folder / f"{stamp}_CSL.edf", start, 0,
              annotations=[edf.Annotation(o, t, d) for o, t, d in csl],
              n_records=1, record_event="Recording starts",
              patient=PATIENT_FIELD, recording=RECORDING_FIELD)

    answer = session_answer(start, records, {"BRP": brp, "PLD": pld}, events, csl)
    answer["script"] = script
    answer["breaths"] = len(breaths)
    return answer


def case_realistic(card):
    """Five nights that look like nights, for someone to try the site with.

    They differ in when they begin, how long they run and what happens in them, and
    only some of them hold a stretch of Cheyne-Stokes respiration, so a reader
    stepping between them sees a week rather than one night five times.
    """
    sessions = []
    folders = []
    for index, night in enumerate(REALISTIC_NIGHTS):
        folder = card / "DATALOG" / cpap_day(night["start"]).strftime("%Y%m%d")
        folders.append(folder)
        sessions.append(realistic_session(folder, night, REALISTIC_SEED + index))

    days = {}
    for session in sessions:
        days.setdefault(session["cpap_day"], []).append(session["start"])

    filler(card, sorted(set(folders)))
    return {
        "case": "realistic",
        "what_it_exercises": "five nights rendered from scripts of what happened in them, so "
                             "the events agree with the flow beneath them and the pressure "
                             "answers them the way the machine does. They differ from each "
                             "other, and only some hold a Cheyne-Stokes stretch",
        "cpap_days": days,
        "sessions": sessions,
        "identifying_marker": MARKER,
        "files_never_to_open": ["STR.edf", "Journal.dat", "Identification.tgt",
                                "Identification.crc", "SETTINGS/SET1.tgt", "*.crc"],
    }


CASES = {
    "plain-night": case_plain_night,
    "on-and-off-leak": case_on_and_off_leak,
    "realistic": case_realistic,
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
