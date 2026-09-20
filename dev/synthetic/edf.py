"""Write EDF and EDF+ files for the synthetic cards.

Everything here comes from formats/resmed.md, which cites the EDF
specification (R-001) and sections 2.1 and 2.2 of the EDF+ specification
(R-002) for each fact. No other source was open while this was written.

What this module is for, and what it is not: it writes files a reader can
be tested against, so it is strict about the parts of the format a reader
will lean on, and it is happy to write a file that is wrong on purpose when
a case asks for one. Every wrongness is asked for by name, never a default.

A note on the numbers: physical and digital extremes, record durations and
samples per record are the generator's own choices. The format file marks
them as such, because no source states what a real card uses, and a reader
must take them from each header rather than assuming them.
"""

import datetime
import pathlib

# The header's fixed part, in order, with the width of each field.
GLOBAL_FIELDS = [
    ("version", 8),
    ("patient", 80),
    ("recording", 80),
    ("startdate", 8),
    ("starttime", 8),
    ("header_bytes", 8),
    ("reserved", 44),
    ("n_records", 8),
    ("record_duration", 8),
    ("n_signals", 4),
]

# Each of these appears once per signal, all of one field before the next.
SIGNAL_FIELDS = [
    ("label", 16),
    ("transducer", 80),
    ("dimension", 8),
    ("physical_min", 8),
    ("physical_max", 8),
    ("digital_min", 8),
    ("digital_max", 8),
    ("prefiltering", 80),
    ("samples_per_record", 8),
    ("reserved", 32),
]

ANNOTATION_LABEL = "EDF Annotations"
TAL_DURATION = b"\x15"
TAL_END = b"\x14"
TAL_PAD = b"\x00"


class Signal:
    """One ordinary signal: its calibration, and its samples as digital values."""

    def __init__(self, label, dimension, physical_min, physical_max,
                 digital_min, digital_max, samples_per_record, samples,
                 transducer="", prefiltering=""):
        self.label = label
        self.dimension = dimension
        self.physical_min = physical_min
        self.physical_max = physical_max
        self.digital_min = digital_min
        self.digital_max = digital_max
        self.samples_per_record = samples_per_record
        self.samples = list(samples)
        self.transducer = transducer
        self.prefiltering = prefiltering

    def to_physical(self, digital):
        """The value a reader must arrive at, by the mapping in formats/resmed.md."""
        span = (self.physical_max - self.physical_min) / (self.digital_max - self.digital_min)
        return self.physical_min + (digital - self.digital_min) * span

    def to_digital(self, physical):
        span = (self.digital_max - self.digital_min) / (self.physical_max - self.physical_min)
        value = round(self.digital_min + (physical - self.physical_min) * span)
        return max(self.digital_min, min(self.digital_max, value))


class Annotation:
    def __init__(self, onset, text, duration=None):
        self.onset = onset
        self.text = text
        self.duration = duration


class EdfError(Exception):
    pass


def _number(value):
    """A number as EDF writes it: no grouping, a dot for any decimal point."""
    if isinstance(value, int) or float(value).is_integer():
        return str(int(value))
    text = f"{value:.6f}".rstrip("0").rstrip(".")
    return text


def _field(text, width, name):
    """One header field: printable ASCII, left-justified, padded with spaces."""
    text = str(text)
    for char in text:
        if not 32 <= ord(char) <= 126:
            raise EdfError(f"{name}: {char!r} is not printable US-ASCII, which the header forbids")
    if len(text) > width:
        raise EdfError(f"{name}: {text!r} is longer than its {width}-byte field")
    return text.ljust(width).encode("ascii")


def _start_fields(start):
    """The start date and time, with the specification's year clipping."""
    if not 1985 <= start.year <= 2084:
        raise EdfError("a start date outside 1985 to 2084 has no two-digit form in EDF+")
    return start.strftime("%d.%m.%y"), start.strftime("%H.%M.%S")


def _tal(onset, duration, texts):
    """One time-stamped annotation list, ending with its separator and pad."""
    sign = "+" if onset >= 0 else "-"
    out = (sign + _number(abs(onset))).encode("ascii")
    if duration is not None:
        out += TAL_DURATION + _number(duration).encode("ascii")
    out += TAL_END
    for text in texts:
        encoded = text.encode("utf-8")
        for forbidden in (b"\x14", b"\x15", b"\x00"):
            if forbidden in encoded:
                raise EdfError(f"annotation {text!r} holds a byte that separates annotations")
        out += encoded + TAL_END
    return out + TAL_PAD


