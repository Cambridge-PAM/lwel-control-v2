import h5py
import numpy as np
from datetime import datetime
import os


def load_h5(filename):
    """Load timestamps, images, wavelengths and spectra from an acquisition HDF5 file.

    Returns: (timestamps, images, wavelengths, spectra)
    - timestamps: list of datetime objects
    - images: list of numpy arrays
    - wavelengths: list (usually identical per spectrum) of wavelength arrays
    - spectra: list of intensity arrays
    """
    timestamps = []
    images = []
    wavelengths = []
    spectra = []

    if not os.path.exists(filename):
        raise FileNotFoundError(filename)

    with h5py.File(filename, "r") as f:
        # Expect groups named dataset_0, dataset_1, ...
        keys = sorted([k for k in f.keys() if k.startswith("dataset_")])

        for k in keys:
            g = f[k]
            # image
            try:
                img = g["image"][()]
            except Exception:
                img = None

            # spectrum stored as [wavelengths, intensities]
            try:
                spec = g["spectrum"][()]
                # spec may be shape (2, N) or [wl, intens]
                if isinstance(spec, np.ndarray) and spec.dtype == object:
                    wl, intensity = spec
                elif isinstance(spec, np.ndarray) and spec.ndim == 2 and spec.shape[0] == 2:
                    wl = spec[0]
                    intensity = spec[1]
                else:
                    # try indexing
                    wl, intensity = spec[0], spec[1]
            except Exception:
                wl, intensity = None, None

            # timestamp
            ts = None
            try:
                t = g.attrs.get("timestamp")
                if t is not None:
                    ts = datetime.fromisoformat(t)
            except Exception:
                ts = None

            timestamps.append(ts)
            images.append(img)
            wavelengths.append(wl)
            spectra.append(intensity)

    # If any timestamps are present, sort all entries by timestamp so
    # plotting and interactive viewers receive time-ordered data.
    # Entries with missing timestamps are placed after those with valid timestamps,
    # preserving their original relative order.
    if any(t is not None for t in timestamps):
        decorated = []
        for i, t in enumerate(timestamps):
            # sort key: tuples (missing_flag, timestamp or placeholder)
            missing = 1 if t is None else 0
            key_ts = t if t is not None else datetime.max
            decorated.append((missing, key_ts, i))

        decorated.sort()
        order = [item[2] for item in decorated]

        timestamps = [timestamps[i] for i in order]
        images = [images[i] for i in order]
        wavelengths = [wavelengths[i] for i in order]
        spectra = [spectra[i] for i in order]

    return timestamps, images, wavelengths, spectra


def load_reference(filename):
    """Load a reference .npy that contains wavelengths and intensities.

    Attempts to unpack common save formats and returns (wavelengths, intensities).
    """
    data = np.load(filename, allow_pickle=True)

    # Common shapes: (2, N) or array([wl, intens])
    try:
        if isinstance(data, np.ndarray) and data.dtype == object:
            wl, intensity = data
        elif isinstance(data, np.ndarray) and data.ndim == 2 and data.shape[0] == 2:
            wl = data[0]
            intensity = data[1]
        elif isinstance(data, np.ndarray) and data.ndim == 1 and len(data) == 2:
            wl, intensity = data[0], data[1]
        else:
            # fallback: try to split along first axis
            wl = data[0]
            intensity = data[1]
    except Exception:
        raise ValueError(f"Unrecognised reference format: {filename}")

    return wl, intensity


def elapsed_time(timestamps, units="minutes"):
    arr = np.array([(t - timestamps[0]).total_seconds() for t in timestamps])
    if units == "minutes":
        return arr / 60.0
    return arr


def absorbance_from_references(spectra, dark_int, bright_int):
    """Convert raw spectra to absorbance using dark and bright references.

    spectra: (N, M) array-like (N spectra, M wavelengths)
    dark_int, bright_int: arrays of length M
    Returns: absorbance matrix (N, M)
    """
    spectra = np.asarray(spectra)
    dark_int = np.asarray(dark_int)
    bright_int = np.asarray(bright_int)

    denom = bright_int - dark_int
    denom = np.where(np.abs(denom) < 1e-12, np.nan, denom)
    trans = (spectra - dark_int) / denom
    trans = np.clip(trans, 1e-12, None)
    return -np.log10(trans)


def relative_absorbance_change(spectra, dark_int, baseline_spectrum):
    spectra = np.asarray(spectra)
    dark_int = np.asarray(dark_int)
    baseline = np.asarray(baseline_spectrum)

    denom_ref = baseline - dark_int
    denom_ref = np.where(np.abs(denom_ref) < 1e-12, np.nan, denom_ref)
    ratio = (spectra - dark_int) / denom_ref
    ratio = np.clip(ratio, 1e-12, None)
    return -np.log10(ratio)


def integrate_region(wavelengths, values, low=600, high=700):
    wavelengths = np.asarray(wavelengths)
    values = np.asarray(values)
    mask = (wavelengths >= low) & (wavelengths <= high)
    if not np.any(mask):
        raise ValueError("No wavelengths in requested region")
    # values shape (N, M) -> integrate along axis=1
    return np.trapezoid(values[:, mask], wavelengths[mask], axis=1)
