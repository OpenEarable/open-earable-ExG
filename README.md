# OpenEarable ExG

OpenEarable ExG is an open-source hardware platform for measuring biopotentials in and around the ears, including electroencephalography (EEG), electrooculography (EOG), and electromyography (EMG). It builds on OpenEarable v1.3 and supports up to seven sensing channels (including one reference) plus ground.

This repository contains the electronics designs, printable mechanical parts, firmware, and Python tools for recording and visualizing biopotential signals.

## Paper

**OpenEarable ExG: Open-Source Hardware for Ear-Based Biopotential Sensing Applications**  
Philipp Lepold, Tobias Röddiger, Tobias King, Kai Kunze, Christoph Maurer, and Michael Beigl. UbiComp Companion 2024.

[Read the paper (ACM PDF)](https://dl.acm.org/doi/epdf/10.1145/3675094.3678480)

The paper describes the hardware and its initial evaluation for eye movements, alpha brain activity, and jaw clenching.

## Repository contents

| Path | Contents |
| --- | --- |
| [OpenEarable ExG EasyEDA/](OpenEarable%20ExG%20EasyEDA/) | EasyEDA JSON files for the main-board schematic and PCB layout. |
| [CAD/](CAD/) | Fusion 360 source models (`.f3d`, `.f3z`) and printable STL files for the housing, earpieces, and earplugs. |
| [Code/OpenEarableExG PlatformIO/](Code/OpenEarableExG%20PlatformIO/) | PlatformIO firmware project, including the local OpenEarable Arduino Mbed framework. |
| [Code/record_and_realtime_plot_BLE.py](Code/record_and_realtime_plot_BLE.py) | Receive biopotential samples over Bluetooth Low Energy, plot them live, and optionally save CSV recordings. |
| [Code/record_and_realtime_plot_Serial.py](Code/record_and_realtime_plot_Serial.py) | Receive biopotential samples over serial, plot them live, and optionally save CSV recordings. |
| [Code/plot_recorded_data.py](Code/plot_recorded_data.py) | Plot previously recorded CSV data. |
| [Code/digitalfilter.py](Code/digitalfilter.py) | Streaming digital filters used by the recording scripts. |


## Firmware and flashing

For PlatformIO setup and general instructions on compiling and flashing OpenEarable firmware, see [here](https://github.com/OpenEarable/open-earable) and [here](https://github.com/OpenEarable/open-earable-PlatformIO#readme).

To use the ExG firmware supplied here:

1. Install Visual Studio Code with the PlatformIO extension as described in the linked repository.
2. Open `Code/OpenEarableExG PlatformIO/` as the PlatformIO project; this directory contains `platformio.ini`.
3. Build and upload using PlatformIO and the upstream flashing instructions.

Use this repository's project for ExG acquisition. Its [main.cpp](Code/OpenEarableExG%20PlatformIO/src/main.cpp) configures the AD7124 ADC and streams samples over serial and BLE. The supplied configuration enables one differential ADC channel with a nominal sampling rate of 256 samples per second; the hardware's available channels are not all enabled by default.

## Recording and plotting

The Python scripts contain example settings that must be adapted to your device and acquisition configuration.

From the repository root, install the Python dependencies and enter the script directory:

```sh
python3 -m pip install bleak pyserial matplotlib numpy scipy pandas
cd Code
```

Before running a live plot:

- Set `BLE_ADDRESS` in `record_and_realtime_plot_BLE.py`, or the serial port in `record_and_realtime_plot_Serial.py`.
- Match the sampling rate, amplifier gain (`inamp_gain`), and filter settings to your firmware and hardware setup.
- To save CSV files, create a `recordings/` directory inside `Code/` and set `write_to_file = True` in the selected script. Recording is disabled by default.

Run the script for your connection:

```sh
python3 record_and_realtime_plot_BLE.py
# Or, for serial:
python3 record_and_realtime_plot_Serial.py
```

To view a saved recording, set `folder`, `filename`, and the plotting parameters at the bottom of `plot_recorded_data.py`, then run:

```sh
python3 plot_recorded_data.py
```
