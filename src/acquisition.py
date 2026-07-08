import time
from time import perf_counter, sleep


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
    
    estimated_duration = (
        (n_measurements - 1)
        * interval_seconds
    )

    print("\n" + "=" * 60)
    print("SYSTEM READY")
    print("=" * 60)
    print(f"Measurements      : {n_measurements}")
    print(f"Interval          : {interval_seconds:.2f} s")
    print(f"Expected duration : {estimated_duration:.1f} s")
    print(f"Output file       : {output_file}")
    print("=" * 60)
    print("Press ENTER to start acquisition...")


    input()

    camera.setup_acquisition(nframes=n_measurements)
    camera.start_acquisition()
    
    print("\n")
    print("Acquisition running . . . \n")
    
    start_time = perf_counter()  # Record the start time

    for idx in range(n_measurements):
        
        scheduled_time = (start_time + idx * interval_seconds)
        remaining = scheduled_time - perf_counter()
        if remaining > 0:
            sleep(remaining)
        
        actual_time = perf_counter()

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
        
        elapsed_time = actual_time - start_time
        print(f"{idx+1}/{n_measurements}: Elapsed time: {elapsed_time:.2f} seconds")

        
        if update_callback is not None:
            update_callback(
                image,
                intensity,
                idx=idx,
                n_measurements=n_measurements,
                elapsed=elapsed_time
            )
            
    camera.stop_acquisition()
    
    total_time = perf_counter() - start_time

    print("\n" + "=" * 60)
    print("ACQUISITION COMPLETE")
    print("=" * 60)
    print(f"Measurements acquired : {n_measurements}")
    print(f"Total duration        : {total_time:.2f} s")
    print(f"Average interval      : "
        f"{total_time / max(1, n_measurements-1):.3f} s")
    print(f"Data saved to         : {output_file}")
    print("=" * 60)



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