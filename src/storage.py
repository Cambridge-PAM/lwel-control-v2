import h5py

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


def save(
    filename,
    idx,
    image,
    wavelengths,
    intensities
):

    with h5py.File(
        filename,
        "a"
    ) as f:

        group = f.create_group(
            f"dataset_{idx}"
        )

        group.create_dataset(
            "image",
            data=image
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