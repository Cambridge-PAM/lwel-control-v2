# LWEL Control v2

Control software for the LWEL experimental setup, supporting:

- Thorlabs TLCamera control
- Ocean Insight spectrometer control
- Automated calibration routines
- HDF5 data acquisition
- Dark and bright reference management
- Reproducible configuration via YAML

---

# Features

## Camera Control

- Connect to a Thorlabs TLCamera
- Configure camera exposure
- Configure Region of Interest (ROI)
- Automatic exposure calibration
- Image preview during calibration

## Spectrometer Control

- Connect to Ocean Insight spectrometers via SeaBreeze
- Automatic integration time optimisation
- Dark reference acquisition
- Bright reference acquisition
- Real-time spectrum visualisation

## Acquisition

- Simultaneous camera and spectrometer acquisition
- Scheduled measurements
- Configurable time intervals
- Data stored in HDF5 format

## Data Management

- Calibration settings stored in `config.yml`
- Bright and dark references saved for reuse
- Experimental data stored in HDF5 files
- Reproducible acquisition settings

---

# Repository Structure

```text
lwel-control-next/

├── config.yml
├── main.py
├── calibrate.py
├── environment.yml
├── README.md

├── data/
│   ├── acquisition.h5
│   ├── dark_reference.npy
│   ├── bright_reference.npy

├── src/
│   ├── camera.py
│   ├── spectrometer.py
│   ├── acquisition.py
│   ├── storage.py
│   └── plotting.py

```

---

# Installation

## Clone Repository

```bash
git clone https://github.com/Cambridge-PAM/lwel-control-v2.git

cd lwel-control-v2
```

## Create Environment

```bash
conda env create -f environment.yml
```

Activate:

```bash
conda activate lwel-control-env
```

---

# Hardware Requirements

## Camera

Supported:

- Thorlabs TLCamera family

Example:

- CS505MU
- CS2100M-USB

Ensure:

- Thorlabs SDK installed
- Thorlabs DLLs available

## Spectrometer

Supported:

- Ocean Insight devices
- Ocean Optics devices

Ensure:

- SeaBreeze backend installed
- Spectrometer connected prior to launching software

---

# Configuration

All settings are stored in:

```text
config.yml
```

Example:

```yaml
camera:
  serial: "16906"

  exposure_time: 0.05

  roi:
    - 100
    - 1440
    - 4
    - 1080
    - 1
    - 1

spectrometer:
  integration_time_us: 7000

acquisition:
  measurements: 5
  interval_seconds: 1

storage:
  h5_file: data/acquisition.h5
```

---

# Calibration Workflow

Calibration should be run before collecting data.

```bash
python calibrate.py
```

The calibration procedure performs:

## Camera Calibration

1. Connect camera
2. Capture images
3. Automatically adjust exposure
4. Display calibrated image
5. Save exposure setting

A calibration image is displayed for visual verification.

---

## Spectrometer Calibration

The user will be prompted to acquire:

### Dark Reference

Close the shutter or cap the fibre.

Press:

```text
ENTER
```

to record the dark spectrum.

Saved as:

```text
data/dark_reference.npy
```

---

### Bright Reference

Illuminate the reference target/sample.

Press:

```text
ENTER
```

to record the bright spectrum.

Saved as:

```text
data/bright_reference.npy
```

---

### Integration Time Optimisation

The software automatically adjusts the integration time until:

```text
Peak signal ≈ 75% detector saturation
```

This helps avoid:

- Detector saturation
- Poor signal-to-noise ratio
- Manual tuning errors

---

## Calibration Outputs

The following plots are shown:

### Camera Calibration

```text
Image
+
Colour Scale
+
Exposure Value
```

### Spectrometer Calibration

```text
Dark Reference
Bright Reference
Optimised Spectrum
```

The plots should be inspected by the operator.

Expected behaviour:

- Dark reference near detector baseline
- Bright reference significantly above dark reference
- Optimised spectrum below saturation

---

# Running an Experiment

Once calibration is complete:

```bash
python main.py
```

The acquisition system will:

1. Load settings from `config.yml`
2. Connect camera
3. Connect spectrometer
4. Collect measurements
5. Store results in HDF5

---

# Output Data Structure

Example:

```text
acquisition.h5

├── dataset_0
│   ├── image
│   └── spectrum

├── dataset_1
│   ├── image
│   └── spectrum

├── dataset_2
│   ├── image
│   └── spectrum
```

Metadata stored:

```text
Camera Exposure
Spectrometer Integration Time
Acquisition Interval
Acquisition Timestamp
```

---

# Development Workflow

Open the repository in VS Code:

```bash
code .
```

Useful extensions:

- Python
- Jupyter
- Pylance
- GitHub Pull Requests

---

# Recommended Daily Workflow

## Start of Experiment

```bash
python calibrate.py
```

Verify:

- Camera image
- Dark reference
- Bright reference
- Optimised spectrum

---

## Data Collection

```bash
python main.py
```

---

## Data Analysis

Open:

```text
data/acquisition.h5
```

using:

- Python
- HDFView
- Jupyter notebooks

---

# Future Enhancements

Planned improvements:

- Live acquisition GUI
- Dark subtraction during acquisition
- Reflectance/transmittance calculations
- Multi-camera support
- Automatic calibration reports
- Calibration history database
- Real-time plotting
- Spectrometer wavelength calibration
- Flat-field correction
- Instrument health monitoring

---

# Troubleshooting

## No Camera Found

Check:

- USB connection
- Camera serial number
- Thorlabs SDK installation

---

## No Spectrometer Found

Check:

```bash
python -c "from seabreeze.spectrometers import list_devices; print(list_devices())"
```

---

## Saturated Spectrum

Re-run:

```bash
python calibrate.py
```

Ensure illumination conditions have not changed.

---

## Dark Reference Too High

Check:

- Shutter fully closed
- Fibre capped
- Ambient light blocked

---

# License

MIT License

Copyright (c) Cambridge-PAM

Permission is hereby granted to use, modify and distribute this software for research and educational purposes.

---
