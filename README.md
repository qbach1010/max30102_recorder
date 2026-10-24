# MAX30102 PPG Recorder

This repository contains a complete MAX30102 pulse oximeter / photoplethysmography (PPG) data acquisition setup split into two parts:

- an STM32 firmware project in `max_ppg/` that reads IR and RED values from the MAX30102 sensor and streams them over USB serial
- a Python GUI application in `ppg_plot.py` that uses PyQt5 and Matplotlib to receive the streamed data, plot live signals, and save recordings to CSV

The project is designed for rapid prototyping and lab work with a MAX30102 sensor connected to an STM32 development board.

Thís project use a public HAL driver for MAX30102: https://github.com/eepj/stm32-max30102

## Project overview

### 1) STM32 firmware (`max_ppg/`)
The firmware is a CubeMX / STM32 project for a microcontroller such as STM32F401RCT6. It configures:

- I2C communication with the MAX30102
- USB CDC communication for serial data transfer
- sensor initialization and sampling
- real-time transmission of `IR,RED` samples to host PC

The embedded firmware uses the `stm32-max30102-master` driver included under `max_ppg/Drivers/stm32-max30102-master` and calls `max30102_read_fifo()` in the main loop. Each data packet is sent to the PC over USB as text like:

```text
12345,6789
23456,6901
```

### 2) Python GUI (`ppg_plot.py`)
The Python app:

- opens a serial port (for example `/dev/ttyACM0` or `COM3`)
- receives `IR,RED` values from the STM32 board
- updates a live plot with both channels
- stores data into a CSV file
- supports recording duration options (continuous, 1, 2, or 5 minutes)

It is built with:

- PyQt5 for the interface
- Matplotlib for plotting
- pyserial for serial communication

## Repository structure

```text
max30102_recorder/
├── LICENSE
├── README.md
├── gitignore
├── ppg_plot.py
├── max_ppg/
│   ├── .cproject
│   ├── .mxproject
│   ├── .project
│   ├── .settings/
│   ├── Core/
│   ├── Debug/
│   ├── Drivers/
│   │   └── stm32-max30102-master/
│   ├── Middlewares/
│   ├── USB_DEVICE/
│   ├── STM32F401RCTX_FLASH.ld
│   ├── max_ppg.ioc
│   └── max_ppg Debug.launch
└── ppg_plot.py
```

## Hardware requirements

- STM32 development board (tested with STM32F401RCT6 / compatible F401 family board)
- MAX30102 pulse oximeter / heart-rate sensor module
- I2C wires and power wiring
- USB cable for the STM32 board
- optional: breadboard and pull-up resistors depending on your board layout

Typical connection concept:

- MAX30102 SDA -> STM32 I2C SDA
- MAX30102 SCL -> STM32 I2C SCL
- MAX30102 VIN -> 3.3V
- MAX30102 GND -> GND
- MAX30102 INT -> optional GPIO interrupt pin (if using interrupt-driven approach)

I can't use the INT pin since my module is pretty cheap, interrupt pin often don't work on cheaper module, current project I set a timer for sampling (hardcoded 20ms)

## Software dependencies

### Python dependencies
Install the following packages:

```bash
pip install PyQt5 matplotlib pyserial
```

Required Python packages used by this project:

- `PyQt5` - GUI framework for live control and plotting interface
- `matplotlib` - drawing the PPG waveform
- `pyserial` - serial communication with the STM32 board
- `csv` - built-in Python library for CSV logging
- `datetime`, `time` - built-in Python stdlib modules

### STM32 firmware dependencies
The embedded project depends on:

- STM32CubeIDE or STM32CubeMX
- STM32 HAL drivers
- STM32 USB Device CDC middleware
- I2C peripheral configuration
- `max30102_for_stm32_hal.h` driver from `Drivers/stm32-max30102-master`

The embedded driver folder is already included in the repo:

```text
max_ppg/Drivers/stm32-max30102-master/
```

It contains the MAX30102 HAL driver implementation and driver documentation.

## Build and run instructions

### 1) Build the STM32 firmware

1. Open `max_ppg/max_ppg.ioc` using STM32CubeMX or open the project folder in STM32CubeIDE.
2. Make sure the project is configured for:
   - I2C1 enabled
   - USB CDC enabled
   - correct MCU and clock settings
   - GPIO for the MAX30102 interrupt (if used)
3. Build the firmware.
4. Flash the program to the STM32 board using ST-LINK or STM32CubeProgrammer.

### 2) Run the Python GUI

From the repository root:

```bash
python ppg_plot.py
```

Then:

1. Select the serial port connected to the STM32 board.
2. Click Connect.
3. Choose a save file and recording duration.
4. Click START RECORDING to begin capturing data.
5. The waveform is displayed in real time and saved into CSV.

## Data format

The STM32 sends two channels as comma-separated values:

```text
IR,RED
```

Example:

```text
14233,15880
14251,15910
14266,15924
```

The Python code writes each sample to CSV in columns:

```text
Timestamp,IR,Red
```

## How it works

1. The MAX30102 sensor measures infrared and red reflected light.
2. The STM32 reads FIFO data from the sensor over I2C.
3. The firmware converts each sample into a CSV-like stream and sends it via USB serial.
4. The Python GUI reads the stream and draws the waveform live.
5. User can save the sensor data for later analysis.

## Quick start summary

```bash
# Python side
pip install PyQt5 matplotlib pyserial
python ppg_plot.py
```

Then flash the STM32 code from `max_ppg/` and connect the device.

## Notes

- This project is intended for development and experimental use.
- It is not a medical device or clinical-grade acquisition system.
- The code and driver configuration are suitable as a starting point for custom biomedical signal instrumentation.

## License

This repository includes an open-source license file (`LICENSE`).

## Useful references

- MAX30102 datasheet
- STM32 HAL documentation
- STM32 CubeIDE / CubeMX setup
- PyQt5 documentation
- Matplotlib documentation
- pySerial documentation
