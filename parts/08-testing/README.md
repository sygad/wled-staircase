[← Part 7 · Home Assistant](../07-home-assistant/README.md) · [All parts](../../README.md#the-parts)

# Part 8 · Testing

Two scripts. One reads the controller and tells you whether it is set up
correctly; the other drives it and tells you whether it *behaves* correctly.
They are how the behaviour patches in [Part 4](../04-behaviour-patches/README.md)
were proved, rather than hoped for.

## At a glance

| | |
|---|---|
| **Built from** | WLED's JSON API and Python 3's standard library — no packages to install |
| **Files in this folder** | `check_device.py` (settings and presets) · `preset_matrix.py` (every preset change) |
| **Reads** | `/json/si`, `/json/cfg`, `/presets.json` on the controller |
| **Writes** | nothing, unless you pass `--presets`, `--sweep`, or run `preset_matrix.py` |
| **Needs** | the controller on your network; the LEDs can be disconnected for everything except `--sweep` |

## check_device.py

```bash
python3 parts/08-testing/check_device.py --host <ip>             # read-only
python3 parts/08-testing/check_device.py --host <ip> --presets    # also apply each preset
python3 parts/08-testing/check_device.py --host <ip> --sweep      # also trigger and time a sweep
python3 parts/08-testing/check_device.py --host <ip> --rows 48 --width 10 --step-ms 150
```

It checks, in this order:

| Group | What it proves |
|---|---|
| Firmware | enough segments for your steps, and the staircase usermod is in the build |
| LED output | LED count, data pin, the 2D matrix size, **that the first LED is at the bottom**, and that a power limit is set |
| Staircase usermod | both trigger pins, `toggle-on-off`, the step delay, the on-time, and that it boots into preset 1 |
| Trigger inputs | both inputs read "not triggered" right now — a held button, a swapped wire or a floating pin shows up here |
| Presets | all nine exist, with the right names |
| `--presets` | each preset actually does what it promises: dark and waiting, or lit with the right effect and colour, with the staircase logic on or off to match |
| `--sweep` | a real trigger lights every row, and reaches halfway at about the time the arithmetic says it should |

A clean run on my controller:

```
WLED Staircase v2 — WLED 16.0.1 (ESP32-S3_Staircase) on ESP32-S3
...
23 passed, 0 failed
```

Anything that fails prints what it found next to what it expected, so the fix is
usually in the message.

## preset_matrix.py

```bash
python3 parts/08-testing/preset_matrix.py --host <ip>
```

Every preset → every other preset: 63 changes, including two that happen
**mid-animation** (a sweep halfway up, and All fully lit). After each change it
samples the controller three times over half a second, because the bugs it hunts
are brief.

This is the harness that found what patch P6 fixes. Switching away from a lit
Sweep used to play an off-sweep over the top of the new preset; switching to
Matrix sometimes left master power off, so a continuous effect ran into a dark
strip; and a trigger arriving while the logic was disabled switched it back on.
None of that is visible in a single preset change — only in particular pairs.

It takes a few minutes and the LEDs will flash about. It ends on preset 1.

## What to test by hand

Three things no script can see:

1. **Direction.** Press the bottom button. The bottom step must light first. The
   script can check the matrix is configured bottom-start, but only you can see
   which end of the stairs lit.
2. **Dimming at the far end.** Run All at full brightness and look at the top
   steps. Yellow or dim means the power injection isn't doing its job.
3. **Walking it.** Patch P5 exists because walking up the stairs trips the top
   sensor halfway. Walk up, walk down, and stop halfway for ten seconds.

---

[← Part 7 · Home Assistant](../07-home-assistant/README.md) · [All parts](../../README.md#the-parts)
