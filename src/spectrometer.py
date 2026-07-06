from seabreeze.spectrometers import (
    list_devices,
    Spectrometer
)

import numpy as np


def connect_spectrometer():

    return Spectrometer(
        list_devices()[0]
    )


def acquire_spectrum(spec):

    return spec.spectrum(
        correct_nonlinearity=True
    )


def set_integration(
    spec,
    integration_time_us):

    spec.integration_time_micros(
        int(integration_time_us)
    )
    
    
def peak_counts(intensity):

    return np.max(intensity)


def spectrometer_metrics(
    intensity,
    detector_max=65535
):
    peak = np.max(intensity)

    detector_usage = (
        peak / detector_max
    )

    return {
        "peak_counts": float(peak),
        "detector_usage": float(detector_usage * 100),
        "saturated": peak >= detector_max
    }
    

def auto_integration_time(
        spec,
        target_fraction=0.75,
        detector_max=65535,
        min_time=1000,
        max_time=1000000,
        max_iterations=100
):

    target = (
        target_fraction
        * detector_max
    )

    integration = 1000

    for _ in range(max_iterations):

        spec.integration_time_micros(
            int(integration)
        )

        wl, intensity = (
            acquire_spectrum(spec)
        )

        peak = np.max(intensity)

        print(
            f"Time={integration:.0f} us "
            f"Peak={peak:.0f}"
        )

        if abs(
            peak-target
        ) < target*0.05:

            metrics = spectrometer_metrics(
                intensity,
                detector_max
            )

            return (
                integration,
                wl,
                intensity,
                metrics
            )


        scale = (
            target /
            max(peak,1)
        )

        integration *= scale

        integration = max(
           min_time,
           min(max_time,integration)
        )

    
    metrics = spectrometer_metrics(
        intensity,
        detector_max
    )

    return (
        integration,
        wl,
        intensity,
        metrics
    )

