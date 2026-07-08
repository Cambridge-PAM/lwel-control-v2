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

        keys = sorted(
            f.keys(),
            key=lambda x: int(
                x.split("_")[-1]
            )
        )

        for key in keys:

            group = f[key]

            images.append(
                group["image"][()]
            )

            spec = group[
                "spectrum"
            ][()]

            wavelengths.append(
                spec[0]
            )

            spectra.append(
                spec[1]
            )

            timestamps.append(
                datetime.fromisoformat(
                    group.attrs[
                        "timestamp"
                    ]
                )
            )

    return (
        timestamps,
        images,
        wavelengths,
        spectra
    )


def load_reference(filename):

    data = np.load(filename)

    return (
        data[0],
        data[1]
    )
    

def elapsed_time(
    timestamps,
    units="minutes"
):


    t0 = timestamps[0]

    elapsed = np.array([
        (t - t0).total_seconds()
        for t in timestamps
    ])

    if units == "minutes":
        return elapsed / 60.0

    return elapsed


def plot_spectral_heatmap(
    h5_file,
    dark_reference,
    bright_reference
):

    (
        timestamps,
        images,
        wavelengths,
        spectra
    ) = load_h5(h5_file)

    n_spectra = len(spectra)

    if n_spectra < 1:

        raise RuntimeError(
            "No spectra found."
        )

    wl = np.asarray(
        wavelengths[0]
    )

    spectral_matrix = np.asarray(
        spectra
    )

    if spectral_matrix.ndim == 1:

        spectral_matrix = spectral_matrix[
            np.newaxis, :
        ]

    elapsed_min = np.array([
        (
            t - timestamps[0]
        ).total_seconds() / 60.0
        for t in timestamps
    ])

    #################################################
    # REFERENCES
    #################################################

    dark_wl, dark_int = (
        load_reference(
            dark_reference
        )
    )

    bright_wl, bright_int = (
        load_reference(
            bright_reference
        )
    )

    #################################################
    # REFERENCE CORRECTION
    #################################################

    denominator = (
        bright_int - dark_int
    )

    denominator = np.where(
        np.abs(denominator) < 1e-12,
        np.nan,
        denominator
    )

    corrected = (
        spectral_matrix - dark_int
    ) / denominator

    corrected_initial = (
        corrected[0]
    )

    relative_change = (
        corrected -
        corrected_initial
    )

    #################################################
    # FIGURE
    #################################################

    fig = plt.figure(
        figsize=(14, 12)
    )

    gs = fig.add_gridspec(
        3,
        2,
        width_ratios=[30, 1],
        height_ratios=[1.2, 3, 2]
    )

    ax_ref = fig.add_subplot(
        gs[0, 0]
    )

    ax_heat = fig.add_subplot(
        gs[1, 0],
        sharex=ax_ref
    )

    ax_change = fig.add_subplot(
        gs[2, 0],
        sharex=ax_ref
    )

    cax = fig.add_subplot(
        gs[1, 1]
    )

    #################################################
    # PANEL 1
    #################################################

    ax_ref.plot(
        dark_wl,
        dark_int,
        "k--",
        linewidth=2,
        label="Dark Reference"
    )

    ax_ref.plot(
        bright_wl,
        bright_int,
        "r--",
        linewidth=2,
        label="Bright Reference"
    )

    ax_ref.plot(
        wl,
        spectral_matrix[0],
        "b",
        linewidth=2,
        label="First Spectrum"
    )

    ax_ref.plot(
        wl,
        spectral_matrix[-1],
        "g",
        linewidth=2,
        label="Last Spectrum"
    )

    ax_ref.set_ylabel(
        "Counts"
    )

    ax_ref.set_title(
        "References and Measured Spectra"
    )

    ax_ref.legend()

    ax_ref.grid(True)

    #################################################
    # PANEL 2
    #################################################

    ymax = max(
        elapsed_min[-1],
        elapsed_min[0] + 1e-6
    )

    heat = ax_heat.imshow(
        spectral_matrix,
        aspect="auto",
        origin="lower",
        extent=[
            wl[0],
            wl[-1],
            elapsed_min[0],
            ymax
        ],
        vmin=np.nanpercentile(
            spectral_matrix,
            1
        ),
        vmax=np.nanpercentile(
            spectral_matrix,
            99
        )
    )

    ax_heat.set_ylabel(
        "Elapsed Time (min)"
    )

    ax_heat.set_title(
        "Spectral Evolution"
    )

    cb = fig.colorbar(
        heat,
        cax=cax
    )

    cb.set_label(
        "Counts"
    )

    #################################################
    # PANEL 3
    #################################################

    rel_range = np.nanmax(
        np.abs(relative_change)
    )

    im2 = ax_change.imshow(
        relative_change,
        aspect="auto",
        origin="lower",
        extent=[
            wl[0],
            wl[-1],
            elapsed_min[0],
            ymax
        ],
        cmap="RdBu_r",
        vmin=-rel_range,
        vmax=rel_range
    )

    ax_change.set_title(
        "Relative Change from Initial Spectrum\n"
        "(Reference Corrected)"
    )

    ax_change.set_xlabel(
        "Wavelength (nm)"
    )

    ax_change.set_ylabel(
        "Elapsed Time (min)"
    )

    cbar2 = fig.colorbar(
        im2,
        ax=ax_change
    )

    cbar2.set_label(
        "Δ Relative Intensity"
    )

    plt.tight_layout()

    plt.show()

