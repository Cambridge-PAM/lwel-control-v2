import yaml
import numpy as np
import matplotlib.pyplot as plt

from camera import (
    connect_camera,
    configure_camera,
    auto_exposure,
    camera_metrics,
    camera_status
)

from spectrometer import (
    connect_spectrometer,
    acquire_spectrum,
    auto_integration_time,
    spectrometer_metrics,
    spectrometer_status
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


def camera_status(metrics):

    sat = (
        metrics[
            "saturation_fraction"
        ]
    )

    if sat > 0.05:

        return (
            "FAIL",
            "Camera heavily saturated."
        )

    if sat > 0.01:

        return (
            "WARNING",
            "Camera approaching saturation."
        )

    if metrics["mean"] < 20:

        return (
            "WARNING",
            "Image underexposed."
        )

    return (
        "PASS",
        "Camera calibration acceptable."
    )

def spectrometer_status(
        peak,
        detector_max=65535
):

    fraction = peak / detector_max

    if fraction > 0.98:

        return (
            "FAIL",
            "Detector saturated."
        )

    if fraction > 0.90:

        return (
            "WARNING",
            "Detector close to saturation."
        )

    if fraction < 0.20:

        return (
            "WARNING",
            "Detector utilization low."
        )

    return (
        "PASS",
        "Detector operating normally."
    )


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

    
    (
        exposure,
        image,
        cam_metrics
    ) = auto_exposure(cam)
    
    
    (
        cam_state,
        cam_message
    ) = camera_status(
        cam_metrics
    )

    cfg["camera"][
        "exposure_time"
    ] = float(exposure)

    fig, ax = plt.subplots(
        figsize=(8,6)
    )

    im = ax.imshow(image)

    colour = {
        "PASS":"green",
        "WARNING":"orange",
        "FAIL":"red"
    }[cam_state]

    ax.set_title(
        f"Camera Calibration "
        f"({cam_state})",
        color=colour
    )

    plt.colorbar(im)

    plt.tight_layout()
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

    (
    integration,
    wl,
    intensity,
    spec_metrics
    ) = auto_integration_time(
        spec,
        cfg["calibration"][
            "target_detector_fraction"
        ],
        cfg["calibration"][
            "detector_max_counts"
        ]
    )
    
    (
    spec_state,
    spec_message
    ) = spectrometer_status(
        spec_metrics["peak_counts"]
    )

    cfg["spectrometer"][
        "integration_time_us"
    ] = int(integration)
    
    #################################################
    # PLOTS
    #################################################

    fig, ax = plt.subplots(
        figsize=(10,6)
    )

    ax.plot(
        dark_wl,
        dark_int,
        label="Dark Reference"
    )

    ax.plot(
        bright_wl,
        bright_int,
        label="Bright Reference"
    )

    ax.plot(
        wl,
        intensity,
        linewidth=2,
        label="Optimised Spectrum"
    )

    colour = {
        "PASS":"green",
        "WARNING":"orange",
        "FAIL":"red"
    }[spec_state]

    ax.set_title(
        f"Spectrometer Calibration "
        f"({spec_state})",
        color=colour
    )

    ax.set_xlabel("Wavelength / nm")
    ax.set_ylabel("Counts")
    ax.legend()

    ax.grid(True)

    plt.tight_layout()
    plt.show()
    
     #################################################
    # Calibration
    #################################################
    print()

    print("="*60)
    print("CALIBRATION SUMMARY")
    print("="*60)

    print("\nCAMERA")

    print(
        f"Exposure Time: "
        f"{exposure:.4f} s"
    )

    print(
        f"Mean Brightness: "
        f"{cam_metrics['mean']:.1f}"
    )

    print(
        f"Maximum Pixel: "
        f"{cam_metrics['max']:.1f}"
    )

    print(
        f"Saturated Pixels: "
        f"{cam_metrics['saturated_pixels']}"
    )

    print(
        f"Saturation Fraction: "
        f"{100*cam_metrics['saturation_fraction']:.2f}%"
    )

    print(
        f"Status: {cam_state}"
    )

    print(cam_message)

    print("\n" + "-"*60)

    print("\nSPECTROMETER")

    print(
        f"Integration Time: "
        f"{integration:.0f} us"
    )

    print(
        f"Peak Counts: "
        f"{spec_metrics['peak_counts']:.0f}"
    )

    print(
        f"Detector Usage: "
        f"{spec_metrics['detector_usage']:.1f}%"
    )

    print(
        f"Dark Max: "
        f"{np.max(dark_int):.0f}"
    )

    print(
        f"Bright Max: "
        f"{np.max(bright_int):.0f}"
    )

    print(
        f"Status: "
        f"{spec_state}"
    )

    print(spec_message)

    print("\n" + "="*60)

    #########################################
    # SAVE UPDATED CONFIG
    #########################################
    cfg["calibration_results"] = {
        "camera":

        {
            "status": cam_state,
            "mean_brightness":
                cam_metrics["mean"],
            "max_pixel":
                cam_metrics["max"],
            "saturation_fraction":
                cam_metrics["saturation_fraction"]
        },

        "spectrometer":

        {
            "status": spec_state,
            "peak_counts":
                spec_metrics["peak_counts"],
            "detector_usage":
                spec_metrics["detector_usage"]
        }
    }
    
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