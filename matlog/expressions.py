"""Derived channels: user-typed expressions over the loaded signals."""
import re

import numpy as np


def identifier(name):
    """A channel name turned into something an expression can reference."""
    cleaned = re.sub(r"\W+", "_", name.strip().lower()).strip("_")
    return cleaned or "unnamed"


def smooth(x, n):
    """Moving average over n samples, keeping the input length."""
    n = max(1, int(n))
    kernel = np.ones(n) / n
    return np.convolve(np.asarray(x, dtype=float), kernel, mode="same")


def make_namespace(t, channels):
    """What an expression may reference: the time vector, the signals, and math."""
    space = {
        "t": t, "pi": np.pi, "np": np,
        "sin": np.sin, "cos": np.cos, "tan": np.tan, "exp": np.exp, "log": np.log,
        "sqrt": np.sqrt, "abs": np.abs, "clip": np.clip, "where": np.where,
        "cumsum": np.cumsum, "deg": np.rad2deg, "rad": np.deg2rad,
        "smooth": smooth,
        "deriv": lambda x: np.gradient(np.asarray(x, dtype=float), t),
    }
    space.update(channels)
    return space


def evaluate(expression, namespace, label):
    """Run one expression, or raise ValueError naming the channel that failed."""
    try:
        value = eval(expression, {"__builtins__": {}}, namespace)  # noqa: S307 - local, user's own file
    except Exception as exc:
        raise ValueError(f"{label}: {exc}")
    array = np.asarray(value, dtype=float).ravel()
    expected = len(namespace["t"])
    if array.size == 1:
        array = np.full(expected, array.item())
    if array.size != expected:
        raise ValueError(f"{label}: expression gave {array.size} values, need {expected}")
    return array
