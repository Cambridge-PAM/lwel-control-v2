import yaml

from src.camera import (
    connect_camera as camera_connect,
    configure_camera as camera_configure
)

from src.spectrometer import (
    connect_spectrometer as spectrometer_connect,
    set_integration
)

from src.acquisition import run

from src.device_factory import (
    build_camera,
    build_spectrometer
)

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import numpy as np
from time import time
from pathlib import Path

def load_config():
    with open("config.yml") as f:
        return yaml.safe_load(f)

def main():
    
    cfg = load_config()
    
    camera = build_camera(cfg)

    camera_configure(
        camera,
        cfg["camera"]["exposure_time"],
        tuple(cfg["camera"]["roi"])
    )

    spectrometer = build_spectrometer(cfg)
    
    set_integration(
    spectrometer,
        cfg["spectrometer"]["integration_time_us"]
    )
    wavelengths = spectrometer.wavelengths

    sample_id = cfg["experiment"]["sample_id"]

    dark_reference = np.load(
        Path("data") / sample_id / "dark_reference.npy"
    )[1]

    bright_reference = np.load(
        Path("data") / sample_id / "bright_reference.npy"
    )[1]
    
    run(
        cfg=cfg,
        camera=camera,
        spectrometer=spectrometer,
        n_measurements=cfg["acquisition"]["measurements"],
        interval_seconds=cfg["acquisition"]["interval_seconds"],
        camera_exposure=cfg["camera"]["exposure_time"],
        spectrometer_int=cfg["spectrometer"]["integration_time_us"]
    )
    
    plt.show()
    camera.close()
    
if __name__ == "__main__":
    main()