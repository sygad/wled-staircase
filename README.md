# WLED Staircase Lights

Stair lights that sweep on one step at a time when you press a button at the bottom or top of the stairs, then sweep off again a few seconds later.

It runs on an ESP32 with **WLED 16.0.1** and the **Animated Staircase** usermod. It's a complete standalone device: Home Assistant control is an optional extra.

> 📷 *Build photo coming soon.*
<!-- TODO: add images/build-photo.jpg and replace the line above with: ![Build photo](images/build-photo.jpg) -->

This page is the quick start. It has everything you need to build and use the project. The [docs/](docs/) folder has more detail on each part.

---

## What you get

- **Press the bottom button:** the stairs light bottom to top, stay on, then switch off bottom to top.
- **Press the top button:** the same, top to bottom.
- **Three effects:** Sweep (warm white), Rainbow (red at the bottom through to violet at the top), and All (every stair on and off together).
- **Works on its own.** The buttons are wired straight to the ESP32, so no Wi-Fi, app or Home Assistant is needed. Switching effects and changing timings works from WLED's own web page or app.
- **Optional Home Assistant control:** a dashboard card with Bottom and Top buttons and an effect dropdown.

---

## ✅ Do / ❌ Don't

The short version of everything that went wrong while building this.

| ✅ Do | ❌ Don't |
|---|---|
| Fit the **10 kΩ pull-down resistors** on both button pins | Leave the button pins floating. They read "pressed" all the time and nothing happens |
| Connect the ESP32 **GND** to the LED power supply **GND** | Skip the common ground. The LEDs won't respond |
| Set the **brightness limiter** to about 85% of your supply's rating | Leave it at the WLED default (4000 mA) without checking your supply |
| Tap presets to switch effect | **Re-save preset 1, 2 or 3 from the WLED UI.** It drops the staircase setting and breaks Rainbow |
| **Switch to preset 1** before saving any WLED Config page | Save a Config page while preset 3 (All) is active |
| Update the firmware with this project's `OTA.bin` (Manual OTA) | Use WLED's **online update**. Stock firmware removes the staircase feature |
| Keep the on-time longer than the sweep (stairs × delay) | Set the on-time shorter than the sweep. The far end never lights |
| Name the device **before** adding it to Home Assistant | Rename it afterwards. The entity IDs don't change and the automation won't match |
| Flash and test over **USB** with a data cable | Use a charge-only cable. The computer won't see the board |
| Back up the config and presets once it works | Power the ESP32 from USB **and** the LED supply's 5 V at the same time |

---

## Using it day to day (no Home Assistant needed)

Open the WLED page at `http://<ip>` (or `http://<name>.local`), or use the free WLED app for iOS or Android.

**At power-on** it loads preset 1 (**Staircase Warm**) with all LEDs off, ready for a button press. After a power cut it always comes back to Warm.

| To | Do this |
|---|---|
| **Switch effect** | Tap preset **1** Warm, **2** Rainbow or **3** All (or the 1 / 2 / 3 quick-load buttons). This doesn't light anything; it changes what the next press does |
| **Trigger a sweep from your phone** | Tap preset **zz Trigger Bottom** or **zz Trigger Top**. Same as pressing the button |
| **Change speed or on-time** | Switch to preset 1, then **Config → Usermods → Animated Staircase**: `segment-delay-ms` (default 100) and `on-time-s` (default 30). Save |
| **Swap the button directions** | Same page: swap `topPIRorTrigger_pin` and `bottomPIRorTrigger_pin` |
| **Change brightness or colour for now** | Use the slider or colour wheel. It resets at the next reboot |
| **Change brightness or colour for good** | Regenerate the presets with `tools/make_wled_config.py --brightness … --colour …` and upload them. Don't re-save presets 1–3 in the UI |
| **Switch effects on a schedule** | **Config → Time & Macros → Time-Controlled Presets** (needs the clock set up via NTP) |
| **Add a physical effect button** | Wire a button to a free GPIO, then map short / long / double press to presets 1 / 2 / 3 under **Time & Macros → Button Action Presets** |

WLED's own schedules can only do simple time-based rules. Anything conditional, like "only when someone's home", needs Home Assistant.

Full guide, with every setting explained: **[docs/using-wled-standalone.md](docs/using-wled-standalone.md)**

### The presets

