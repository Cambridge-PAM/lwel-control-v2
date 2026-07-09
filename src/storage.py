import h5py
import numpy as np

from datetime import datetime


def initialise(
    filename,
    cam_int,
    spec_int,
    interval
):

    with h5py.File(
        filename,
        "w"
    ) as f:

        f.attrs["camera_int"] = cam_int
        f.attrs["spec_int"] = spec_int
        f.attrs["interval"] = interval

        f.attrs["created"] = (
            datetime.now().isoformat()
        )


def _to_greyscale_uint8(image):
    """Convert an RGB image to greyscale uint8 using luminance weights."""
    # Expect image shape (H, W, 3)
    if image.ndim != 3 or image.shape[-1] != 3:
        return image

    # Use standard luminance conversion and clip
    grey = (0.2989 * image[..., 0]
            + 0.5870 * image[..., 1]
            + 0.1140 * image[..., 2])

    grey = np.rint(grey).astype(np.uint8)

    return grey


def save(
    filename,
    idx,
    image,
    wavelengths,
    intensities,
    cfg=None
):
    """Save a dataset to an HDF5 file.

    If `cfg` contains a `storage` section, it may include:
      - image_mode: 'full' | 'greyscale' | 'greyscale_when_color'
      - compression: { method: 'gzip'|None, level: int }
    """

    storage_cfg = (cfg or {}).get("storage", {})
    image_mode = storage_cfg.get("image_mode", "full")
    compression_cfg = storage_cfg.get("compression", {})
    compression_method = compression_cfg.get("method", "gzip")
    compression_level = compression_cfg.get("level", 4)

    # Convert image if requested
    out_image = image

    if image_mode == "greyscale":
        out_image = _to_greyscale_uint8(image)

    if image_mode == "greyscale_when_color":
        if image.ndim == 3 and image.shape[-1] == 3:
            out_image = _to_greyscale_uint8(image)

    # Ensure numpy array
    out_image = np.asarray(out_image)

    # Downcast to a compact dtype if possible (uint8)
    if out_image.dtype != np.uint8:
        try:
            # Scale/clip to 0-255 if values are larger
            maxv = out_image.max()
            minv = out_image.min()
            if maxv > 255 or minv < 0:
                # Normalize to 0-255
                out_image = (255 * (out_image - minv) / max(1, (maxv - minv)))
            out_image = np.rint(out_image).astype(np.uint8)
        except Exception:
            out_image = out_image.astype(np.uint8, copy=False)

    with h5py.File(
        filename,
        "a"
    ) as f:

        group = f.create_group(
            f"dataset_{idx}"
        )

        # Create image dataset with optional compression
        ds_kwargs = {}
        if compression_method:
            ds_kwargs["compression"] = compression_method
            ds_kwargs["compression_opts"] = compression_level

        group.create_dataset(
            "image",
            data=out_image,
            **ds_kwargs
        )

        group.create_dataset(
            "spectrum",
            data=[
                wavelengths,
                intensities
            ]
        )

        group.attrs["timestamp"] = (
            datetime.now().isoformat()
        )