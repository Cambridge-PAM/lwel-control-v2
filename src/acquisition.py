import time

from src.storage import (
    initialise,
    save
)

from pathlib import Path
from datetime import datetime


def create_experiment_folder(cfg):
    sample_id = cfg["experiment"]["sample_id"]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Add a unique identifier for each run
    run_id = f"run_{timestamp}"
    
    folder = (
        Path(cfg["experiment"]["output_root"])
        / sample_id
        / run_id
    )

    folder.mkdir(parents=True, exist_ok=True)

    return folder


def run(
    cfg,
    camera,
    spectrometer,
    output_file,
    n_measurements,
    interval_seconds,
    camera_exposure,
    spectrometer_int,
    update_callback=None
):
    # Create a unique folder for this run
    experiment_folder = create_experiment_folder(cfg)
    
    # Update the output file path to include the unique folder
    output_file = experiment_folder / "acquisition.h5"
    
    initialise(
        output_file,
        camera_exposure,
        spectrometer_int,
        interval_seconds
    )
    
    print("\nSystem ready.")
    print("Press ENTER to start acquisition.")

    input()

    camera.setup_acquisition(nframes=n_measurements)
    camera.start_acquisition()
    
    start_time = time.time()  # Record the start time

    for idx in range(n_measurements):
        if idx:
            time.sleep(interval_seconds)

        camera.wait_for_frame()

        image = camera.read_oldest_image()

        wavelength, intensity = spectrometer.spectrum(correct_nonlinearity=True)

        save(
            output_file,
            idx,
            image,
            wavelength,
            intensity
        )
        
        elapsed_time = time.time() - start_time
        print(f"{idx+1}/{n_measurements}: Elapsed time: {elapsed_time:.2f} seconds")

        
        if update_callback is not None:
            update_callback(
                image,
                intensity
            )
            
    camera.stop_acquisition()


def create_experiment_folder(cfg):

    sample_id = cfg[
        "experiment"
    ][
        "sample_id"
    ]

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    folder = (
        Path(
            cfg["experiment"][
                "output_root"
            ]
        )
        / sample_id
        / timestamp
    )

    folder.mkdir(
        parents=True,
        exist_ok=True
    )

    return folder