"""Create a publication-style plot of scattering over time with three images.

Usage: python publication_plot.py <acquisition.h5> --dark dark.npy --bright bright.npy
"""
import argparse
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import gridspec
from src.h5_utils import load_h5, load_reference, absorbance_from_references, integrate_region, elapsed_time
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

    run_path = Path(args.run_folder)
    if run_path.is_dir():
        h5_file = run_path / "acquisition.h5"
        base_dir = run_path.parent.parent
        sample_id = run_path.parent.name
    else:
        h5_file = run_path
        base_dir = h5_file.parent.parent
        sample_id = h5_file.parent.name

    if not h5_file.exists():
        raise FileNotFoundError(f"HDF5 file not found: {h5_file}")

    timestamps, images, wavelengths, spectra = load_h5(h5_file)
    wl = np.asarray(wavelengths[0])
    spec_matrix = np.asarray(spectra)

    # Determine dark/bright references
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

    # scattering outside [low, high]
    scatter_low = integrate_region(wl, abs_matrix, low=wl.min(), high=args.low - 1)
    scatter_high = integrate_region(wl, abs_matrix, low=args.high + 1, high=wl.max())
    scattering = scatter_low + scatter_high

    times_min = elapsed_time(timestamps)

    # indices for images
    idx_first = 0
    idx_last = len(scattering) - 1
    idx_min = int(np.nanargmin(scattering))

    # colormap for points
    cmap = plt.get_cmap('viridis')
    norm = plt.Normalize(times_min.min(), times_min.max())
    colors = cmap(norm(times_min))

    fig = plt.figure(figsize=(10, 8))
    gs = gridspec.GridSpec(3, 3, height_ratios=[2, 1, 1])

    ax_scatter = fig.add_subplot(gs[0, :])
    ax_scatter.scatter(times_min, scattering, c=colors, s=40)
    ax_scatter.set_ylabel('Integrated scattering')
    ax_scatter.set_xlabel('Time (min)')
    ax_scatter.grid(True)

    # pick colors for selected indices
    c_first = cmap(norm(times_min[idx_first]))
    c_min = cmap(norm(times_min[idx_min]))
    c_last = cmap(norm(times_min[idx_last]))

    # image axes
    ax_img1 = fig.add_subplot(gs[1, 0])
    ax_img2 = fig.add_subplot(gs[1, 1])
    ax_img3 = fig.add_subplot(gs[1, 2])

    # show images with color-coded borders
    for ax, idx, col, title in [(ax_img1, idx_first, c_first, 'First'), (ax_img2, idx_min, c_min, 'Min scattering'), (ax_img3, idx_last, c_last, 'Last')]:
        img = images[idx]
        ax.imshow(img, cmap='gray')
        ax.set_title(f"{title} (idx {idx})")
        ax.axis('off')
        # color the spine
        for spine in ax.spines.values():
            spine.set_edgecolor(col)
            spine.set_linewidth(4)

    # add a colorbar matching time
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax_scatter, orientation='vertical', pad=0.02)
    cbar.set_label('Time (min)')

    plt.tight_layout()
    plt.show()


if __name__ == '__main__':
    main()
