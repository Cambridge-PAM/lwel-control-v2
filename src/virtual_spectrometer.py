# virtual_spectrometer.py

import numpy as np


class VirtualSpectrometer:

    def __init__(self):

        self.integration_time = 10000
        
        self.dark_mode = False

        self.wavelengths = np.linspace(
            350,
            850,
            2048
        )

    def integration_time_micros(
        self,
        value
    ):
        self.integration_time = value
            
    def enable_dark_mode(self):
        self.dark_mode = True

    def disable_dark_mode(self):
        self.dark_mode = False

    def spectrum(
        self,
        correct_nonlinearity=True
    ):
        
        noise = np.random.normal(
            50,
            10,
            len(self.wavelengths)
        )
        
        if self.dark_mode:

            counts = noise

        else:

            peak1 = np.exp(
                -(
                    self.wavelengths - 520
                )**2
                / 1000
            )

            peak2 = np.exp(
                -(
                    self.wavelengths - 680
                )**2
                / 4000
            )

            signal = (
                peak1 +
                0.7*peak2
            )

            scale = (
                self.integration_time
                / 10000
            )

            counts = (
                signal
                * scale
                * 60000
            )

            noise = np.random.normal(
                0,
                150,
                len(counts)
            )

            counts += noise

            counts = np.clip(
                counts,
                0,
                65535
            )

        return (
            self.wavelengths,
            counts
        )