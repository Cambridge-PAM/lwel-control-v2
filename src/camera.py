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
    
    if hasattr(camera, "set_roi"):
            camera.set_roi(*roi)

def acquire_image(camera):

    return camera.grab(1)[0]


def mean_brightness(image):

    return np.mean(image)



def camera_metrics(
    image, detector_max=255
):
    """
    Calculate image quality metrics.
    """

    max_pixel = float(np.max(image))
    mean_pixel = float(np.mean(image))

    metrics = {
        "mean": mean_pixel,
        "max": max_pixel,
        "min": float(np.min(image)),
        "std": float(np.std(image)),
        "total_pixels": image.size,
    }

    metrics["peak_fraction"] = (
        max_pixel / detector_max
    )

    metrics["mean_fraction"] = (
        mean_pixel / detector_max
    )

    metrics["saturated_pixels"] = int(
        np.sum(image >= detector_max)
    )

    metrics["saturation_fraction"] = (
        metrics["saturated_pixels"]
        / metrics["total_pixels"]
    )

    metrics["scale_factor"] = (
        detector_max / max(max_pixel, 1)
    )

    return metrics


def auto_exposure(
    cam,
    target_peak_fraction=0.8,
    detector_max=255,
    tolerance=0.03,
    max_iterations=15
):
    
    exposure = 0.01

    for _ in range(max_iterations):

        cam.set_exposure(exposure)

        image = acquire_image(cam)

        metrics = camera_metrics(
            image, detector_max
        )

        peak_fraction = (
            metrics["peak_fraction"]
        )

        mean_fraction = (
            metrics["mean_fraction"]
        )

        print(
            f"Exp={exposure:.6f}s "
            f"Peak={100*peak_fraction:.1f}% "
            f"Mean={100*mean_fraction:.1f}%"
        )

        error = (
            peak_fraction -
            target_peak_fraction
        )

        if abs(error) < tolerance:

            return (
                exposure,
                image,
                metrics
            )

        scale = (
            target_peak_fraction /
            max(peak_fraction, 1e-6)
        )

        exposure *= scale

        exposure = max(
            0.0001,
            min(exposure, 6.0)
        )

    return (
        exposure,
        image,
        metrics
    )

