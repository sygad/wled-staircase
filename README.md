# WLED Staircase Lights

Stair lights that sweep on one step at a time when you press a button at the bottom or top of the stairs, then sweep off again a few seconds later.

It runs on an ESP32 with **WLED 16.0.1** and the **Animated Staircase** usermod. Home Assistant control is an optional extra.

> 📷 *Build photo coming soon.*
<!-- TODO: add images/build-photo.jpg and replace the line above with: ![Build photo](images/build-photo.jpg) -->

---

## What you get

- **Press the bottom button:** the stairs light bottom to top, stay on, then switch off bottom to top.
- **Press the top button:** the same, top to bottom.
- **Three effects:** Sweep (warm white), Rainbow (red at the bottom through to violet at the top), and All (every stair on and off together).
- **Works on its own.** The buttons talk straight to the ESP32, so no Wi-Fi, app or Home Assistant is needed.
- **Optional Home Assistant control:** a dashboard card with Bottom and Top buttons and an effect dropdown.

## The two parts

| Part | Needed? | What it is |
|---|---|---|
| **Core** | Yes | ESP32, LED strip, power supply and two push buttons. This is a complete, working project. |
| **Home Assistant** | No, it's a bonus | Dashboard control, effect switching and automations. Needs the WLED integration. Bubble Card is optional. |

---

## What's different from stock WLED

The full story is in [docs/what-changed.md](docs/what-changed.md). In short:

1. **WLED 0.14 → 16.0.1.** I started on MoonModules WLED-MM 14.x, which is based on WLED 0.14. This project runs on official WLED 16.0.1, built from source.
2. **Segment limit removed.** Stock WLED allows only 32 segments on an ESP32. Each stair is one segment, and my staircase has 33 stairs, so this build raises the limit to 48.
3. **Faster sweep.** 100 ms per stair, down from the usermod's 150 ms default. The minimum on-time drops from 10 s to 1 s.
4. **Sweep direction fixed.** The lights now switch off in the same direction they came on. Stock code always switched off top to bottom after a single bottom press.

---

## Choose your path

### A. My staircase is the same (33 stairs × 15 LEDs, same pins)
Flash the pre-built firmware from [firmware/](firmware/) and load the settings. See [docs/flash-and-test.md](docs/flash-and-test.md).

### B. My staircase is different (most people)
Use **[Build Your Own Version](#build-your-own-version)** below. Claude Code asks about your setup, then builds and flashes firmware made for your stairs.

---

## Hardware

Full parts list and notes: [docs/hardware.md](docs/hardware.md)

| Part | What I used |
|---|---|
| Controller | Wemos D1 Mini ESP32 (ESP32-WROOM-32, 4 MB flash, CH9102X USB chip) |
| LEDs | WS2812B strip, GRB, 15 LEDs per stair × 33 stairs = 495 LEDs |
| Power | Separate 5 V supply for the LEDs |
| Triggers | 2 × momentary push buttons (bottom and top of the stairs) |
| Resistors | 1 × 330 Ω (LED data line), 2 × 10 kΩ (button pull-downs) |

### Wiring

![Wiring diagram](images/wiring.svg)

| From | To | Notes |
|---|---|---|
| PSU +5V | Strip +5V | |
| PSU GND | Strip GND **and** ESP32 GND | Common ground is essential |
| ESP32 GPIO 2 | 330 Ω → Strip DIN | Data in at the bottom stair |
| ESP32 3V3 | One side of both buttons | |
| ESP32 GPIO 18 | Other side of the **top** button, and 10 kΩ → GND | |
| ESP32 GPIO 19 | Other side of the **bottom** button, and 10 kΩ → GND | |

> **The 10 kΩ pull-down resistors are required.** Without them both inputs read "pressed" all the time and nothing happens.

---

## Flashing: use USB

Connect the ESP32 **straight to your computer with a USB data cable** to flash and test it. This is better than flashing over Wi-Fi because:

- it's quicker
- it works before the ESP32 is on your Wi-Fi
- you can recover a board that won't boot

**The LEDs don't need to be connected.** Flashing and every check can be done on the bare ESP32 on your desk, before anything is installed on the stairs.

Step-by-step instructions and tests: [docs/flash-and-test.md](docs/flash-and-test.md)

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
docs/hardware.md, docs/flash-and-test.md and docs/home-assistant.md before
doing anything else. Then work in three phases.

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
   with a short summary.
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

## Home Assistant (optional)

Details: [docs/home-assistant.md](docs/home-assistant.md)

| | |
|---|---|
| **Required** | The [WLED integration](https://www.home-assistant.io/integrations/wled/) (built into Home Assistant) |
| **Required for the Claude Code setup** | Claude Code connected to Home Assistant through an MCP server, e.g. [HA-MCP](https://github.com/homeassistant-ai/ha-mcp) from HACS |
| **Optional** | [Bubble Card](https://github.com/Clooos/Bubble-Card) v3.x via HACS, for the nicer dashboard card |
| **Included** | Effect dropdown helper, an automation that keeps the dropdown and WLED in sync, and two dashboard cards (Bubble Card and built-in only) |

---

## Repo contents

| Path | What it is |
|---|---|
| `firmware/` | Pre-built binaries for my staircase, source patches, build config |
| `tools/make_wled_config.py` | Generates WLED presets, settings and Home Assistant YAML for any staircase |
| `tools/check_device.py` | Tests a flashed board over Wi-Fi, no LEDs needed |
| `home-assistant/` | Helper, automation and dashboard YAML templates |
| `docs/` | Step-by-step guides |
| `images/` | Wiring diagram and build photo |

## Credits

- [WLED](https://github.com/wled/WLED) and its contributors
- The [Animated Staircase usermod](https://github.com/wled/WLED/tree/main/usermods/Animated_Staircase) and its contributors
- [MoonModules WLED-MM](https://github.com/MoonModules/WLED-MM), where this project started
- [Bubble Card](https://github.com/Clooos/Bubble-Card) by Clooos

WLED is licensed under the EUPL-1.2. The patches and firmware in this repo are derived from WLED and fall under the same licence.
