# What changed, and why

This project started on MoonModules WLED-MM and ended up on a custom build of official WLED 16.0.1. This page explains each change.

---

## 1. WLED 0.14 → WLED 16.0.1

**Before:** MoonModules **WLED-MM 14.x** from the web installer. WLED-MM is a fork of WLED **0.14**.

**After:** official **WLED 16.0.1**, built from source (git tag `v16.0.1`) with the Animated Staircase usermod built in.

**Why:**
- Stock binaries don't include the Animated Staircase usermod, so a custom build was needed either way.
- Building from source let me fix the segment limit (below).
- The usermod logic is the same in 0.14 and 16.0.1, so the behaviour carried over.

The partition table (`WLED_ESP32_4MB_1MB_FS.csv`) is the same as the old install, so the settings survived the upgrade.

> ⚠️ **Never use WLED's built-in online update** on this controller. Stock release binaries don't include the staircase usermod and will remove it.

---

## 2. The segment limit

The usermod treats **each WLED segment as one stair**. My staircase has **33 stairs**.

Stock WLED on a classic ESP32 without PSRAM allows **32 segments** at most (set in `wled00/FX.h`). The 33rd stair could never light.

**The fix** ([patch 0001](../firmware/patches/0001-allow-overriding-MAX_NUM_SEGMENTS.patch)):
- `wled00/FX.h` now wraps the ESP32 `MAX_NUM_SEGMENTS` value in `#ifndef`, so it can be overridden at build time.
- `platformio_override.ini` sets `-D MAX_NUM_SEGMENTS=48` (33 stairs plus headroom).

The firmware is 1.27 MB, which fits the 1.5 MB app slot with room to spare.

If you have 32 stairs or fewer you don't need a higher limit. `tools/make_wled_config.py` works out the right number for you.

---

## 3. Sweep speed and on-time

| Setting | Usermod default | This project |
|---|---|---|
| Delay between stairs | 150 ms | **100 ms** |
| Minimum on-time allowed | 10 s | **1 s** |
| On-time used | 30 s | 30 s (mine is currently 7 s while testing) |

At 100 ms per stair, a full 33-stair sweep takes about **4 seconds** (measured).

**Patch 0002** lowers the on-time minimum from 10 s to 1 s, so short on-times can be used for testing.

> The on-time counts from the button press, not from when the sweep finishes. It must be longer than the sweep, or the far end of the stairs never lights. The config tool warns you if it's too short.

---

## 4. Sweep direction

**Stock behaviour:** a single bottom press lit the stairs bottom → top, but then switched them off **top → bottom**. The usermod only remembered the direction when you pressed again while the lights were already on.

**Fixed behaviour** (also in [patch 0002](../firmware/patches/0002-staircase-sweep-direction-and-min-on-time.patch)): every press records its direction.
- Bottom press: on bottom → top, off bottom → top
- Top press: on top → bottom, off top → bottom

It looks like walking through the light: it follows you up or down the stairs.

---

## 5. How the presets are built

| # | Name | What it does |
|---|---|---|
| 1 | Staircase Warm (**boot preset**) | Sweep effect: one segment per stair, warm white (255,160,60). Standby = master off, all stairs dark |
| 2 | Staircase Rainbow | Same as 1, but each stair has a fixed colour from red (bottom) to violet (top) |
| 3 | Staircase All | One segment covering every LED. A press turns all stairs on together, and they go off together |
| 6 | zz Trigger Top | Simulates a top button press: `{"staircase":{"top-sensor":true}}` |
| 7 | zz Trigger Bottom | Simulates a bottom button press: `{"staircase":{"bottom-sensor":true}}` |

Things that took a while to work out:

- **Only segment 0 is selected** in each preset. WLED 16 copies the first selected segment's colour onto *every* selected segment whenever the usermod updates. With all segments selected, the rainbow turned solid red.
- **"All" uses one big segment** instead of switching the usermod off. Switching the usermod off with toggle-on-off enabled flipped the master power unpredictably.
- **The usermod stays enabled in every preset.** Picking an effect never lights anything; it only changes what the next button press does.

---

## Gotchas

1. **Pull-down resistors are required** on both trigger pins. The usermod treats HIGH as "pressed", so a floating pin reads as pressed all the time.
2. **Don't re-save presets 1–3 from the WLED web UI.** The UI drops the `staircase` setting and changes which segments are selected. Edit presets through the JSON API, or regenerate them with `tools/make_wled_config.py`. What's safe to change in the UI is listed in [using-wled-standalone.md](using-wled-standalone.md).
3. **Switch to preset 1 before saving any WLED Config page.** WLED 16 saves the usermod's *current* enabled state with the config.
4. **API triggers only work while the physical pins read LOW**, i.e. not pressed and pulled down properly.
5. **Set the brightness limiter** (LED Preferences → max current) to about 85% of your LED power supply's rating. The WLED default is 4000 mA.
