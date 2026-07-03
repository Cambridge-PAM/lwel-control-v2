import yaml

from src.camera import (
    connect as camera_connect,
    configure as camera_configure
)

from src.spectrometer import (
    connect as spectrometer_connect,
    set_integration
)

from src.acquisition import run

def load_config():
    with open("config.yml") as f:
        return yaml.safe_load(f)

camera = camera_connect(
    CAMERA_SERIAL
)

def main():
    
    cfg = load_config()
    
    camera = camera_connect(
        cfg["camera"]["serial"]
    )

    camera_configure(
        camera,
        cfg["camera"]["exposure_time"],
        tuple(cfg["camera"]["roi"])
    )

    spectrometer = spectrometer_connect()
    
    set_integration(
    spectrometer,
        cfg["spectrometer"]["integration_time_us"]
    )

    run(
        camera=camera,
        spectrometer=spectrometer,
        output_file=cfg["storage"]["h5_file"],
        n_measurements=cfg["acquisition"]["measurements"],
        interval_seconds=cfg["acquisition"]["interval_seconds"]
    )

    camera.close()
    
if __name__ == "__main__":
    main()