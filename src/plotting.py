import matplotlib.pyplot as plt


def plot_spectrum(
    wavelength,
    intensity
):

    plt.figure()

    plt.plot(
        wavelength,
        intensity
    )

    plt.xlabel(
        "Wavelength (nm)"
    )

    plt.ylabel(
        "Counts"
    )

    plt.tight_layout()

    plt.show()