# Flash and test (USB, no LEDs needed)

This guide flashes the **pre-built firmware for my staircase** (33 stairs × 15 LEDs, data GPIO 2, buttons on GPIO 18/19).

If your staircase is different, use **[Build Your Own Version](../README.md#build-your-own-version)** instead. It follows the same steps for you.

---

## Why USB?

Connect the ESP32 **straight to your computer with a USB data cable**:

- **Quicker** than uploading over Wi-Fi
- **Works on a blank board** that isn't on your network yet
- **Recoverable.** If anything goes wrong, you can always reflash over USB

**You don't need the LEDs.** Everything on this page works with just the ESP32 on your desk. Wire it to the stairs at the end.

---

## Step 1: Connect the ESP32

1. Plug the ESP32 into your computer with a **USB data cable**. Charge-only cables won't work.
2. Check the computer can see it:
   - **macOS:** `ls /dev/cu.usb*` should show something like `/dev/cu.usbserial-…`
   - **Windows:** Device Manager → *Ports (COM & LPT)* should list a new COM port
   - **Linux:** `ls /dev/ttyUSB* /dev/ttyACM*`
3. If nothing appears, try a different cable, then install the USB driver for your board's chip (CH340, CH9102 or CP210x; the chip name is printed on the board).

---

## Step 2: Flash the firmware

Pick **one** option.

### Option A: In the browser (nothing to install)

1. Open **https://espressif.github.io/esptool-js/** in Chrome or Edge.
2. Set the baud rate to **921600** and click **Connect**. Pick your ESP32's port.
3. Click **Erase Flash** and wait for it to finish.
4. Under *Program*, set **Flash Address** to `0x0` and choose `firmware/WLED_16.0.1_ESP32_Staircase_48seg_FACTORY.bin`.
5. Click **Program**. When it says it's done, press the board's **RST/EN** button (or unplug and replug it).

### Option B: Command line (esptool)

```bash
pip install esptool
esptool.py --chip esp32 --port /dev/cu.usbserial-XXXX erase_flash
esptool.py --chip esp32 --port /dev/cu.usbserial-XXXX --baud 921600 write_flash 0x0 firmware/WLED_16.0.1_ESP32_Staircase_48seg_FACTORY.bin
```
Replace the port with yours (on Windows, e.g. `COM5`).

### Option C: Upgrade a board that already runs WLED (over Wi-Fi)

Only if the board already runs WLED with the standard 4 MB layout:
**WLED → Config → Security & Updates → Manual OTA update** → choose `firmware/WLED_16.0.1_ESP32_Staircase_48seg_OTA.bin`.

> **FACTORY vs OTA:** the `FACTORY` file is a full image (bootloader + partition table + app) and goes to address `0x0` over USB. The `OTA` file is just the app, for updating an existing WLED install.

---

## Step 3: Connect it to Wi-Fi

1. After flashing, the ESP32 creates a Wi-Fi hotspot called **WLED-AP** (password `wled1234`).
2. Join it from your phone or laptop. The setup page opens, or go to **http://4.3.2.1**.
3. Enter your home Wi-Fi name and password and save.
4. Find the board's new IP address in your router's device list, or at `http://wled-xxxxxx.local`.

---

## Step 4: Load the staircase settings

The firmware starts with WLED defaults. This step adds the LED count, pins, presets and your device name.

1. Generate the settings. Pick your own name; it becomes the WLED name, hostname and Home Assistant entity names:
   ```bash
   python3 tools/make_wled_config.py --name "Staircase Lights" --stairs 33 --leds-per-stair 15
   ```
2. Send them to the board (replace the IP):
   ```bash
   curl -X POST -H "Content-Type: application/json" -d @out/cfg-update.json http://192.168.1.50/json/cfg
   curl -F "data=@out/presets.json;filename=/presets.json" http://192.168.1.50/upload
   sleep 3
   curl -X POST -H "Content-Type: application/json" -d '{"rb":true}' http://192.168.1.50/json/state
   ```
   The last command reboots the board.

> **Name the device before adding it to Home Assistant.** Home Assistant sets the entity IDs from the device name when it first finds the device. Renaming afterwards doesn't change them.

---

## Step 5: Test it (still no LEDs)

Run the checker:

```bash
python3 tools/check_device.py --host 192.168.1.50 --stairs 33 --leds-per-stair 15
```

It checks:

| Check | What it proves |
|---|---|
| WLED version 16.0.1 | The right firmware is running |
| Staircase build | It's this custom build, not stock WLED |
| LED count | The settings were applied |
| Usermod present and enabled | The staircase feature is built in and on |
| Presets installed | Sweep, Rainbow, All and the two trigger presets exist |
| Preset 1 creates N segments | The segment limit is high enough for your stairs |
| Trigger inputs idle | The button inputs read "not pressed" |

### The trigger inputs on a bare board

With nothing connected, the button pins **float HIGH** and read as "pressed", so *Trigger inputs idle* fails. That's expected on a bare board.

To finish testing without the real wiring, use **two jumper wires**:
- **GPIO 18 → GND**
- **GPIO 19 → GND**

Then run the sweep test. It "presses" the bottom button through the API and watches each stair switch on in order:

```bash
python3 tools/check_device.py --host 192.168.1.50 --stairs 33 --leds-per-stair 15 --sweep
```

**Simulate a real button press:** use the two **10 kΩ resistors** instead of bare jumper wires (GPIO 18 → 10 kΩ → GND, GPIO 19 → 10 kΩ → GND, e.g. on a breadboard). Then briefly touch a wire from **3V3** to GPIO 19 (bottom) or GPIO 18 (top). The WLED web page shows the stairs switching on in the segment list.

> ⚠️ **Never touch 3V3 to a pin that's jumpered straight to GND.** That shorts the 3.3 V supply. Only do the 3V3 test with the 10 kΩ resistors in place.

---

## Step 6: Wire it up

Unplug the USB. Wire everything as shown in the [wiring diagram](hardware.md#wiring), with the **10 kΩ pull-downs replacing the jumper wires**. Power it up and:

1. Press the **bottom** button. The stairs light bottom → top, then switch off bottom → top.
2. Press the **top** button. The same, top → bottom.

If the directions are reversed, the GPIO 18 and 19 wires are swapped.

Finally, set the **brightness limiter** to about 85% of your power supply's rating: WLED → Config → LED Preferences → Maximum current.

---

## Backups

Once it's working, save a backup: **WLED → Config → Security & Updates → Backup configuration** and **Backup presets**. Restore them from the same page.
