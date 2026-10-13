# Firmware

## Pre-built binaries (my staircase)

Built for **33 stairs × 15 LEDs = 495 LEDs**, WS2812B GRB, data on GPIO 2, top button GPIO 18, bottom button GPIO 19, classic ESP32 with 4 MB flash.

The pins, LED count and timings are **settings**, not compiled in, so you can change them after flashing. The only compiled-in limit is **48 segments**, i.e. up to 48 stairs. If your stairs fit within that and you use a classic ESP32, these binaries will work. Load your own settings with `tools/make_wled_config.py`.

| File | Use it for | SHA-256 |
|---|---|---|
| `WLED_16.0.1_ESP32_Staircase_48seg_FACTORY.bin` | **USB flashing** to address `0x0`. Full image: bootloader, partition table and app | `6e6714e0a54e7e269413abe3624994f5991c4206824a6c9872d058d54fb0a448` |
| `WLED_16.0.1_ESP32_Staircase_48seg_OTA.bin` | **Updating** a board already running WLED (Manual OTA in the web UI) | `449ab6676b114a3a16d844b4bed0a3094c472bb65331753cb8ecc47cc138da25` |

Version: WLED 16.0.1, release name `ESP32_Staircase`, Animated Staircase usermod, `MAX_NUM_SEGMENTS=48`.

How to flash: [docs/flash-and-test.md](../docs/flash-and-test.md)

> ⚠️ Never use WLED's built-in online update on this controller. Stock binaries don't include the staircase usermod.

## Building from source

Everything needed to rebuild this firmware:

| File | What it does |
|---|---|
| `patches/0001-allow-overriding-MAX_NUM_SEGMENTS.patch` | `wled00/FX.h`: lets the build override the 32-segment ESP32 limit |
| `patches/0002-staircase-sweep-direction-and-min-on-time.patch` | Usermod: the off-sweep follows the trigger direction, and the minimum on-time is 1 s |
| `platformio_override.ini` | Build env `esp32dev_staircase`: classic ESP32 + Animated Staircase usermod + 48 segments |

```bash
git clone --depth 1 --branch v16.0.1 https://github.com/wled/WLED.git WLED-src
cd WLED-src
git apply ../firmware/patches/*.patch
cp ../firmware/platformio_override.ini .
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/pio run -e esp32dev_staircase                                   # build (~12 min the first time)
.venv/bin/pio run -e esp32dev_staircase -t upload --upload-port <your-port>   # flash over USB
```

Needs Node.js 20 on your PATH (WLED builds its web UI during the build).

The built app ends up in `.pio/build/esp32dev_staircase/firmware.bin`. PlatformIO's upload writes the bootloader and partition table too.
