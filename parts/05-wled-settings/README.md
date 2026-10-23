[← Part 4 · The six behaviour patches](../04-behaviour-patches/README.md) · [All parts](../../README.md#the-parts) · [Part 6 · The nine presets →](../06-presets/README.md)

# Part 5 · WLED settings

The settings that turn a flashed board into a staircase: the LED output, the 2D
matrix, the power limit and the usermod. None of this is compiled in, so it can
all be changed later without rebuilding.

## At a glance

| | |
|---|---|
| **Built from** | WLED's own settings pages, or the JSON API |
| **Files in this folder** | this page; the generator is [`tools/make_staircase.py`](../../tools/make_staircase.py) |
| **Reads** | nothing |
| **Writes** | `/json/cfg` on the controller |
| **The real thing** | [`device/cfg.json`](../../device/cfg.json) is the exact backup from my controller, with my Wi-Fi name and hostname replaced |

## Settings I chose

| Page | Setting | Value | Why |
|---|---|---|---|
| LED Preferences | LED count | **512** | 64 rows × 8 LEDs |
| | Type | **WS281x** (GRB) | What the panels are |
| | Data GPIO | **12** | Free, not a strapping pin ([Part 2](../02-wiring/README.md)) |
| | Max current | **26000 mA** | ~85 % of the 30 A supply. WLED dims globally rather than letting the rail sag |
| | mA per LED | **55** | WS2812B at full white |
| | Target refresh | **42 fps** | What 512 pixels on one line will actually do |
| 2D Configuration | Panels | **1 panel, 8 wide × 64 high** | One logical matrix, even though it's two physical panels chained |
| | First LED | **bottom** | So segment 0 is the bottom step. Get this wrong and the sweep runs the wrong way |
| | Serpentine | **on** | Matches how the panel rows are wired |
| User Interface | Name | **WLED Staircase v2** | Set it **before** adding the device to Home Assistant ([Part 7](../07-home-assistant/README.md)) |
| Usermods → Animated Staircase | Enabled | **on** | |
| | bottomPIRorTrigger_pin | **4** | |
| | topPIRorTrigger_pin | **5** | |
| | segment-delay-ms | **100** | 100 ms × 64 steps = a 6.4 s sweep |
| | on-time-s | **5** | 5 s with every step lit, measured from the end of the sweep (patch P3) |
| | toggle-on-off | **on** | Lets the usermod bring master power up on a trigger and drop it at the end |
| Usermods → AudioReactive | Enabled | **off** for now | The microphone isn't fitted. Type: generic I2S, SD 15, WS 14, SCK 13 |
| LED Preferences | Boot preset | **1** | After a power cut the stairs come back as Sweep, buttons working, no Home Assistant needed |
| | Boot brightness / power | **255**, **off** | Bright when lit, dark when idle |
| Time & Macros, Sync, MQTT, Alexa | — | **all off** | Nothing else talks to this controller |

Two deliberate omissions: there are **no button actions** configured in WLED
(the usermod owns both pins), and **no time-controlled presets** (Home Assistant
decides when the stairs are live, in [Part 7](../07-home-assistant/README.md)).

## How it works

The sweep timing is the only arithmetic here:

```
sweep        = steps × segment-delay-ms   = 64 × 100 ms = 6.4 s
one trigger  = sweep + on-time + sweep    = 6.4 + 5 + 6.4 = 17.8 s
```

Keep `on-time-s` at or above about a second; the rest is taste. What you must not
do is make the sweep so slow that a walk up the stairs finishes before the light
does.

## Add just this part

With the firmware flashed and the board on your network:

```bash
# writes out/cfg-update.json, out/presets.json and out/palette0.json
python3 tools/make_staircase.py --rows 64 --width 8 --name "WLED Staircase"

# apply the settings
curl -X POST -H "Content-Type: application/json" -d @out/cfg-update.json http://<ip>/json/cfg
```

Or let the script do both the settings and the presets in one go:

```bash
python3 tools/make_staircase.py --rows 64 --width 8 --ip <ip> --apply
```

Then **check the orientation before trusting it**. Light the bottom row only:

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"on":true,"bri":128,"seg":[{"id":0,"start":0,"stop":8,"startY":63,"stopY":64,"on":true,"col":[[255,255,255]]}]}' \
  http://<ip>/json/state
```

If the **top** row lights, your panel is top-start or wired straight: flip
*first LED* or *serpentine* in 2D Configuration, or pass `--straight`.

Finish with [Part 6 · The nine presets](../06-presets/README.md), then
`python3 parts/08-testing/check_device.py --host <ip>` to confirm every setting
above landed.

> ⚠️ Back up both files once it works: Config → Security & Updates → **Backup
> configuration** and **Backup presets**. That pair is the whole device.

---

[← Part 4 · The six behaviour patches](../04-behaviour-patches/README.md) · [All parts](../../README.md#the-parts) · [Part 6 · The nine presets →](../06-presets/README.md)
