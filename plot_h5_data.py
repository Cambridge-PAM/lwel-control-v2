import h5py
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from matplotlib.widgets import Slider
from datetime import datetime
import sys


def load_h5(filename):
    timestamps = []
    images = []
    wavelengths = []
    spectra = []

    with h5py.File(filename, "r") as f:
        keys = sorted(f.keys(), key=lambda x: int(x.split("_")[-1]))
        for key in keys:
            group = f[key]
            img = group["image"][()]

            if isinstance(img, np.ndarray) and img.ndim == 3:
                if img.shape[-1] == 3:
                    img = (0.2989 * img[..., 0] + 0.5870 * img[..., 1] + 0.1140 * img[..., 2])
                elif img.shape[0] == 3:
                    img = (0.2989 * img[0] + 0.5870 * img[1] + 0.1140 * img[2])

            images.append(img)
            spec = group["spectrum"][()]
            wavelengths.append(np.asarray(spec[0]))
            spectra.append(np.asarray(spec[1]))
            timestamps.append(datetime.fromisoformat(group.attrs["timestamp"]))

    return timestamps, images, wavelengths, spectra


def load_reference(filename):
    data = np.load(filename)
    return data[0], data[1]


def elapsed_time(timestamps, units="minutes"):
    elapsed = np.array([ (t - timestamps[0]).total_seconds() for t in timestamps ])
    if units == "minutes":
        return elapsed / 60.0
    return elapsed


def absorbance_from_references(spectra, dark_int, bright_int):
    denom = bright_int - dark_int
    denom = np.where(np.abs(denom) < 1e-12, np.nan, denom)
    trans = (spectra - dark_int) / denom
    trans = np.clip(trans, 1e-12, None)
    return -np.log10(trans)


def relative_absorbance_change(spectra, dark_int, baseline_spectrum):
    denom_ref = baseline_spectrum - dark_int
    denom_ref = np.where(np.abs(denom_ref) < 1e-12, np.nan, denom_ref)
    ratio = (spectra - dark_int) / denom_ref
    ratio = np.clip(ratio, 1e-12, None)
    return -np.log10(ratio)


def integrate_region(wavelengths, values, low=600, high=700):
    mask = (wavelengths >= low) & (wavelengths <= high)
    if not np.any(mask):
        raise ValueError(f"No wavelength points found in {low}-{high} nm")
    return np.trapezoid(values[:, mask], wavelengths[mask], axis=1)


def plot_spectrometer_summary(h5_file, dark_reference, bright_reference):
    timestamps, images, wavelengths, spectra = load_h5(h5_file)
    if len(spectra) == 0:
        raise RuntimeError("No spectra found.")
    
    wavelengthMin = 400
    wavelengthMax = 750

    wl = np.asarray(wavelengths[0])
    spec_matrix = np.asarray(spectra)
    elapsed_min = elapsed_time(timestamps, units="minutes")

    dark_wl, dark_int = load_reference(dark_reference)
    bright_wl, bright_int = load_reference(bright_reference)

    abs_matrix = absorbance_from_references(spec_matrix, dark_int, bright_int)
    rel_abs_matrix = relative_absorbance_change(spec_matrix, dark_int, spec_matrix[0])
    integrated_abs = integrate_region(wl, abs_matrix, low=600, high=700)
    integrated_change = integrated_abs - integrated_abs[0]

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    ax_refs, ax_abs, ax_rel, ax_integ = axes.flatten()

    ax_refs.plot(dark_wl, dark_int, "k--", linewidth=2, label="Dark Reference")
    ax_refs.plot(bright_wl, bright_int, "r--", linewidth=2, label="Bright Reference")
    ax_refs.plot(wl, spec_matrix[0], "b-", linewidth=1.5, label="First Spectrum")
    ax_refs.plot(wl, spec_matrix[-1], "g-", linewidth=1.5, label="Last Spectrum")
    ax_refs.set_title("Raw Spectra and References")
    ax_refs.set_xlim(wavelengthMin, wavelengthMax)
    ax_refs.set_xlabel("Wavelength (nm)")
    ax_refs.set_ylabel("Counts")
    ax_refs.legend(loc="best")
    ax_refs.grid(True)

    ax_abs.plot(wl, abs_matrix[0], label="First Absorbance")
    ax_abs.plot(wl, abs_matrix[-1], label="Last Absorbance")
    ax_abs.axvspan(600, 700, color="gray", alpha=0.15, label="600-700 nm region")
    ax_abs.set_title("Material Absorbance (bright/dark corrected)")
    ax_abs.set_xlim(wavelengthMin, wavelengthMax)
    ax_abs.set_xlabel("Wavelength (nm)")
    ax_abs.set_ylabel("Absorbance")
    ax_abs.legend(loc="best")
    ax_abs.grid(True)

    rel_change = rel_abs_matrix - rel_abs_matrix[0]
    vlim = np.nanmax(np.abs(rel_change))
    im = ax_rel.imshow(
        rel_change,
        aspect="auto",
        origin="lower",
        extent=[wl[0], wl[-1], elapsed_min[0], elapsed_min[-1]],
        cmap="RdBu_r",
        vmin=-vlim,
        vmax=vlim,
    )
    ax_rel.set_title("Relative Absorbance Change vs First Spectrum")
    ax_rel.set_xlim(wavelengthMin, wavelengthMax)
    ax_rel.set_xlabel("Wavelength (nm)")
    ax_rel.set_ylabel("Elapsed Time (min)")
    fig.colorbar(im, ax=ax_rel, label="Δ Absorbance")

    ax_integ.plot(elapsed_min, integrated_change, "-o", color="tab:purple")
    ax_integ.set_title("Integrated Absorbance Change (600-700 nm)")
    ax_integ.set_xlabel("Elapsed Time (min)")
    ax_integ.set_ylabel("Δ Integrated Absorbance")
    ax_integ.grid(True)

    fig.tight_layout()
    plt.show()


