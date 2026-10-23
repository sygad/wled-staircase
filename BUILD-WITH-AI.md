# Build it with an AI

Cloning a repo and editing config by hand is the old way. This page lets your own
AI build the project for your stairs, your board and your Home Assistant — asking
you about your setup first.

Be clear about what this needs, though: an AI **on the computer your board is
plugged into**. It doesn't happen inside a chat window on your phone.

---

## Part 1: For you (the human)

### What happens

1. **Questions first.** It asks about your board, your steps, your LEDs, your
   sensors and whether you use Home Assistant. Nothing is installed or changed
   while it asks.
2. **You approve a plan.** It shows what it understood and every step it's about
   to take, including anything it wants to install.
3. **It builds and checks.** Firmware, settings, presets, then Home Assistant if
   you want it, finishing with the test script in
   [Part 8](parts/08-testing/README.md). If you don't have something — no PIRs,
   no alarm panel, no microphone — that part is left out rather than faked.

### What you need

| | Tested route | What has to be set up first |
|---|---|---|
| **The board** | [Claude Code](https://claude.com/claude-code) on the computer the board is plugged into | A USB **data** cable. The AI installs PlatformIO and esptool after asking. **You** type your Wi-Fi password, into WLED's own setup page — never give it to the AI |
| **Home Assistant** (optional) | Claude Code + [HA-MCP](https://github.com/homeassistant-ai/ha-mcp) from HACS | HA-MCP connected, so the AI can read your entities and create the helpers, automations and card |
| **No AI connection at all** | – | Any chat AI can still read this repo and give you finished config and step-by-step instructions to paste and flash yourself |

Other AI assistants with the same kind of connection should work. Claude Code is
the route I've actually tested.

### The prompt

```text
I want to recreate the WLED Staircase project from
https://github.com/sygad/wled-staircase on my own ESP32 and in my own
Home Assistant.

Read BUILD-WITH-AI.md in that repo first and follow its "Part 2: For the AI"
section exactly. Start with the questions in Step 1, one at a time.
Don't install, create, change or flash anything until I've approved your plan.
```

---

## Part 2: For the AI

You are setting up a WLED staircase controller for this user. Work through the
steps in order. The repo is the source of truth; do not invent values.

### The files

| File | What it is |
|---|---|
| `device/cfg.json` | **The reference controller's full WLED config**, as a backup file. Shows what every setting ends up as |
| `device/presets.json` | **The reference presets 1–9**, byte-for-byte as they run on the real device |
| `device/palette0.json` | The custom palette the Disco preset needs |
| `tools/make_staircase.py` | Generates `cfg-update.json`, `presets.json` and `palette0.json` for the user's own step count and width. **Use this rather than editing JSON by hand** |
| `parts/03-firmware/*.bin` | Pre-built ESP32-S3 firmware: `_FACTORY.bin` for USB flashing at `0x0`, `_OTA.bin` for updating |
| `parts/03-firmware/platformio_override.ini` | The build environments |
| `parts/04-behaviour-patches/patches/*.patch` | The two patches, applied to a clean WLED 16.0.1 checkout |
| `parts/07-home-assistant/*.yaml` | Helpers, three automations, two dashboard cards. Every line needing a change is marked `# CHANGE:` |
| `parts/08-testing/check_device.py` | The acceptance test. Run it at the end |
| `parts/08-testing/preset_matrix.py` | The deeper behaviour test. Offer it if the user changed the patches |

### Rules

- **Never change or delete the user's existing config.** Add alongside it. Their
  existing WLED devices, automations and dashboards stay as they are.
- **Ask before installing anything**, and say what it is.
- **Never guess** an entity ID, a GPIO pin, a device or an IP. Read it, or ask.
- **Copy the config as it is.** Change only what the substitution table says.
  Don't tidy the patches or rewrite the scripts.
- **If the user doesn't have something a part needs, leave that part out** —
  and anything only it uses. Never fake a sensor or a value.
- **Never type the user's passwords or tokens.** Wi-Fi goes into WLED's own
  setup page, typed by them.
- **Flashing is destructive.** Say so, name the board and the port, and get a
  clear yes before erasing or writing flash.
- **Don't flash while the LED supply is connected to the board.** Tell the user
  to unplug the supply's 5 V wire first.

### Step 1: Ask the user

One question at a time, waiting for each answer:

1. **Board:** which ESP32? (This project needs an **ESP32-S3 with PSRAM** for
   more than 32 steps. A classic ESP32 caps out at 32 segments — if that's what
   they have, say so now and offer the 32-step version of the same build.)
2. **Steps:** how many steps, and how many LEDs per step? What LED type
   (WS2812B?) and colour order?
3. **Layout:** separate strips wired as one chain, or chained matrix panels? Is
   the **first LED at the bottom** of the stairs?
4. **Power:** what supply, how many amps? Is the far end of the chain fed too?
5. **Triggers:** push buttons wired to ground, PIRs wired to the board, or
   sensors that already exist in Home Assistant? Which GPIOs are free?
6. **Microphone:** fitted, planned or not wanted? (Only the Disco preset uses it.)
7. **Home Assistant:** in use? Which dashboard should the card go on? Do they
   have occupancy sensors, an alarm panel, a house-wide motion toggle?
8. **Modes:** which of Sweep, All, Rainbow, Matrix, Disco, Danger do they want?
9. **Firmware:** flash the pre-built binary, or build from source? (Building
   needs PlatformIO, Node.js 20 and about 10 minutes.)

### Step 2: Map their setup to this project's roles

Fill in the role table at the end of this file from their answers. Work out:

- `rows` = number of steps, `width` = LEDs per step. **`rows` must be ≤ 64** —
  that is the firmware's compiled-in segment limit. More than 64 needs a rebuild
  with a higher `MAX_NUM_SEGMENTS`.
- the power limit: about 85 % of their supply's rating, in mA.
- the sweep arithmetic: `rows × step-ms` is the sweep; keep the on-time at or
  above 1 s. Tell them the resulting cycle length.
- which presets survive their answers (no microphone is fine — Disco still runs,
  just not sound-reactive; no alarm panel means no Danger).

### Step 3: Show the plan and wait

A table of what you understood, the numbers you derived, every file you will
write or change, and anything you'll install. Then stop and wait for a clear yes.

### Step 4: Firmware

1. Find the port (`ls /dev/cu.usb*` on macOS, `mode` or Device Manager on
   Windows, `ls /dev/ttyUSB* /dev/ttyACM*` on Linux). An ESP32-S3's native USB
   appears as an *Espressif USB JTAG/serial debug unit*.
2. Confirm the LED supply is **not** connected to the board.
3. Pre-built route: flash `parts/03-firmware/WLED_16.0.1_ESP32-S3_Staircase_FACTORY.bin`
   at `0x0` with esptool, or hand them
   [esptool-js](https://espressif.github.io/esptool-js/) to do it in a browser.
4. Build-from-source route: the commands in
   [Part 3](parts/03-firmware/README.md#building-it-yourself), with
   `-D MAX_NUM_SEGMENTS=` set to their step count if it isn't 64.
5. Let **them** join it to Wi-Fi via the WLED-AP hotspot, and have them name the
   device **now**, before Home Assistant ever sees it.

### Step 5: Settings and presets

| What | Where | Change to |
|---|---|---|
| `--rows` | `tools/make_staircase.py` | their step count |
| `--width` | " | their LEDs per step |
| `--data-pin` | " | their LED data GPIO |
| `--bottom-pin` / `--top-pin` | " | their button or PIR GPIOs (`-1` if triggers come only from Home Assistant) |
| `--max-ma` | " | ~85 % of their supply, in mA |
| `--step-ms` / `--on-time` | " | their taste; default 100 ms and 5 s |
| `--colour-order` | " | `0` for GRB, `1` for RGB |
| `--straight` | " | pass it if the panel is not serpentine |
| `--name` | " | their device name |

Run it, show them the summary it prints, then apply with `--ip <their ip>
--apply`, upload `palette0.json`, and reboot the controller.

**Then verify the orientation** with the single-row command in
[Part 5](parts/05-wled-settings/README.md#add-just-this-part) before going on. If
the wrong end lights, fix the 2D settings rather than reversing the presets.

### Step 6: Home Assistant (only if they want it)

1. Add the WLED device through the WLED integration. Nothing in this project uses
   the light entities, only the preset select; turn on **Keep main light** in the
   integration's options only if the user wants to control the strip as a light
   too.
2. Create the three helpers from `parts/07-home-assistant/helpers.yaml`.
3. Create the automations they need: always `automation-apply-state.yaml`;
   `automation-pir-trigger.yaml` only if they have occupancy sensors;
   `automation-danger.yaml` only if they have an alarm panel.
4. Substitute every `# CHANGE:` entity for theirs. The house-wide motion toggle
   condition should be **deleted** if they don't have one, not faked.
5. Add one dashboard card: Bubble Card if they have it, otherwise
   `dashboard-built-in-cards.yaml`.

### Step 7: Check it works

Run, and show them the output:

```bash
python3 parts/08-testing/check_device.py --host <ip> --rows <rows> --width <width>
```

Every line must pass. Then concrete checks you cannot script, asked as questions:

- Tap `zz Trigger Bottom` in WLED: does the **bottom** step light first?
- Press each button: does it sweep from the end you pressed?
- Does every step light before the sweep turns around?
- In Home Assistant, switch Power off: does the preset select show **Stairs Off**?
- Switch the mode: does the select follow within a second?

If they changed the patches, offer `preset_matrix.py` and explain it drives the
LEDs for a few minutes.

### Reference: role table

| Role | Units / type | Used by | Required? | If missing |
|---|---|---|---|---|
| Step count (`rows`) | 1–64 | every part | **yes** | Ask. Don't assume 64 |
| LEDs per step (`width`) | integer | every part | **yes** | Ask |
| LED data GPIO | pin | [2](parts/02-wiring/README.md), [5](parts/05-wled-settings/README.md) | **yes** | Ask. Avoid strapping pins |
| Bottom trigger GPIO | pin | [2](parts/02-wiring/README.md), [4](parts/04-behaviour-patches/README.md) | no | Set `-1`; triggers then come only from Home Assistant |
| Top trigger GPIO | pin | " | no | Set `-1` |
| Supply rating | A | [1](parts/01-hardware/README.md), [5](parts/05-wled-settings/README.md) | **yes** | Ask. Never leave the limiter at the default |
| Occupancy sensor, bottom | `binary_sensor` | [7](parts/07-home-assistant/README.md) | no | Skip automation 1 |
| Occupancy sensor, top | `binary_sensor` | " | no | Skip automation 1, and Danger |
| Alarm panel | `alarm_control_panel` | " | no | Skip Danger; drop it from the modes |
| House motion toggle | `input_boolean` | " | no | Delete that condition from both automations |
| Sun | `sun.sun` | " | yes, if using HA | Built in, nothing to do |
| Microphone | INMP441 on I2S | [1](parts/01-hardware/README.md), [6](parts/06-presets/README.md) | no | Disco still runs, just not sound-reactive |
