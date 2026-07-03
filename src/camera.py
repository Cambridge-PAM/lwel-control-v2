from pylablib.devices import Thorlabs
import numpy as np

def connect_camera(serial):

    camera = Thorlabs.ThorlabsTLCamera(
        serial=serial
    )

    camera.open()

    return camera


def configure_camera(
    camera,
    exposure,
    roi
):

    camera.set_exposure(exposure)

    camera.set_roi(*roi)


def acquire_image(camera):

    return camera.grab(1)[0]


def mean_brightness(image):

    return np.mean(image)


def auto_exposure(
        cam,
        target_mean=120,
        tolerance=10,
        max_iterations=15
):

    exposure = 0.01

    for _ in range(max_iterations):

        cam.set_exposure(exposure)

        image = acquire_image(cam)

        brightness = mean_brightness(image)

        print(
            f"Exp={exposure:.4f}s "
            f"Brightness={brightness:.1f}"
        )

        error = (
            brightness-target_mean
        )

        if abs(error) < tolerance:

            return exposure, image

        scale = (
            target_mean /
            max(brightness,1)
        )

        exposure *= scale

        exposure = max(
            0.001,
            min(exposure,5)
        )

    return exposure, image
