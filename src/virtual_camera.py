# virtual_camera.py

import numpy as np

class VirtualCamera:

    def __init__(self):

        self.exposure = 0.05

        self.roi = (
            100,
            1440,
            4,
            1080,
            1,
            1
        )

        self.acquiring = False

    #################################################
    # Basic Camera Functions
    #################################################

    def open(self):
        pass

    def close(self):
        pass

    def set_exposure(self, exposure):
        self.exposure = exposure

    def get_exposure(self):
        return self.exposure

    def set_roi(self, *roi):
        self.roi = roi

    def get_roi(self):
        return self.roi

    #################################################
    # Image Generator
    #################################################

    def _generate_image(self):

        h = 1024
        w = 1280

        x, y = np.meshgrid(
            np.arange(w),
            np.arange(h)
        )

        blob = np.exp(
            -(
                (x - 650) ** 2 +
                (y - 500) ** 2
            )
            / 100000
        )

        scale = self.exposure / 0.05

        image = (
            blob
            * scale
            * 255
        )

        image += np.random.normal(
            0,
            15,
            image.shape
        )

        image = np.clip(
            image,
            0,
            255
        )

        return image.astype(
            np.uint8
        )

    #################################################
    # Snapshot Interface
    #################################################

    def snap(self):

        return self._generate_image()

    def grab(self, n=1):

        return [
            self._generate_image()
        ]

    #################################################
    # Acquisition Interface
    #################################################

    def setup_acquisition(
        self,
        nframes=100
    ):
        self.nframes = nframes

    def start_acquisition(self):
        self.acquiring = True

    def stop_acquisition(self):
        self.acquiring = False

    def wait_for_frame(self):
        pass

    def read_oldest_image(self):

        return self._generate_image()