def interactive_browser(
    h5_file,
    dark_reference=None,
    bright_reference=None
):

    (
        timestamps,
        images,
        wavelengths,
        spectra
    ) = load_h5(h5_file)
    
    
    elapsed_sec = elapsed_time(
        timestamps,
        units="seconds"
    )
    
    elapsed_min = elapsed_sec/60.0

    dark_wl = None
    dark_int = None

    bright_wl = None
    bright_int = None

    if dark_reference is not None:

        dark_wl, dark_int = (
            load_reference(
                dark_reference
            )
        )

    if bright_reference is not None:

        bright_wl, bright_int = (
            load_reference(
                bright_reference
            )
        )

    idx0 = 0

    fig = plt.figure(
        figsize=(14, 7)
    )

    gs = fig.add_gridspec(
        2,
        2,
        height_ratios=[20, 1]
    )

    ax_image = fig.add_subplot(
        gs[0, 0]
    )

    ax_spec = fig.add_subplot(
        gs[0, 1]
    )

    image_artist = ax_image.imshow(
        images[idx0],
        cmap="gray"
    )

    ax_image.set_title(
        f"t = {elapsed_sec} s"
        f"({elapsed_min[idx0]:.2f} min)"
    )

    spec_artist, = ax_spec.plot(
        wavelengths[idx0],
        spectra[idx0],
        linewidth=2,
        label="Spectrum"
    )

    if dark_wl is not None:

        ax_spec.plot(
            dark_wl,
            dark_int,
            "--k",
            alpha=0.7,
            label="Dark"
        )

    if bright_wl is not None:

        ax_spec.plot(
            bright_wl,
            bright_int,
            "--r",
            alpha=0.7,
            label="Bright"
        )

    ax_spec.set_xlabel(
        "Wavelength (nm)"
    )

    ax_spec.set_ylabel(
        "Counts"
    )

    ax_spec.legend()

    ax_spec.grid(True)

    slider_ax = fig.add_subplot(
        gs[1, :]
    )

    slider = Slider(
        ax=slider_ax,
        label="Dataset",
        valmin=0,
        valmax=len(images) - 1,
        valinit=0,
        valstep=1
    )

    
    def update(val):

        idx = int(slider.val)

        image_artist.set_data(
            images[idx]
        )

        spec_artist.set_data(
            wavelengths[idx],
            spectra[idx]
        )

        ax_image.set_title(
            f"t = {elapsed_sec} s "
            f"({elapsed_min} min)"
        )

        ax_spec.relim()
        ax_spec.autoscale_view()

        fig.canvas.draw_idle()


    slider.on_changed(
        update
    )

    plt.tight_layout()
    plt.show()
    

if __name__ == "__main__":

    if len(sys.argv) != 2:
        print("Usage: python plot_h5_data.py <sample_run_folder>")
        print("Example: python plot_h5_data.py data/sample_001/run_001")
        sys.exit(1)

    run_folder = Path(sys.argv[1])

    if not run_folder.exists():
        raise FileNotFoundError(f"Folder not found: {run_folder}")

    BASE_DIR = run_folder.parent.parent
    SAMPLE_ID = run_folder.parent.name
    RUN_ID = run_folder.name

    H5_FILE = run_folder / "acquisition.h5"

    if not H5_FILE.exists():
        raise FileNotFoundError(f"HDF5 file not found: {H5_FILE}")

    DARK = BASE_DIR / SAMPLE_ID / "dark_reference.npy"
    BRIGHT = BASE_DIR / SAMPLE_ID / "bright_reference.npy"

    if not DARK.exists() or not BRIGHT.exists():
        raise FileNotFoundError("Dark or bright reference file not found.")

    plot_spectral_heatmap(
        H5_FILE,
        DARK,
        BRIGHT
    )

    interactive_browser(
        H5_FILE,
        DARK,
        BRIGHT
    )