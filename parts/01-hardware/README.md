[All parts](../../README.md#the-parts) · [Part 2 · Wiring and power →](../02-wiring/README.md)

# Part 1 · Hardware

![Wiring diagram](../../images/wiring.svg)

What the controller is made of, and why each piece was chosen over the obvious
cheaper option.

## At a glance

| | |
|---|---|
| **Built from** | diymore ESP32-S3 DevKitC-1 N16R8, two 32 × 8 WS2812B panels, a 5 V 30 A supply |
| **Files in this folder** | this page only |
| **Also needs** | [Part 2 · Wiring and power](../02-wiring/README.md) for how it all joins up |
| **Drives** | 512 LEDs as one 8 × 64 matrix: 64 rows of 8, one row per step |
| **Costs** | about £55 for the board, panels and supply, at 2026 UK prices |

## The parts

| Part | What I used | Why this one |
|---|---|---|
| Controller | **diymore ESP32-S3 DevKitC-1 N16R8** — 16 MB flash, 8 MB octal PSRAM, USB-C | WLED only allows more than 32 segments on a board with PSRAM, and 64 steps needs 64 segments. The S3 also has the headroom for 2D effects and, later, a microphone |
| LEDs | **Two 32 × 8 WS2812B panels**, chained into one 8 × 64 matrix: 512 LEDs | A panel row is a tidy stand-in for a step: 8 LEDs wide, addressable as a block. On real stairs this is one short strip per step, wired as one long chain |
| Power | **5 V 30 A** supply, feeding the panels at both ends | 512 LEDs at full white is about 28 A. See [Power: one source at a time](../../shared/README.md#power-one-source-at-a-time) |
| Triggers | **2 × momentary push buttons** (bottom and top), to GND, no resistors | The firmware uses the ESP32's internal pull-ups, so a press pulls the pin low. Patch P4 in [Part 4](../04-behaviour-patches/README.md) |
| Motion | **Zigbee PIRs already in Home Assistant** | They never touch the ESP32. Home Assistant turns a PIR into a preset selection, so the sensors can be any kind Home Assistant can see |
| Microphone | **INMP441 I2S** — specified, **not fitted yet** | Only the Disco preset wants it. The firmware is already built with `audioreactive` and the pins are set, so fitting it later needs no rebuild |

A classic ESP32 will not do this build: without PSRAM, WLED caps segments at 32,
and it has neither the RAM nor the speed for a 512-LED 2D matrix with sound
input. The older 33-step version on a classic ESP32 is in
[sygad/wled-staircase-old](https://github.com/sygad/wled-staircase-old).

## Settings I chose

- **8 LEDs per step.** Wide enough to look like a lit step rather than a dot,
  narrow enough that 64 steps stay inside one data line.
- **One data pin for all 512 LEDs.** 512 pixels on one WS2812B line refreshes at
  about 42 fps, which is plenty for a sweep. Splitting across two pins would buy
  frame rate the project doesn't need.
- **26 A power limit** in WLED, about 85 % of the supply's rating. WLED dims
  globally rather than letting the rail sag.
- **Power injection at the far end** of the chain, so the top steps aren't dim
  and yellow.

## What I changed from the first version

1. **Classic ESP32 → ESP32-S3 with PSRAM.** 33 stairs needed 33 segments and a
   recompile to lift the 32-segment cap; 64 needs PSRAM, which the S3 has. It
   also unlocked the 2D effects the Matrix and Disco presets use.
2. **Strip per stair → one chained matrix.** WLED can then address the whole
   staircase as a 2D area when an effect wants to, and as 64 one-row segments
   when the sweep wants to. Both layouts live in presets, not in the firmware.
3. **Pull-down resistors → internal pull-ups.** The first version wired each
   button to 3.3 V with a 10 kΩ pull-down, and a missing resistor made the pins
   read "pressed" forever. Buttons now go straight to ground and the firmware
   enables the internal pull-ups, so there is nothing to forget.

## Add just this part

1. Buy the board, the panels and a supply sized for your LED count: LEDs × 60 mA
   is the worst case, and the supply wants about 20 % headroom on top.
2. Count your steps. That number is `--rows` everywhere in this repo, and it must
   be 64 or fewer (the firmware's compiled-in segment limit).
3. Decide the LEDs per step. That is `--width`.
4. Carry on to [Part 2 · Wiring and power](../02-wiring/README.md).

---

[All parts](../../README.md#the-parts) · [Part 2 · Wiring and power →](../02-wiring/README.md)
