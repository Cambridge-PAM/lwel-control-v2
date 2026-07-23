"""Camera overview plots: mean & max over time and image at interesting timepoint.

Usage: python camera_overview.py <acquisition.h5>
"""
import argparse
import matplotlib.pyplot as plt
import numpy as np
from src.h5_utils import load_h5, elapsed_time
from pathlib import Path
import matplotlib
matplotlib.use('TkAgg')


def main():
    p = argparse.ArgumentParser()
    p.add_argument("run_folder", help="Path to run folder containing acquisition.h5 or path to acquisition.h5")
    args = p.parse_args()

    run_path = Path(args.run_folder)
    if run_path.is_dir():
        h5_file = run_path / "acquisition.h5"
    else:
        h5_file = run_path

    if not h5_file.exists():
        raise FileNotFoundError(f'HDF5 file not found: {h5_file}')

    timestamps, images, wavelengths, spectra = load_h5(h5_file)

    # compute mean and max for each image
    means = np.array([np.nanmean(img) if img is not None else np.nan for img in images])
    maxs = np.array([np.nanmax(img) if img is not None else np.nan for img in images])

    times_min = elapsed_time(timestamps)

    # choose interesting index: where max is maximum (falls back to mean)
    if np.nanmax(maxs) >= np.nanmax(means):
        interesting_idx = int(np.nanargmax(maxs))
    else:
        interesting_idx = int(np.nanargmax(means))

    fig = plt.figure(constrained_layout=True, figsize=(10, 6))
    gs = fig.add_gridspec(2, 2, width_ratios=[2, 1])

    ax_ts = fig.add_subplot(gs[:, 0])
    ax_img = fig.add_subplot(gs[0, 1])
    ax_hist = fig.add_subplot(gs[1, 1])

    ax_ts.plot(times_min, means, label='Mean', color='tab:orange')
    ax_ts.plot(times_min, maxs, label='Max', color='tab:red')
    ax_ts.set_xlabel('Time (min)')
    ax_ts.set_ylabel('Pixel intensity')
    ax_ts.legend()
    ax_ts.grid(True)

    # show interesting image
    img = images[interesting_idx]
    ax_img.imshow(img, cmap='gray')
    ax_img.set_title(f'Image at idx {interesting_idx} (peak)')
    ax_img.axis('off')

    # histogram of pixel intensities at interesting time
    ax_hist.hist(img.ravel(), bins=64, color='gray')
    ax_hist.set_title('Pixel distribution')

    plt.show()


if __name__ == '__main__':
    main()
