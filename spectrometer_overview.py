"""Spectrometer overview plots.

Usage: python spectrometer_overview.py <acquisition.h5> --dark dark.npy --bright bright.npy
"""
import argparse
import matplotlib.pyplot as plt
import numpy as np
from src.h5_utils import load_h5, load_reference, absorbance_from_references, relative_absorbance_change, integrate_region, elapsed_time
from pathlib import Path
import matplotlib
matplotlib.use('TkAgg')

def main():
    p = argparse.ArgumentParser()
    p.add_argument("run_folder", help="Path to run folder containing acquisition.h5 or path to acquisition.h5")
    p.add_argument("--dark", required=False, help="Path to dark reference .npy (optional)")
    p.add_argument("--bright", required=False, help="Path to bright reference .npy (optional)")
    p.add_argument("--low", type=float, default=600.0)
    p.add_argument("--high", type=float, default=700.0)
    args = p.parse_args()

    # Resolve input: allow either a run folder or direct h5 file path
    run_path = Path(args.run_folder)
    if run_path.is_dir():
        h5_file = run_path / "acquisition.h5"
        base_dir = run_path.parent.parent
        sample_id = run_path.parent.name
    else:
        # assume user passed the h5 file directly
        h5_file = run_path
        base_dir = h5_file.parent.parent
        sample_id = h5_file.parent.name

    if not h5_file.exists():
        raise FileNotFoundError(f"HDF5 file not found: {h5_file}")

    timestamps, images, wavelengths, spectra = load_h5(h5_file)
    wl = np.asarray(wavelengths[0])
    spec_matrix = np.asarray(spectra)

    # Determine dark/bright references: prefer CLI args, else look next to sample folder
    if args.dark:
        dark_ref = Path(args.dark)
    else:
        dark_ref = base_dir / sample_id / 'dark_reference.npy'

    if args.bright:
        bright_ref = Path(args.bright)
    else:
        bright_ref = base_dir / sample_id / 'bright_reference.npy'

    if not dark_ref.exists() or not bright_ref.exists():
        raise FileNotFoundError('Dark or bright reference file not found. Provide with --dark/--bright or place them in the sample folder.')

    dark_wl, dark_int = load_reference(dark_ref)
    bright_wl, bright_int = load_reference(bright_ref)

    abs_matrix = absorbance_from_references(spec_matrix, dark_int, bright_int)
    rel_matrix = relative_absorbance_change(spec_matrix, dark_int, spec_matrix[0])

    # scattering defined as absorbance outside [low, high]
    low_edge = wl.min()
    high_edge = wl.max()
    scatter_low = integrate_region(wl, abs_matrix, low=low_edge, high=args.low - 1)
    scatter_high = integrate_region(wl, abs_matrix, low=args.high + 1, high=high_edge)
    scattering = scatter_low + scatter_high

    times_min = elapsed_time(timestamps)

    fig, axes = plt.subplots(3, 1, figsize=(10, 12), sharex=True)

    # 1) Absorbance overview: first and last
    axes[0].plot(wl, abs_matrix[0], label='First', color='tab:blue')
    axes[0].plot(wl, abs_matrix[-1], label='Last', color='tab:green')
    axes[0].set_xlim(350, 850)
    axes[0].set_ylabel('Absorbance')
    axes[0].legend()
    axes[0].grid(True)

    # 2) Relative absorbance heatmap (time x wavelength)
    im = axes[1].imshow(rel_matrix, aspect='auto', extent=[wl[0], wl[-1], times_min[-1], times_min[0]], cmap='viridis')
    axes[1].set_ylabel('Time (min)')
    axes[1].set_title('Relative Absorbance (first spectrum as baseline)')
    fig.colorbar(im, ax=axes[1], label='Delta Abs')

    # 3) Scattering over time
    axes[2].plot(times_min, scattering, marker='o', color='tab:purple')
    axes[2].set_xlabel('Time (min)')
    axes[2].set_ylabel('Integrated scattering (outside {low}-{high} nm)'.format(low=int(args.low), high=int(args.high)))
    axes[2].grid(True)

    plt.tight_layout()
    plt.show()


if __name__ == '__main__':
    main()
