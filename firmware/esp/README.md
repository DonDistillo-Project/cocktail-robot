# ESP32 Firmware

This directory contains the firmware for the ESP32 microcontroller used in the cocktail robot.

## Features

- Records user input via the microphone.
- Plays back audio output via the speaker.
- Controls the display.
- Reads data from scale.
- Communicates with the `connector` service via WiFi.

## Requirements

- [PlatformIO](https://platformio.org/install/)
- An ESP32 board (the project is configured for the `pico32`)

## Flashing the Firmware

1.  Connect the ESP32 to your computer.
2.  Navigate to this directory:

    ```bash
    cd firmware/esp
    ```

3.  Build and upload the firmware:

    ```bash
    pio run -t upload
    ```

## Monitoring

To view the serial output from the ESP32, run:

```bash
pio device monitor
```
