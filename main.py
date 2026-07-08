import yaml
import numpy as np
from time import time
from pathlib import Path

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

from src.live_monitor import LiveMonitor


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
    
    monitor = LiveMonitor(
    image_shape=(1024, 1280),
    wavelengths=wavelengths
    )

    monitor.start()
    
    print("\n" + "=" * 60)
    print("EXPERIMENT CONFIGURATION")
    print("=" * 60)
    print(f"Sample ID              : {sample_id}")
    print(f"Measurement Duration   : {cfg['acquisition']['measurement_duration']}")
    print(f"Interval               : {cfg['acquisition']['interval_seconds']} s")
    print(f"Camera exposure        : {cfg['camera']['exposure_time']} us")
    print(f"Spectrometer integration: "
        f"{cfg['spectrometer']['integration_time_us']} us")
    print(f"Camera ROI             : {cfg['camera']['roi']}")
    print(f"Wavelength points      : {len(wavelengths)}")
    print("=" * 60)
    
    n_measurements = int(( cfg["acquisition"]["measurement_duration"] / cfg['acquisition']['interval_seconds'] ) + 1)
    
    run(
        cfg=cfg,
        camera=camera,
        spectrometer=spectrometer,
        n_measurements=n_measurements,
        interval_seconds=cfg["acquisition"]["interval_seconds"],
        camera_exposure=cfg["camera"]["exposure_time"],
        spectrometer_int=cfg["spectrometer"]["integration_time_us"],
        update_callback=monitor.update
    )
    
    camera.close()
    
if __name__ == "__main__":
    main()