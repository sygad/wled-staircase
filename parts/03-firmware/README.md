[← Part 2 · Wiring and power](../02-wiring/README.md) · [All parts](../../README.md#the-parts) · [Part 4 · The six behaviour patches →](../04-behaviour-patches/README.md)

# Part 3 · Firmware

A custom WLED 16.0.1 build. Stock WLED cannot do this project: its binaries don't
include the staircase usermod at all, and its segment limit is lower than the
number of steps.

## At a glance

| | |
|---|---|
| **Built from** | [WLED](https://github.com/wled/WLED) 16.0.1, EUPL-1.2, plus the patches in [Part 4](../04-behaviour-patches/README.md) |
| **Files in this folder** | `WLED_16.0.1_ESP32-S3_Staircase_FACTORY.bin` (USB flashing) · `WLED_16.0.1_ESP32-S3_Staircase_OTA.bin` (updating) · `platformio_override.ini` (the build env) |
| **Also needs** | the patches in [Part 4](../04-behaviour-patches/patches/), to rebuild it |
| **Compiled in** | 64 segments, the staircase usermod, the audioreactive usermod, release name `ESP32-S3_Staircase` |
| **Not compiled in** | LED count, pins, timings, colours, effects — all of those are settings ([Part 5](../05-wled-settings/README.md)) and presets ([Part 6](../06-presets/README.md)) |

## Pre-built binaries

Built for a **diymore ESP32-S3 DevKitC-1 N16R8** (16 MB flash, 8 MB octal PSRAM).
Any ESP32-S3 with 16 MB flash and PSRAM should take them.

| File | Use it for | SHA-256 |
|---|---|---|
| `WLED_16.0.1_ESP32-S3_Staircase_FACTORY.bin` | **USB flashing** to address `0x0`. Bootloader, partition table, OTA data and app in one image | `1eb09719b5bb8170b7373fd8f63da450af50932f83b571c83481bc6f69a28d2a` |
| `WLED_16.0.1_ESP32-S3_Staircase_OTA.bin` | **Updating** a board already running WLED, through Manual OTA in the web UI | `594f1131aac62986220492c9116042ff57f791f03f1764b149a7b7eaf7e45b57` |

> ⚠️ Never use WLED's built-in online update on this controller. Stock firmware
> has no staircase usermod and a lower segment limit, so the whole project stops
> working. Update with the OTA file above instead.

## What the build changes

| Flag | Why |
|---|---|
| `-D MAX_NUM_SEGMENTS=64` | One segment per step. WLED's own limit is 32, or 64 on a board with PSRAM — the patch in [Part 4](../04-behaviour-patches/README.md) lets the build ask for a number instead of inferring it |
| `-D STAIRCASE_V2` | Gates patches P3–P6, so the same usermod source still builds the older classic-ESP32 firmware unchanged |
| `custom_usermods = Animated_Staircase audioreactive` | The staircase logic, and the microphone support the Disco preset will want |
| `-DBOARD_HAS_PSRAM` + `memory_type = qio_opi` (inherited) | 8 MB octal PSRAM, which is what allows more than 32 segments |
| `-D ARDUINO_USB_CDC_ON_BOOT=1` | This board has only the S3's native USB, no serial chip |
| `-D WLED_WATCHDOG_TIMEOUT=0` | Inherited from the stock S3 env |

## Flashing it

**Over USB, from scratch** (a bare board, or one running something else):

1. Plug the board into a USB **data** cable. Check it appears:
   `ls /dev/cu.usb*` on macOS, Device Manager → Ports on Windows. The S3's native
   USB shows up as an *Espressif USB JTAG/serial debug unit*.
2. In Chrome or Edge, open [esptool-js](https://espressif.github.io/esptool-js/),
   connect at 921600 baud, **Erase Flash**, then program
   `WLED_16.0.1_ESP32-S3_Staircase_FACTORY.bin` at address `0x0`.
3. Press reset. Join it to Wi-Fi through the **WLED-AP** hotspot (password
   `wled1234`) at `http://4.3.2.1`, then find its address on your network.
4. Load the settings and presets: [Part 5](../05-wled-settings/README.md).

**Updating a board that already runs this firmware:** WLED UI → Config →
Security & Updates → Manual OTA → the `_OTA.bin` file.

## Building it yourself

```bash
git clone --depth 1 --branch v16.0.1 https://github.com/wled/WLED.git WLED-src
cd WLED-src
git apply ../parts/04-behaviour-patches/patches/*.patch
cp ../parts/03-firmware/platformio_override.ini .
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/pio run -e esp32s3_staircase                 # about 5 minutes, longer the first time
.venv/bin/pio run -e esp32s3_staircase -t upload --upload-port /dev/cu.usbmodem1101   # yours will differ
```

Node.js 20 must be on your PATH: WLED builds its web UI as part of the build.

The app lands in `.pio/build/esp32s3_staircase/firmware.bin` — that is the OTA
file. `pio run -t upload` writes the bootloader and partition table too, so the
factory image is only needed for browser flashing. To rebuild the factory image:

```bash
esptool.py --chip esp32s3 merge_bin -o FACTORY.bin \
  --flash_mode dio --flash_freq 80m --flash_size 16MB \
  0x0 .pio/build/esp32s3_staircase/bootloader.bin \
  0x8000 .pio/build/esp32s3_staircase/partitions.bin \
  0xe000 ~/.platformio/packages/framework-arduinoespressif32/tools/partitions/boot_app0.bin \
  0x10000 .pio/build/esp32s3_staircase/firmware.bin
```

## Add just this part

1. Flash the factory image over USB, as above.
2. Join it to Wi-Fi and give it a name **before** adding it to Home Assistant —
   Home Assistant builds its entity IDs from the name and won't rename them later
   ([Part 7](../07-home-assistant/README.md)).
3. Check what you've got: `python3 parts/08-testing/check_device.py --host <ip>`.
   The firmware checks pass as soon as it's flashed; the LED and usermod ones
   need [Part 5](../05-wled-settings/README.md).

---

[← Part 2 · Wiring and power](../02-wiring/README.md) · [All parts](../../README.md#the-parts) · [Part 4 · The six behaviour patches →](../04-behaviour-patches/README.md)
