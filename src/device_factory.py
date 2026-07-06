import yaml


def build_camera(cfg):

    mode = cfg["development"]["mode"]

    if mode == "simulation":

        from src.virtual_camera import (
            VirtualCamera
        )

        print(
            "Using Virtual Camera"
        )

        return VirtualCamera()

    from src.camera import (
        connect_camera
    )

    return connect_camera(
        cfg["camera"]["serial"]
    )


def build_spectrometer(cfg):

    mode = cfg["development"]["mode"]

    if mode == "simulation":

        from src.virtual_spectrometer import (
            VirtualSpectrometer
        )

        print(
            "Using Virtual Spectrometer"
        )

        return VirtualSpectrometer()

    from src.spectrometer import (
        connect_spectrometer
    )

    return connect_spectrometer()