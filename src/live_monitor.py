# src/live_monitor.py

import matplotlib
matplotlib.use("TkAgg")

import matplotlib.pyplot as plt
import numpy as np

class LiveMonitor:

    def __init__(self, image_shape, wavelengths):

        plt.ion()

        self.fig, (self.ax_img, self.ax_spec) = plt.subplots(
            2,
            1,
            figsize=(10, 8)
        )

        self.image_artist = self.ax_img.imshow(
            np.zeros(image_shape),
            cmap="gray"
        )

        self.spectrum_artist, = self.ax_spec.plot(
            wavelengths,
            np.zeros_like(wavelengths),
            lw=1
        )

        self.ax_img.set_title("Camera")
        self.ax_spec.set_title("Spectrum")

        self.fig.tight_layout()

        plt.show(block=False)
        plt.pause(0.1)

    def start(self):
        pass

    def stop(self):
        plt.close(self.fig)

    def update(self, image, spectrum):

        image_display = image[::4, ::4]

        self.image_artist.set_data(image_display)

        self.image_artist.set_clim(
            image_display.min(),
            image_display.max()
        )

        self.spectrum_artist.set_ydata(
            spectrum
        )

        self.ax_spec.relim()
        self.ax_spec.autoscale_view()

        self.fig.canvas.draw_idle()
        self.fig.canvas.flush_events()

        plt.pause(0.001)
