import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from matplotlib.widgets import Slider
import sys
import matplotlib
matplotlib.use('TkAgg')

from src.h5_utils import (
    load_h5,
    load_reference,
    absorbance_from_references,
    relative_absorbance_change,
    integrate_region,
    elapsed_time,
)

def interactive_browser(h5_file, dark_reference=None, bright_reference=None):
    timestamps, images, wavelengths, spectra = load_h5(h5_file)
    print(f"Loaded {len(spectra)} spectra from {h5_file}")
    if len(spectra) == 0:
        raise ValueError("No spectra found in file")

    wl = np.asarray(wavelengths[0])
    spec_matrix = np.asarray(spectra)

    dark_wl, dark_int = (None, None)
    bright_wl, bright_int = (None, None)

    if dark_reference and bright_reference:
        dark_wl, dark_int = load_reference(dark_reference)
        bright_wl, bright_int = load_reference(bright_reference)
        abs_matrix = absorbance_from_references(spec_matrix, dark_int, bright_int)
    else:
        abs_matrix = None

    times_min = elapsed_time(timestamps)

    idx0 = 0

    fig = plt.figure(figsize=(12, 8))
    gs = fig.add_gridspec(3, 2, height_ratios=[3, 3, 0.2])

    ax_img = fig.add_subplot(gs[0, 0])
    ax_spec = fig.add_subplot(gs[1, 0])
    ax_meta = fig.add_subplot(gs[:, 1])
    ax_slider = fig.add_subplot(gs[2, 0])

    img_artist = ax_img.imshow(images[idx0], cmap='gray')
    ax_img.set_title('Image')

    # Primary axis: raw counts
    spec_artist, = ax_spec.plot(wl, spec_matrix[idx0], label='Counts', color='C0')
    ax_spec.set_xlabel('Wavelength (nm)')
    ax_spec.set_ylabel('Counts', color='C0')
    ax_spec.tick_params(axis='y', labelcolor='C0')
    ax_spec.set_xlim(400,800)


    # Secondary axis: absorbance (if available)
    ax_spec_right = ax_spec.twinx()
    absorbance_line = None
    if abs_matrix is not None:
        absorbance_line, = ax_spec_right.plot(wl, abs_matrix[idx0], label='Absorbance', color='C1', alpha = 0.5)
    ax_spec_right.set_ylabel('Absorbance', color='C1')
    ax_spec_right.tick_params(axis='y', labelcolor='C1')
    ax_spec_right.set_ylim(-1,1.5)
    ax_spec.set_ylim(0, 70000)

    # Combined legend from both axes
    handles = []
    labels = []
    h1, l1 = ax_spec.get_legend_handles_labels()
    h2, l2 = ax_spec_right.get_legend_handles_labels()
    handles.extend(h1)
    handles.extend(h2)
    labels.extend(l1)
    labels.extend(l2)
    if handles:
        ax_spec.legend(handles, labels)
        ax_spec.legend(loc='upper center', bbox_to_anchor=(0.5, 1.05),
          ncol=2, fancybox=True, shadow=True)


    ax_meta.axis('off')
    text = ax_meta.text(0, 1, '', va='top', family='monospace', fontsize=10)

    slider = Slider(ax_slider, 'Index', 0, len(spectra) - 1, valinit=idx0, valstep=1)
    print("Set up axes")
    def update(val):
        i = int(slider.val)
        img = images[i]
        img_artist.set_data(img)
        img_artist.set_clim(img.min(), img.max())

        spec_artist.set_ydata(spec_matrix[i])
        if absorbance_line is not None:
            absorbance_line.set_ydata(abs_matrix[i])

        lines = [f'Index: {i} / {len(spectra)-1}']
        if timestamps and len(timestamps) > i:
            lines.append(f'Time: {timestamps[i].isoformat()}')
            lines.append(f'Elapsed (min): {times_min[i]:.2f}')

        text.set_text('\n'.join(lines))

        # Rescale both axes
        try:
            ax_spec.relim()
            ax_spec.autoscale_view()
        except Exception:
            pass
        try:
            ax_spec_right.relim()
            ax_spec_right.autoscale_view()
        except Exception:
            pass
        print("Updated axes")
        fig.canvas.draw_idle()

    slider.on_changed(update)

    # Allow left/right arrow keys to move the slider
    def on_key(event):
        try:
            key = event.key
        except Exception:
            return

        if key not in ("left", "right"):
            return

        cur = int(slider.val)
        if key == "left":
            new = max(0, cur - 1)
        else:
            new = min(len(spectra) - 1, cur + 1)

        if new != cur:
            slider.set_val(new)

    cid = fig.canvas.mpl_connect('key_press_event', on_key)

    plt.tight_layout()
    print("Showing axes")
    plt.show()


def main():
    if len(sys.argv) != 2:
        print('Usage: python plot_h5_data.py <sample_run_folder>')
        print('Example: python plot_h5_data.py data/sample_001/run_20260708_111348')
        sys.exit(1)

    run_folder = Path(sys.argv[1])
    if not run_folder.exists():
        raise FileNotFoundError(f'Folder not found: {run_folder}')

    h5_file = run_folder / 'acquisition.h5'
    if not h5_file.exists():
        raise FileNotFoundError(f'HDF5 file not found: {h5_file}')

    base_dir = run_folder.parent.parent
    sample_id = run_folder.parent.name
    dark_reference = base_dir / sample_id / 'dark_reference.npy'
    bright_reference = base_dir / sample_id / 'bright_reference.npy'

    if not dark_reference.exists() or not bright_reference.exists():
        raise FileNotFoundError('Dark or bright reference file not found.')

    print("Before interactive browser")
    interactive_browser(h5_file, dark_reference, bright_reference)

if __name__ == '__main__':
    main()
