# Using it without Home Assistant

The staircase is a complete, standalone device. The buttons are wired straight to the ESP32, and the sweep logic runs in the firmware. It doesn't need Home Assistant, a phone app or even Wi-Fi to work.

Everything Home Assistant does can also be done from **WLED's own web page** (`http://<ip>` or `http://<name>.local`) or the free **WLED app** for iOS and Android.

---

> ## ⚠️ Read this first: what not to save
>
> The presets that make this work contain settings the WLED web page can't show or keep. **Re-saving them from the UI breaks them.**
>
> | ✅ Safe | ❌ Don't |
> |---|---|
> | Tap a preset to switch effect | Open preset 1, 2 or 3 and press **Save** (it drops the staircase setting and breaks Rainbow) |
> | Change brightness or colour for now (it resets on the next reboot) | Use **"Save to ID"** over preset 1, 2 or 3 |
> | Change the sweep speed and on-time in the Usermods settings | Save any **Config** page while preset 3 (All) is active. Switch to preset 1 first |
> | Make **new** presets for other uses, under new IDs | Use WLED's **online update** button (stock firmware removes the staircase feature) |
>
> If you break a preset, restore your preset backup (Config → Security & Updates → Restore presets), or regenerate the presets with `tools/make_wled_config.py` and upload them again.

---

## What happens by default

| When | What happens |
|---|---|
| **Power on** | Preset 1 (**Staircase Warm**) loads. All LEDs are off |
| **Bottom button** | Warm white lights the stairs one at a time, bottom to top (100 ms per stair) |
| **Top button** | The same, top to bottom |
| **After the on-time** (default 30 s from the last press) | The stairs switch off one at a time, in the same direction they came on |
| **Press again while lit** | The on-time restarts from that press |
| **Power cut or reboot** | Back to preset 1 (Warm), whatever effect was picked before |

---

## Switch effect

On the WLED main page, open **Presets** and tap one, or use the **1 / 2 / 3** quick-load buttons:

| Preset | Quick-load | Effect |
|---|---|---|
| 1 | 1 | **Staircase Warm**: warm white sweep (default) |
| 2 | 2 | **Staircase Rainbow**: sweep, each stair a fixed colour from red (bottom) to violet (top) |
| 3 | 3 | **Staircase All**: every stair switches on and off at once, like a normal light switch |

Picking an effect **doesn't light anything**. It only changes what the next button press does. It lasts until you pick another one, or until the next reboot.

## Trigger a sweep from your phone

Tap one of these presets. They act exactly like pressing the physical button:

| Preset | Does |
|---|---|
| **zz Trigger Bottom** (7) | Same as pressing the bottom button |
| **zz Trigger Top** (6) | Same as pressing the top button |

These only work while the physical buttons read "not pressed", which needs the 10 kΩ pull-down resistors fitted.

From a script or another system:

```bash
curl -X POST -H "Content-Type: application/json" -d '{"staircase":{"bottom-sensor":true}}' http://<ip>/json/state
```

---

## Change the speed and on-time

**Switch to preset 1 first**, then go to **Config → Usermods → Animated Staircase**:

| Setting | What it does | This project |
|---|---|---|
| `enabled` | Turns the staircase feature on. Leave it ticked | on |
| `segment-delay-ms` | Delay between stairs. Lower is faster | 100 |
| `on-time-s` | How long the stairs stay lit, counted **from the button press** | 30 |
| `topPIRorTrigger_pin` / `bottomPIRorTrigger_pin` | Button GPIOs. Swap them if the directions are reversed | 18 / 19 |
| `toggle-on-off` | Switches WLED's master power with the stairs. Leave it ticked | on |
| `useTopUltrasoundSensor` / `useBottomUltrasoundSensor` | For ultrasonic sensors only. Leave them off | off |

Press **Save**. The change applies straight away and survives a reboot.

**The on-time must be longer than the sweep.** The sweep takes `stairs × segment-delay-ms`. For 33 stairs at 100 ms that's about 4 s. If the on-time is shorter, the stairs start switching off before the far end has lit. Leave a few seconds on top of the sweep time at least.

## Change brightness or colour

Moving the brightness slider or colour wheel works, but it only lasts **until the next reboot**, because preset 1 reloads at boot. Don't save the change into preset 1, 2 or 3 (see the warning above).

To make the change permanent, regenerate the presets and upload them again:

```bash
python3 tools/make_wled_config.py --name "Staircase Lights" --stairs 33 --leds-per-stair 15 --brightness 90 --colour 255,140,40
curl -F "data=@out/presets.json;filename=/presets.json" http://<ip>/upload
```

Then reboot the ESP32 (Config → Security & Updates → Reboot, or power-cycle it).

---

## Schedules without Home Assistant

WLED has its own clock and can switch presets at set times. For example, Rainbow on Friday evening and back to Warm at midnight.

1. **Config → Time & Macros → Time setup**: tick **Get time from NTP server** and set your time zone. The ESP32 needs internet access for the clock.
2. Under **Time-Controlled Presets**, add a row: the time (or sunrise/sunset), the days, and the preset number (1, 2 or 3).
3. **Switch to preset 1**, then press **Save**.

Only use presets 1, 2 and 3 here. Schedules switch the effect. They don't light the stairs by themselves.

WLED can only do simple time-based rules. Anything like "only when someone's home", "only when it's dark inside" or linking to other lights needs Home Assistant.

## Optional: a physical effect button

To switch effects without a phone, add a third push button:

1. Wire a push button between a **free GPIO** (e.g. GPIO 23) and **GND**. Don't use GPIO 18 or 19, which are the stair buttons. WLED uses the internal pull-up here, so no resistor is needed.
2. **Config → LED Preferences → Buttons**: set **Button 0** to that GPIO and the type to **Pushbutton**, then save. (On many ESP32 boards, Button 0 defaults to GPIO 0, the board's BOOT button.)
3. **Config → Time & Macros → Button Action Presets**: set Button 0 to, for example, **short press = 1** (Warm), **long press = 2** (Rainbow), **double press = 3** (All).
4. Switch to preset 1 and press **Save** on each page.

---

## Things the WLED UI can't do

| Want to | How |
|---|---|
| Change the number of stairs or LEDs per stair | Regenerate the settings with `tools/make_wled_config.py` and load them again ([flash-and-test.md, step 4](flash-and-test.md#step-4-load-the-staircase-settings)). More than 48 stairs needs a new firmware build |
| Edit preset 1, 2 or 3 | Regenerate them with `tools/make_wled_config.py`, or edit them through the JSON API |
| Update the firmware | Only with this project's firmware: Config → Security & Updates → **Manual OTA**, using the `OTA.bin`. **Never** the online update |

## Backups

Once it works the way you like, save a backup: **Config → Security & Updates → Backup configuration** and **Backup presets**. Restore them from the same page if anything goes wrong.
