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

def create_live_display(
    image_shape,
    wavelengths,
    dark_ref,
    bright_ref
):

    fig, (ax_img, ax_spec) = plt.subplots(
        2,
        1,
        figsize=(10, 8)
    )

    image_artist = ax_img.imshow(
        np.zeros(image_shape),
        cmap="gray"
    )
    ax_img.set_title("Camera Image")

    spectrum_artist, = ax_spec.plot(
        wavelengths,
        np.zeros_like(wavelengths),
        label="Spectrum"
    )

    dark_artist, = ax_spec.plot(
        wavelengths,
        dark_ref,
        "--",
        label="Dark"
    )

    bright_artist, = ax_spec.plot(
        wavelengths,
        bright_ref,
        "--",
        label="Bright"
    )

    ax_spec.legend()
    ax_spec.set_title("Spectrum")

    timer_text = fig.text(
        0.02,
        0.01,
        "Elapsed: 00:00:00",
        fontsize=12
    )
    
    start_time = time()
    plt.show(block=False)

    return {
        "fig": fig,
        "image": image_artist,
        "spectrum": spectrum_artist,
        "timer": timer_text,
        "start_time": start_time,
        "ax_spec": ax_spec
    }

def update_live_display(display, image, spectrum):
    
    # Update the camera image
    display["image"].set_data(image)

    # Update the spectrum data
    display["spectrum"].set_ydata(spectrum)

    # Rescale the spectrum axes
    display["ax_spec"].relim()
    display["ax_spec"].autoscale_view()

    # Update the elapsed time
    elapsed = int(time() - display["start_time"])
    h = elapsed // 3600
    m = (elapsed % 3600) // 60
    s = elapsed % 60
    display["timer"].set_text(f"Elapsed: {h:02d}:{m:02d}:{s:02d}")

    # Redraw the canvas
    display["fig"].canvas.draw_idle()
    plt.show(block=False)


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

    display = create_live_display(
        image_shape=(1024, 1280),   # camera resolution
        wavelengths=wavelengths,
        dark_ref=dark_reference,
        bright_ref=bright_reference
    )
    
    run(
        cfg=cfg,
        camera=camera,
        spectrometer=spectrometer,
        output_file=cfg["storage"]["h5_file"],
        n_measurements=cfg["acquisition"]["measurements"],
        interval_seconds=cfg["acquisition"]["interval_seconds"],
        camera_exposure=cfg["camera"]["exposure_time"],
        spectrometer_int=cfg["spectrometer"]["integration_time_us"],  
        update_callback=lambda img, spec: update_live_display(
                display,
                img,
                spec
            )
    )
    
    plt.show()
    camera.close()
    
if __name__ == "__main__":
    main()