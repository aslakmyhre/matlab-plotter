"""Reading MATLAB files and presenting them as a channel × sample matrix."""
import re
from collections import namedtuple

import numpy as np
import scipy.io
from scipy.io.matlab import mat_struct

# A log has few channels and many samples; more than this means the orientation is wrong.
MAX_CHANNELS = 64
# Equally long vectors saved one by one are one log, shown under this name.
VECTORS_VARIABLE = "all vectors"
# A variable named like this is preferred when several lists of text could name the channels.
NAME_HINTS = ("name", "label", "signal", "channel", "header", "var", "legend")
UNIT_HINT = "unit"
# Only a rising row that is also called this beats the first row as the time vector.
TIME_NAMES = {"t", "time", "times", "tout", "timestamp"}
_NAME_WITH_UNIT = re.compile(r"^(.*\S)\s*[\[(]([^\[\]()]*)[\])]$")

# arrays: variable -> 2-D numeric array, the likeliest log first.
# names: variable -> [(name, unit)] per channel, for the variables whose names the file holds.
Log = namedtuple("Log", "arrays names")


def load_log(path):
    """Everything plottable in a .mat file, with whatever names it holds for it."""
    try:
        mat = scipy.io.loadmat(path, squeeze_me=True, struct_as_record=False)
    except (scipy.io.matlab.MatReadError, NotImplementedError) as exc:
        # NotImplementedError is how scipy turns away v7.3 (HDF5) files.
        raise ValueError(f"{path} cannot be read: {exc}") from exc
    variables = {k: v for k, v in mat.items() if not k.startswith("__")}
    log = Log({}, {})
    _read_scope(variables, "", log)
    for name, value in variables.items():
        if isinstance(value, mat_struct):
            _read_struct(name, value, log)
    if not log.arrays:
        # An aborted run leaves its To File matrix with no samples at all.
        raise ValueError(f"{path} holds no non-empty 2-D numeric array")
    ranked = sorted(log.arrays, key=lambda name: -_channel_rank(log.arrays[name]))
    return Log({name: log.arrays[name] for name in ranked}, log.names)


def _channel_rank(array):
    channels = min(array.shape)
    return channels if channels <= MAX_CHANNELS else 0


def _is_numeric(value):
    return (isinstance(value, np.ndarray) and value.ndim <= 2 and value.size > 1
            and np.issubdtype(value.dtype, np.number))


def _strings(value):
    """A cell array or char matrix as a list of text, None if it is anything else."""
    if isinstance(value, np.ndarray) and value.ndim == 1 and all(
            isinstance(item, str) for item in value):
        return [str(item).strip() for item in value]
    return None


def split_unit(text):
    """(name, unit) from text such as "pitch [rad]"."""
    match = _NAME_WITH_UNIT.match(text.strip())
    return (match.group(1), match.group(2)) if match else (text.strip(), "")


def _read_scope(variables, prefix, log):
    """The arrays among these variables, named by any list of text that fits them."""
    vectors = {}
    for name, value in variables.items():
        if _is_numeric(value):
            log.arrays[prefix + name] = np.atleast_2d(value)
            if value.ndim == 1:
                vectors[name] = value
    _group_vectors(vectors, prefix, log)
    texts = {name: _strings(value) for name, value in variables.items()}
    texts = {name: text for name, text in texts.items() if text}
    for name, value in variables.items():
        if _is_numeric(value) and value.ndim == 2:
            found = _names_for(min(value.shape), texts)
            if found:
                log.names[prefix + name] = found


def _group_vectors(vectors, prefix, log):
    lengths = [len(value) for value in vectors.values()]
    if not lengths:
        return
    length = max(set(lengths), key=lengths.count)
    group = {name: value for name, value in vectors.items() if len(value) == length}
    if len(group) >= 2:
        log.arrays[prefix + VECTORS_VARIABLE] = np.vstack(list(group.values()))
        log.names[prefix + VECTORS_VARIABLE] = [split_unit(name) for name in group]


def _names_for(channels, texts):
    """[(name, unit)] from the lists of text with one entry per channel, if there are any."""
    fitting = {name: text for name, text in texts.items() if len(text) == channels}
    units = next((text for name, text in fitting.items() if UNIT_HINT in name.lower()), None)
    candidates = {name: text for name, text in fitting.items() if UNIT_HINT not in name.lower()}
    if not candidates:
        return None
    hinted = [text for name, text in candidates.items()
              if any(hint in name.lower() for hint in NAME_HINTS)]
    chosen = hinted[0] if hinted else next(iter(candidates.values()))
    if units:
        return list(zip(chosen, units))
    return [split_unit(text) for text in chosen]


def _read_struct(name, struct, log):
    """A Simulink log, or a struct whose fields are read like top-level variables."""
    fields = {field: getattr(struct, field) for field in struct._fieldnames}
    if "signals" in fields and _read_simulink(name, fields, log):
        return
    _read_scope(fields, f"{name}.", log)


def _read_simulink(name, fields, log):
    """A To Workspace "Structure With Time". Returns whether this was one."""
    signals = np.atleast_1d(fields["signals"])
    if not all(isinstance(signal, mat_struct) and hasattr(signal, "values")
               for signal in signals):
        return False
    rows, names = [], []
    time = fields.get("time")
    if _is_numeric(time):
        rows.append(np.ravel(time))
        names.append(("time", ""))
    for signal in signals:
        values = np.atleast_2d(signal.values)
        # Simulink stores samples in rows, one column per signal.
        if values.shape[0] > values.shape[1]:
            values = values.T
        label = _signal_label(signal)
        for position, row in enumerate(values, start=1):
            names.append(split_unit(f"{label} {position}" if len(values) > 1 and label
                                    else label))
            rows.append(row)
    if len({len(row) for row in rows}) != 1:
        return False
    log.arrays[name] = np.vstack(rows)
    log.names[name] = names
    return True


def _signal_label(signal):
    label = getattr(signal, "label", "")
    if isinstance(label, str) and label.strip("<> "):
        return label.strip("<> ")
    block = getattr(signal, "blockName", "")
    return block.rpartition("/")[2] if isinstance(block, str) else ""


def orient(array, orientation):
    """The array as (channel, sample) for the chosen orientation."""
    return array if orientation == "rows" else array.T


def natural_orientation(array):
    """Signals lie along the short dimension of a log."""
    return "rows" if array.shape[0] <= array.shape[1] else "columns"


def is_time_like(row):
    """A time channel rises steadily; a measured signal does not."""
    return row.size > 1 and bool(np.all(np.diff(row) > 0))


def time_row(matrix, channel_names):
    """The row to use as time: one named so if it rises, else a rising first row, else None."""
    if matrix.shape[0] < 2:
        return None
    for row, name in enumerate(channel_names[:matrix.shape[0]]):
        if name.strip().lower() in TIME_NAMES and is_time_like(matrix[row]):
            return row
    return 0 if is_time_like(matrix[0]) else None
