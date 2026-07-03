import yaml
import numpy as np
import matplotlib.pyplot as plt

from camera import (
    connect_camera,
    configure_camera,
    auto_exposure
)

from spectrometer import (
    connect_spectrometer,
    auto_integration_time,
    acquire_spectrum
)


def load_config():

    with open("config.yml") as f:
        return yaml.safe_load(f)


def save_config(cfg):

    with open("config.yml","w") as f:

        yaml.dump(
            cfg,
            f,
            sort_keys=False
        )


def acquire_dark_reference(spec):

    print(
        "\nPlace dark cap / close shutter."
    )

    input(
        "Press ENTER to acquire dark spectrum:"
    )

    return acquire_spectrum(spec)


def acquire_bright_reference(spec):

    print(
        "\nIlluminate sample."
    )

    input(
        "Press ENTER to acquire bright reference:"
    )

    return acquire_spectrum(spec)


def main():

    cfg = load_config()

    #################################################
    # CAMERA CALIBRATION
    #################################################

    cam = connect_camera(
        cfg["camera"]["serial"]
    )

    configure_camera(
        cam,
        cfg["camera"]["exposure_time"],
        tuple(cfg["camera"]["roi"])
    )

    exposure,image = auto_exposure(cam)

    cfg["camera"][
        "exposure_time"
    ] = float(exposure)

    plt.figure(figsize=(8,6))

    plt.imshow(image)

    plt.title(
        f"Camera Calibration "
        f"({exposure:.3f}s)"
    )

    plt.colorbar()

    plt.show()

    #################################################
    # SPECTROMETER CALIBRATION
    #################################################

    spec = connect_spectrometer()

    dark_wl,dark_int = (
        acquire_dark_reference(spec)
    )

    bright_wl,bright_int = (
        acquire_bright_reference(spec)
    )

    np.save(
        cfg["references"][
            "dark_reference"
        ],
        np.vstack(
            (dark_wl,dark_int)
        )
    )

    np.save(
        cfg["references"][
            "bright_reference"
        ],
        np.vstack(
            (bright_wl,bright_int)
        )
    )

    integration,wl,intensity = (
        auto_integration_time(
            spec,
            cfg["calibration"][
                "target_detector_fraction"
            ],
            cfg["calibration"][
                "detector_max_counts"
            ]
        )
    )

    cfg["spectrometer"][
        "integration_time_us"
    ] = int(integration)

    #################################################
    # PLOTS
    #################################################

    plt.figure(figsize=(10,6))

    plt.plot(
        dark_wl,
        dark_int,
        label="Dark Reference"
    )

    plt.plot(
        bright_wl,
        bright_int,
        label="Bright Reference"
    )

    plt.plot(
        wl,
        intensity,
        label="Calibration Spectrum"
    )

    plt.xlabel(
        "Wavelength / nm"
    )

    plt.ylabel(
        "Counts"
    )

    plt.title(
        "Spectrometer Calibration"
    )

    plt.legend()

    plt.grid(True)

    plt.tight_layout()

    plt.show()

    #########################################
    # SAVE UPDATED CONFIG
    #########################################

    save_config(cfg)

    print("\nCalibration complete")
    print(
        f"Camera exposure = "
        f"{exposure:.4f} s"
    )

    print(
        f"Spectrometer integration = "
        f"{integration:.0f} us"
    )

    cam.close()


if __name__ == "__main__":
    main()