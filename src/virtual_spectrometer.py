# virtual_spectrometer.py

import numpy as np
import time


class VirtualSpectrometer:

    def __init__(self):

        self.integration_time = 10000
        
        self.dark_mode = False

        self.wavelengths = np.linspace(
            350,
            850,
            2048
        )
        
        self.start_time = time.time()


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
            100,
            10,
            len(self.wavelengths)
        )
        
        elapsed = time.time() - self.start_time

        if self.dark_mode:

            counts = noise

        else:

            #Oscillating peak amplitudes
            amp1 = 1.0 + 0.3 * np.sin(2 * np.pi * elapsed / 5)
            amp2 = 0.7 + 0.2 * np.sin(2 * np.pi * elapsed / 8)

            # Slowly shifting peak positions
            center1 = 520 + 10 * np.sin(2 * np.pi * elapsed / 20)
            center2 = 680 + 15 * np.sin(2 * np.pi * elapsed / 30)

            peak1 = amp1 * np.exp(
                -(
                    self.wavelengths - center1
                )**2 / 1000
            )

            peak2 = amp2 * np.exp(
                -(
                    self.wavelengths - center2
                )**2 / 4000
            )

            signal = peak1 + peak2

            scale = (
                self.integration_time
                / 10000
            )

            counts = (
                signal
                * scale
                * 60000
            )

            counts += np.random.normal(
                0,
                150,
                len(counts)
            )

            counts = np.clip(
                counts,
                0,
                65535
            )

        return (
            self.wavelengths,
            counts
        )
