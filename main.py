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