def _annotation_records(n_records, record_duration, annotations, record_event):
    """The annotation channel, one block of bytes per record."""
    blocks = []
    for index in range(n_records):
        start = index * record_duration
        texts = [""] if record_event is None else ["", record_event]
        block = _tal(start, None, texts)
        for note in annotations:
            fits_here = n_records == 1 or start <= note.onset < start + record_duration
            if fits_here:
                block += _tal(note.onset, note.duration, [note.text])
        blocks.append(block)
    return blocks


def write(path, start, record_duration, signals=(), annotations=(),
          patient="X X X X", recording="Startdate X X X X", continuous=True,
          n_records=None, record_event=None, annotation_bytes=None,
          claim_records=None, claim_header_bytes=None, truncate_bytes=0):
    """Write one EDF or EDF+ file.

    signals are ordinary signals; annotations add an 'EDF Annotations'
    channel. A file with annotations and no ordinary signals has a record
    duration of 0 and needs n_records and record_event.

    The last three arguments write a file that does not add up, for the cases
    that test a reader's checking: a header claiming a different number of
    records or header length, and bytes cut off the end.
    """
    path = pathlib.Path(path)
    signals = list(signals)
    annotations = list(annotations)

    if signals:
        counts = {len(s.samples) / s.samples_per_record for s in signals}
        if len(counts) != 1 or not float(counts.copy().pop()).is_integer():
            raise EdfError("every signal must hold a whole number of records, and the same number")
        records = int(counts.pop())
        if n_records is not None and n_records != records:
            raise EdfError("n_records does not match the samples given")
    elif n_records is None:
        raise EdfError("a file with no ordinary signals needs n_records")
    else:
        records = n_records

    for signal in signals:
        if signal.digital_max <= signal.digital_min:
            raise EdfError(f"{signal.label}: digital maximum must be larger than digital minimum")
        if signal.physical_max == signal.physical_min:
            raise EdfError(f"{signal.label}: physical maximum must differ from physical minimum")
        if signal.label == ANNOTATION_LABEL:
            raise EdfError("an ordinary signal may not be labeled as the annotation channel")
        for sample in signal.samples:
            if not signal.digital_min <= sample <= signal.digital_max:
                raise EdfError(f"{signal.label}: a sample lies outside the digital range it declares")

    blocks = []
    if annotations or not signals:
        blocks = _annotation_records(records, record_duration, annotations, record_event)
        widest = max(len(block) for block in blocks)
        size = annotation_bytes if annotation_bytes is not None else widest + (widest % 2)
        if size < widest:
            raise EdfError("the annotation channel is too small for the annotations asked for")
        blocks = [block.ljust(size, b"\x00") for block in blocks]
        annotation_samples = size // 2

    header_signals = list(signals)
    if blocks:
        header_signals.append(Signal(ANNOTATION_LABEL, "", -1, 1, -32768, 32767, annotation_samples, []))

    startdate, starttime = _start_fields(start)
    header_bytes = 256 * (len(header_signals) + 1)
    reserved = ("EDF+C" if continuous else "EDF+D") if blocks else ""

    head = b"".join([
        _field(0, 8, "version"),
        _field(patient, 80, "patient"),
        _field(recording, 80, "recording"),
        _field(startdate, 8, "startdate"),
        _field(starttime, 8, "starttime"),
        _field(claim_header_bytes if claim_header_bytes is not None else header_bytes, 8, "header bytes"),
        _field(reserved, 44, "reserved"),
        _field(claim_records if claim_records is not None else records, 8, "number of records"),
        _field(_number(record_duration), 8, "record duration"),
        _field(len(header_signals), 4, "number of signals"),
    ])

    for name, width in SIGNAL_FIELDS:
        for signal in header_signals:
            if name == "label":
                value = signal.label
            elif name == "transducer":
                value = signal.transducer
            elif name == "dimension":
                value = signal.dimension
            elif name == "physical_min":
                value = _number(signal.physical_min)
            elif name == "physical_max":
                value = _number(signal.physical_max)
            elif name == "digital_min":
                value = _number(signal.digital_min)
            elif name == "digital_max":
                value = _number(signal.digital_max)
            elif name == "samples_per_record":
                value = signal.samples_per_record
            else:
                value = ""
            head += _field(value, width, f"{signal.label} {name}")

    body = bytearray()
    for index in range(records):
        for signal in signals:
            first = index * signal.samples_per_record
            for sample in signal.samples[first:first + signal.samples_per_record]:
                body += int(sample).to_bytes(2, "little", signed=True)
        if blocks:
            body += blocks[index]

    data = head + bytes(body)
    if truncate_bytes:
        data = data[:-truncate_bytes]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return len(data)


def ends_at(start, record_duration, n_records):
    """Where a continuous recording ends, by the EDF+ rule for EDF+C files."""
    return start + datetime.timedelta(seconds=record_duration * n_records)