| # | Name | What it does |
|---|---|---|
| 1 | Staircase Warm (**boot preset**) | Sweep, warm white (255,160,60) |
| 2 | Staircase Rainbow | Sweep, each stair a fixed colour from red (bottom) to violet (top) |
| 3 | Staircase All | Every stair on and off together, like a normal light switch |
| 6 | zz Trigger Top | Simulates a top button press |
| 7 | zz Trigger Bottom | Simulates a bottom button press |

---

## Hardware

| Part | What I used |
|---|---|
| Controller | Wemos D1 Mini ESP32 (ESP32-WROOM-32, 4 MB flash, CH9102X USB chip). Any classic ESP32 dev board works |
| LEDs | WS2812B strip, GRB, 15 LEDs per stair × 33 stairs = 495 LEDs |
| Power | Separate 5 V supply for the LEDs, sized for your LED count (below) |
| Triggers | 2 × momentary push buttons (bottom and top of the stairs). PIR sensors can replace them later with no config changes |
| Resistors | 1 × 330 Ω (LED data line, close to the strip), 2 × 10 kΩ (button pull-downs) |

### Wiring

![Wiring diagram](images/wiring.svg)

| From | To | Notes |
|---|---|---|
| PSU +5V | Strip +5V | |
| PSU GND | Strip GND **and** ESP32 GND | Common ground is essential |
| ESP32 GPIO 2 | 330 Ω → Strip DIN | Data in at the **bottom** stair. Data flows in the direction of the arrows on the strip |
| ESP32 3V3 | One side of both buttons | |
| ESP32 GPIO 18 | Other side of the **top** button, and 10 kΩ → GND | |
| ESP32 GPIO 19 | Other side of the **bottom** button, and 10 kΩ → GND | |

**Why the pull-downs matter:** a pressed button pulls the pin to 3.3 V (HIGH = pressed). The 10 kΩ resistor holds it at 0 V when it isn't pressed. The firmware turns on the ESP32's weak internal pull-ups, so without the resistors both pins read HIGH all the time and the staircase never reacts.

**Power supply:** each WS2812B LED draws up to about 60 mA at full white, so 495 LEDs could draw about 30 A worst case. Real use (warm white, half brightness) is a fraction of that. Set WLED's brightness limiter (**Config → LED Preferences → Maximum current**) to about 85% of your supply's rating, e.g. 8500 mA for a 10 A supply. On long runs, also feed power into the far end of the strip so the top stairs don't look dim or yellow.

**Powering the ESP32:** on the stairs, use either a USB power supply or the LED supply's 5 V on the ESP32's **5V** pin, never both. Unplug the 5 V wire before connecting USB to a computer.

More detail: [docs/hardware.md](docs/hardware.md)

---

## Get it running

### A. My staircase is the same (33 stairs × 15 LEDs, same pins)

Use the pre-built firmware in [firmware/](firmware/). **The LEDs don't need to be connected** for steps 1–5. Do it all on your desk with the bare ESP32 on USB.

