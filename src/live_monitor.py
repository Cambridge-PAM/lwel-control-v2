# src/live_monitor.py

import matplotlib
matplotlib.use("TkAgg")

import matplotlib.pyplot as plt
import numpy as np
from time import perf_counter


class LiveMonitor:

    def __init__(
        self,
        image_shape,
        wavelengths,
        detector_max=None,
        total_measurements=None
    ):

        plt.ion()

        # Create a layout with image (top-left), spectrum (bottom-left)
        # and a right-side text panel that spans both rows.
        self.fig = plt.figure(figsize=(12, 8))
        gs = self.fig.add_gridspec(2, 2, width_ratios=[3, 1])

        self.ax_img = self.fig.add_subplot(gs[0, 0])
        self.ax_spec = self.fig.add_subplot(gs[1, :])
        self.ax_text = self.fig.add_subplot(gs[0, 1])
        self.ax_text.axis("off")

        self.image_artist = self.ax_img.imshow(
            np.zeros(image_shape),
            cmap="gray"
        )

        self.spectrum_artist, = self.ax_spec.plot(
            wavelengths,
            np.zeros_like(wavelengths),
            lw=1
        )

        # Text artist for progress / metrics
        self.text_artist = self.ax_text.text(
            0,
            1,
            "",
            va="top",
            family="monospace",
            fontsize=10
        )

        self.ax_img.set_title("Camera")
        self.ax_spec.set_title("Spectrum")

        self.fig.tight_layout()

        plt.show(block=False)
        plt.pause(0.1)

        # runtime state
        self.start_time = None
        self.frame_idx = 0
        self.detector_max = detector_max
        self.total_measurements = total_measurements

    def start(self):
        self.start_time = perf_counter()
        self.frame_idx = 0

    def stop(self):
        if self.start_time is not None:
            elapsed = perf_counter() - self.start_time
            summary = f"Run complete - elapsed: {elapsed:.1f} s"
            self.text_artist.set_text(summary)
            self.fig.canvas.draw_idle()
            self.fig.canvas.flush_events()
        plt.show(self.fig)

    def update(self, image, spectrum, idx=None, n_measurements=None, elapsed=None):

        # Compute elapsed time if not provided
        if self.start_time is not None and elapsed is None:
            elapsed = perf_counter() - self.start_time

        image_display = image[::4, ::4]

        self.image_artist.set_data(image_display)

        self.image_artist.set_clim(
            image_display.min(),
            image_display.max()
        )

        self.spectrum_artist.set_ydata(spectrum)

        self.ax_spec.relim()
        self.ax_spec.autoscale_view()

        # Compute simple metrics
        try:
            img_mean = float(np.mean(image))
            img_max = float(np.max(image))
            img_min = float(np.min(image))
        except Exception:
            img_mean = img_max = img_min = float("nan")

        try:
            spec_peak = float(np.max(spectrum))
        except Exception:
            spec_peak = float("nan")

        # Build info text
        lines = ["=== Monitoring WEL Formation ==="]
        if elapsed is not None:
            mins = int(elapsed // 60)
            secs = elapsed % 60
            lines.append(f"Elapsed: {mins:d}:{secs:04.1f}")
        else:
            lines.append("Elapsed: -")

        if idx is not None and n_measurements is not None:
            lines.append(f"Measurement: {idx+1}/{n_measurements}")
        elif idx is not None:
            lines.append(f"Measurement: {idx+1}")

        lines.append(f"Image: mean={img_mean:.1f}  max={img_max:.0f}  min={img_min:.0f}")
        lines.append(f"Spectrum peak: {spec_peak:.0f}")

        if self.detector_max is not None and not np.isnan(spec_peak):
            usage = spec_peak / float(self.detector_max) * 100.0
            lines.append(f"Detector usage: {usage:.1f}%")

        info = "\n".join(lines)

        self.text_artist.set_text(info)

        self.fig.canvas.draw_idle()
        self.fig.canvas.flush_events()

        plt.pause(0.001)

        self.frame_idx += 1
