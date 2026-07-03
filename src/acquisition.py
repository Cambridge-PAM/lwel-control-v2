import time

from src.storage import (
    initialise,
    save
)


def run(
    camera,
    spectrometer,
    output_file,
    n_measurements,
    interval_seconds,
    camera_exposure,
    spectrometer_int
):

    initialise(
        output_file,
        camera_exposure,
        spectrometer_int,
        interval_seconds
    )

    camera.setup_acquisition(
        nframes=n_measurements
    )

    camera.start_acquisition()

    for idx in range(
        n_measurements
    ):

        if idx:

            time.sleep(
                interval_seconds
            )

        camera.wait_for_frame()

        image = (
            camera.read_oldest_image()
        )

        wavelength, intensity = (
            spectrometer.spectrum(
                correct_nonlinearity=True
            )
        )

        save(
            output_file,
            idx,
            image,
            wavelength,
            intensity
        )

        print(
            f"{idx+1}/{n_measurements}"
        )

    camera.stop_acquisition()