1. **Connect the ESP32 by USB.** Check the computer sees it (`ls /dev/cu.usb*` on macOS, Device Manager → Ports on Windows). If not, try another cable or install the driver for the board's USB chip (CH340, CH9102 or CP210x).
2. **Flash it.** In Chrome or Edge, open [esptool-js](https://espressif.github.io/esptool-js/), connect at 921600 baud, click **Erase Flash**, then program `firmware/WLED_16.0.1_ESP32_Staircase_48seg_FACTORY.bin` at address `0x0`. Press the board's reset button when it's done.
3. **Join it to Wi-Fi.** Connect to the **WLED-AP** hotspot (password `wled1234`), open `http://4.3.2.1` and enter your Wi-Fi details. Find its new IP in your router.
4. **Load the staircase settings** (pick your own device name; it's used for the hostname and Home Assistant entity names):
   ```bash
   python3 tools/make_wled_config.py --name "Staircase Lights" --stairs 33 --leds-per-stair 15 --max-ma 8500
   curl -X POST -H "Content-Type: application/json" -d @out/cfg-update.json http://<ip>/json/cfg
   curl -F "data=@out/presets.json;filename=/presets.json" http://<ip>/upload
   curl -X POST -H "Content-Type: application/json" -d '{"rb":true}' http://<ip>/json/state
   ```
5. **Test it:** `python3 tools/check_device.py --host <ip> --stairs 33 --leds-per-stair 15`. On a bare board, *Trigger inputs idle* fails because the pins float. Jumper GPIO 18 and 19 to GND, then run it again with `--sweep`. ⚠️ Never touch 3V3 to a pin that's jumpered straight to GND.
6. **Wire it up** as in the diagram, with the 10 kΩ resistors in place of the jumpers. Press both buttons. If the directions are reversed, the GPIO 18 and 19 wires are swapped.
7. **Back it up:** Config → Security & Updates → **Backup configuration** and **Backup presets**.

Step by step, with other flashing options: [docs/flash-and-test.md](docs/flash-and-test.md)

### B. My staircase is different (most people)

Use **[Build Your Own Version](#build-your-own-version)** below. Claude Code asks about your setup, then builds and flashes firmware made for your stairs.

The pre-built firmware also works for any staircase of **up to 48 stairs** on a classic ESP32, because the LED count, pins and timings are settings, not compiled in. Follow path A with your own numbers in steps 4 and 5.

---

## Troubleshooting

| Problem | Likely cause |
|---|---|
| Nothing happens when I press a button | Missing pull-down resistors, or no common ground. Check `http://<ip>/json/state`: idle should show `"top-sensor":false,"bottom-sensor":false` |
| The bottom button lights from the top | GPIO 18 and 19 wires swapped. Swap them, or swap the pins in Config → Usermods |
| The far end never lights | On-time shorter than the sweep. Increase `on-time-s` |
| Rainbow shows all one colour | Preset 2 was re-saved from the UI. Upload the presets again |
| The staircase stopped responding after I saved a setting | A Config page was saved while preset 3 was active, or the usermod was switched off. Switch to preset 1, tick `enabled` in Config → Usermods, and save |
| The top stairs look dim or yellow | Voltage drop. Add power injection at the far end of the strip |
| The phone buttons / API triggers do nothing | They only work while the physical inputs read "not pressed", so the pull-downs must be fitted |
| The staircase feature disappeared after an update | Stock WLED was installed. Reflash this project's firmware |

---

## What's different from stock WLED

The full story is in [docs/what-changed.md](docs/what-changed.md). In short:

1. **WLED 0.14 → 16.0.1.** I started on MoonModules WLED-MM 14.x, which is based on WLED 0.14. This project runs on official WLED 16.0.1, built from source. Stock binaries don't include the staircase usermod, so a custom build was needed either way.
2. **Segment limit raised.** Each stair is one WLED segment. Stock WLED allows only 32 segments on an ESP32, and my staircase has 33 stairs, so this build raises the limit to 48.
3. **Faster sweep.** 100 ms per stair, down from the usermod's 150 ms default. A full 33-stair sweep takes about 4 s. The minimum on-time drops from 10 s to 1 s.
4. **Sweep direction fixed.** The lights now switch off in the same direction they came on. Stock code always switched off top to bottom after a single bottom press.
5. **Presets built by hand.** Only segment 0 is selected in each preset (otherwise WLED 16 copies its colour onto every stair, which turned the rainbow solid red), and "All" uses one big segment instead of switching the usermod off. This is why presets 1–3 mustn't be re-saved from the UI.

---

## Home Assistant (optional)

Home Assistant adds a dashboard card showing whether the stairs are lit, **Bottom** and **Top** buttons, and an **effect dropdown** (Sweep / Rainbow / All). Underneath, these just select the same WLED presets you can tap in the WLED UI.

| | |
|---|---|
| **Required** | The [WLED integration](https://www.home-assistant.io/integrations/wled/) (built into Home Assistant) |
| **Required for the Claude Code setup** | Claude Code connected to Home Assistant through an MCP server, e.g. [HA-MCP](https://github.com/homeassistant-ai/ha-mcp) from HACS |
| **Optional** | [Bubble Card](https://github.com/Clooos/Bubble-Card) v3.x via HACS, for the nicer dashboard card |
| **Included** | Effect dropdown helper, an automation that keeps the dropdown and WLED in sync, and two dashboard cards (Bubble Card and built-in only) |

Key points:

- **Name the device first.** Home Assistant sets entity IDs (e.g. `light.staircase_lights_main`, `select.staircase_lights_preset`) from the name when it discovers the device.
- In the WLED integration options, turn on **Keep main light**. Otherwise the main light entity can disappear when "All" reduces the strip to one segment.
- The YAML in [home-assistant/](home-assistant/) uses `DEVICE` as a placeholder. `tools/make_wled_config.py` writes copies with your name filled in to `out/home-assistant/`.

Setup steps: [docs/home-assistant.md](docs/home-assistant.md)

---

## Build Your Own Version

This builds firmware and settings for **your** staircase, using [Claude Code](https://claude.com/claude-code).

### What happens

1. **Questions first.** Claude Code asks about your board, stairs, LEDs, Home Assistant and Bubble Card. It doesn't change anything until it has the full picture.
2. **You approve a plan.** It shows a summary of your answers and every step it's about to take, including what it will install. Nothing happens until you say yes.
3. **It builds and tests.** It compiles the firmware, flashes it over USB, applies the settings, tests the board, then sets up Home Assistant if you chose it.

### ⚠️ Software will be installed on your computer

Building WLED needs these tools. Claude Code asks before installing each one:

| Tool | Why |
|---|---|
| **git** | Downloads the WLED source code |
| **Python 3** | Runs the build tools and the setup scripts in this repo |
| **PlatformIO** | Compiles the firmware. On first run it downloads the ESP32 toolchain (about 1–2 GB) |
| **Node.js 20** | WLED uses it to build its web interface |
| **esptool** | Writes the firmware to the ESP32 (installed with PlatformIO) |
| **USB-to-serial driver** | Only if your computer doesn't recognise the board (e.g. CH340 / CH9102 / CP210x) |

The first build takes about 10–15 minutes. Rebuilds take 1–2 minutes.

### What you need before you start

- [Claude Code](https://claude.com/claude-code) installed
- Your ESP32 and a **USB data cable** (some cables only charge; those won't work)
- Your Wi-Fi name and password, ready to type into the WLED setup page yourself
- If you want Home Assistant: **Claude Code connected to Home Assistant through an MCP server.** I use [HA-MCP](https://github.com/homeassistant-ai/ha-mcp), installed from HACS. This is how Claude Code creates the helper, automation and dashboard card for you. Set it up before you start; see [docs/home-assistant.md](docs/home-assistant.md#connect-claude-code-to-home-assistant-ha-mcp)

### The prompt

Open Claude Code in an empty folder and paste this:

```text
I want to build my own version of the WLED staircase project at
https://github.com/sygad/wled-staircase

Clone that repo into this folder and read README.md, docs/what-changed.md,
docs/hardware.md, docs/flash-and-test.md, docs/using-wled-standalone.md and
docs/home-assistant.md before doing anything else. Then work in three phases.

PHASE 1 - ASK ME EVERYTHING FIRST. Don't install, build or change anything yet.
Ask one question at a time:
1. Is the ESP32 connected to this computer by USB right now?
   If not, tell me to plug it in with a USB data cable (not a charge-only
   cable), then check that the computer can see the board before moving on.
   Remind me the LEDs don't need to be connected yet.
2. What do I want to call this device (e.g. "Staircase Lights")? Explain that
   a fresh WLED install is just called "WLED", which is hard to recognise.
   This name sets the WLED name, the hostname (e.g. staircase-lights.local)
   and the Home Assistant entity IDs (e.g. light.staircase_lights_main).
3. How many stairs do I have?
4. How many LEDs are on each stair?
5. My hardware: which ESP32 board, which LED type and colour order, and which
   GPIO pins for LED data, top button and bottom button. Offer the project's
   defaults (classic ESP32, WS2812B GRB, data GPIO 2, top GPIO 18,
   bottom GPIO 19) and tell me to accept them if I wired it like the diagram.
   Also ask for my LED power supply rating in amps so you can set the
   brightness limiter.
6. Do I want Home Assistant control? Explain it's optional and that the
   physical buttons work without it.
7. If yes: check that you're connected to Home Assistant through an MCP
   server (e.g. HA-MCP): look for Home Assistant tools, or ask me to run
   /mcp. Explain it's required for you to set up Home Assistant for me.
   If it's not connected, point me to the HA-MCP steps in
   docs/home-assistant.md. Explain that Claude Code has to be restarted
   (claude --continue) before a new MCP server shows up. We can carry on
   with the firmware in the meantime.
8. If yes: is the WLED integration set up in Home Assistant? Explain it's
   required for the Home Assistant part.
9. If yes: is Bubble Card installed? If not, would I like to install it?
   Explain it's optional and only changes how the dashboard looks. Without
   it I get a dashboard made from Home Assistant's built-in cards.

PHASE 2 - SHOW ME THE PLAN.
Summarise my answers. List every step, including every tool you'll install
on my computer and why. Run tools/make_wled_config.py with my answers and
show me its summary and any warnings (segment count, sweep time, on-time).
Wait for me to say yes before continuing.

PHASE 3 - BUILD. Ask before installing each tool.
1. Install what's missing: git, Python 3, Node.js 20, PlatformIO (in a Python
   virtual environment), and a USB driver only if the board isn't detected.
2. Clone WLED v16.0.1, apply the patches in firmware/patches/, copy
   firmware/platformio_override.ini in, and set MAX_NUM_SEGMENTS to the value
   in the generated build-flags.txt. If my board isn't a classic ESP32,
   change the env to extend the matching board env from platformio.ini.
3. Build, then flash over USB. For a board that has never run WLED, erase
   the flash first so it gets a clean partition table.
4. Help me connect the ESP32 to Wi-Fi (WLED-AP hotspot, password wled1234,
   or Improv over USB) and find its IP address. I'll type my Wi-Fi password
   myself.
5. Apply the settings: POST the generated cfg-update.json to /json/cfg,
   upload the generated presets.json to /upload, then reboot the ESP32.
6. Run tools/check_device.py against the board. Then have me jumper both
   trigger GPIOs straight to GND and run it again with --sweep. Warn me never
   to touch 3V3 to a pin while it's jumpered to GND. Fix anything that fails.
7. Tell me to unplug it, wire the LEDs and buttons as in images/wiring.svg,
   power it up, and press both buttons. Confirm the bottom button sweeps
   bottom to top and the top button top to bottom. If they're reversed, the
   trigger wires are swapped. If I didn't want Home Assistant, finish here
   with a short summary, and point me to docs/using-wled-standalone.md.
8. Home Assistant (only if I chose it):
   - Confirm the Home Assistant MCP connection works before changing
     anything. If it still isn't connected, stop and help me set it up.
   - Make sure the device was named BEFORE Home Assistant discovered it.
     Home Assistant sets entity IDs from the name at discovery, and renaming
     later doesn't change them, so the automation wouldn't match.
   - If the WLED integration isn't set up, guide me: it usually appears under
     Settings > Devices & services as discovered. If not, add it by IP.
     Don't continue until the device shows up with my chosen name.
   - Turn on "Keep main light" in the WLED integration options.
   - Create the helper and automation from the generated home-assistant/
     folder (entity IDs are already filled in).
   - If I chose to install Bubble Card, guide me through installing it via
     HACS, then add dashboard-bubble-card.yaml. Otherwise add
     dashboard-default.yaml.
   - Test the dashboard's Bottom and Top buttons and the effect dropdown.

Finish with a summary of what was built, the device's IP and hostname, and
where the backups and generated files are.
```


---

## Repo contents

| Path | What it is |
|---|---|
| `docs/using-wled-standalone.md` | Using and adjusting it from the WLED UI, without Home Assistant |
| `docs/hardware.md` | Parts, wiring and power in detail |
| `docs/flash-and-test.md` | Flashing and testing step by step |
| `docs/what-changed.md` | Every change from stock WLED, and why |
| `docs/home-assistant.md` | Home Assistant setup |
| `firmware/` | Pre-built binaries for my staircase, source patches, build config |
| `tools/make_wled_config.py` | Generates WLED presets, settings and Home Assistant YAML for any staircase |
| `tools/check_device.py` | Tests a flashed board over Wi-Fi, no LEDs needed |
| `home-assistant/` | Helper, automation and dashboard YAML templates |
| `images/` | Wiring diagram and build photo |

## Credits

- [WLED](https://github.com/wled/WLED) and its contributors
- The [Animated Staircase usermod](https://github.com/wled/WLED/tree/main/usermods/Animated_Staircase) and its contributors
- [MoonModules WLED-MM](https://github.com/MoonModules/WLED-MM), where this project started
- [Bubble Card](https://github.com/Clooos/Bubble-Card) by Clooos

WLED is licensed under the EUPL-1.2. The patches and firmware in this repo are derived from WLED and fall under the same licence.
