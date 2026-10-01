"""Reading MATLAB files and presenting them as a channel × sample matrix."""
import numpy as np
import scipy.io

# A log has few channels and many samples; more than this means the orientation is wrong.
MAX_CHANNELS = 64


def load_arrays(path):
    """Every 2-D numeric variable in a .mat file, keyed by name."""
    try:
        mat = scipy.io.loadmat(path)
    except (scipy.io.matlab.MatReadError, NotImplementedError) as exc:
        # NotImplementedError is how scipy turns away v7.3 (HDF5) files.
        raise ValueError(f"{path} cannot be read: {exc}") from exc
    arrays = {k: np.atleast_2d(v) for k, v in mat.items()
              if not k.startswith("__") and isinstance(v, np.ndarray)
              and v.ndim <= 2 and v.size and np.issubdtype(v.dtype, np.number)}
    if not arrays:
        # An aborted run leaves its To File matrix with no samples at all.
        raise ValueError(f"{path} holds no non-empty 2-D numeric array")
    return arrays


def orient(array, orientation):
    """The array as (channel, sample) for the chosen orientation."""
    return array if orientation == "rows" else array.T


def natural_orientation(array):
    """Signals lie along the short dimension of a log."""
    return "rows" if array.shape[0] <= array.shape[1] else "columns"


def is_time_like(row):
    """A time channel rises steadily; a measured signal does not."""
    return row.size > 1 and bool(np.all(np.diff(row) > 0))