def interactive_browser(h5_file, dark_reference=None, bright_reference=None):
    timestamps, images, wavelengths, spectra = load_h5(h5_file)
    if len(images) == 0:
        raise RuntimeError("No images found.")

    wl = np.asarray(wavelengths[0])
    spec_matrix = np.asarray(spectra)
    elapsed_min = elapsed_time(timestamps, units="minutes")

    abs_matrix = None
    integrated_abs = None

    if dark_reference is not None and bright_reference is not None:
        dark_wl, dark_int = load_reference(dark_reference)
        bright_wl, bright_int = load_reference(bright_reference)
        abs_matrix = absorbance_from_references(spec_matrix, dark_int, bright_int)
        integrated_abs = integrate_region(wl, abs_matrix, low=600, high=700)

    fig = plt.figure(figsize=(16, 8))
    gs = fig.add_gridspec(2, 2, height_ratios=[20, 1])
    ax_image = fig.add_subplot(gs[0, 0])
    ax_spec = fig.add_subplot(gs[0, 1])
    ax_slider = fig.add_subplot(gs[1, :])

    img_artist = ax_image.imshow(images[0], cmap="gray", aspect="auto")
    ax_image.axis("off")

    spectrum_line, = ax_spec.plot(wl, spec_matrix[0], color="tab:blue", label="Spectrum")
    absorbance_line = None
    if abs_matrix is not None:
        absorbance_line, = ax_spec.plot(wl, abs_matrix[0], color="tab:orange", label="Absorbance")

    info_text = ax_spec.text(
        0.02,
        0.95,
        "",
        transform=ax_spec.transAxes,
        va="top",
        fontsize=10,
        bbox={"facecolor": "white", "alpha": 0.8, "edgecolor": "black"},
    )

    ax_spec.set_xlabel("Wavelength (nm)")
    ax_spec.set_ylabel("Counts / Absorbance")
    legend_handles = [spectrum_line]
    legend_labels = ["Spectrum"]
    if absorbance_line is not None:
        legend_handles.append(absorbance_line)
        legend_labels.append("Absorbance")
    ax_spec.legend(legend_handles, legend_labels, loc="best")
    ax_spec.grid(True)

    slider = Slider(
        ax=ax_slider,
        label="Dataset index",
        valmin=0,
        valmax=len(images) - 1,
        valinit=0,
        valstep=1,
    )

    def update(val):
        idx = int(slider.val)
        img_artist.set_data(images[idx])
        spectrum_line.set_ydata(spec_matrix[idx])
        if absorbance_line is not None:
            absorbance_line.set_ydata(abs_matrix[idx])

        elapsed = elapsed_min[idx]
        info_lines = [
            f"Index: {idx}",
            f"Timestamp: {timestamps[idx].isoformat()}",
            f"Elapsed: {elapsed:.2f} min",
            f"Spectrum max: {np.nanmax(spec_matrix[idx]):.1f}",
        ]
        if abs_matrix is not None:
            info_lines.append(f"Absorbance max: {np.nanmax(abs_matrix[idx]):.3f}")
            info_lines.append(f"Integrated 600-700 nm: {integrated_abs[idx]:.4f}")
        info_text.set_text("\n".join(info_lines))

        ax_image.set_title(f"Image {idx} | {elapsed:.2f} min")
        ax_spec.relim()
        ax_spec.autoscale_view()
        fig.canvas.draw_idle()

    slider.on_changed(update)
    update(0)
    plt.tight_layout()
    plt.show()


def main():
    if len(sys.argv) != 2:
        print("Usage: python plot_h5_data.py <sample_run_folder>")
        print("Example: python plot_h5_data.py data/sample_001/20260708_111348")
        sys.exit(1)

    run_folder = Path(sys.argv[1])
    if not run_folder.exists():
        raise FileNotFoundError(f"Folder not found: {run_folder}")

    h5_file = run_folder / "acquisition.h5"
    if not h5_file.exists():
        raise FileNotFoundError(f"HDF5 file not found: {h5_file}")

    base_dir = run_folder.parent.parent
    sample_id = run_folder.parent.name
    dark_reference = base_dir / sample_id / "dark_reference.npy"
    bright_reference = base_dir / sample_id / "bright_reference.npy"

    if not dark_reference.exists() or not bright_reference.exists():
        raise FileNotFoundError("Dark or bright reference file not found.")

    plot_spectrometer_summary(h5_file, dark_reference, bright_reference)
    interactive_browser(h5_file, dark_reference, bright_reference)


if __name__ == "__main__":
    main()
