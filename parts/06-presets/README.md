[← Part 5 · WLED settings](../05-wled-settings/README.md) · [All parts](../../README.md#the-parts) · [Part 7 · Home Assistant →](../07-home-assistant/README.md)

# Part 6 · The nine presets

The presets are the project's interface. Each one carries the whole picture —
segments, colours, effect, master power, and whether the staircase logic is
running — so switching mode is one API call and nothing can end up half-applied.

## At a glance

| | |
|---|---|
| **Built from** | WLED presets, written through the JSON API |
| **Files in this folder** | this page; the generator is [`tools/make_staircase.py`](../../tools/make_staircase.py) |
| **Also needs** | [`device/palette0.json`](../../device/palette0.json) uploaded to the controller, for the Disco preset |
| **Reads** | nothing |
| **The real thing** | [`device/presets.json`](../../device/presets.json), byte-for-byte what is on my controller |

## The presets

| # | Name | Layout | What it does |
|---|---|---|---|
| 1 | **Stairs Sweep** (boot preset) | 64 row segments | Warm white (255, 160, 60). Fills in the trigger's direction, holds 5 s, empties the same way |
| 2 | **Stairs Rainbow** | 64 row segments | Same sweep, each step a fixed colour: red at the bottom through to violet (128, 0, 255) at the top |
| 3 | **Stairs All** | 1 full segment | Every step together: fades up over 0.5 s, holds 5 s, fades away over 2 s (patch P7) |
| 4 | **Stairs Matrix** | 1 full segment | 2D effect **Matrix** (fx 153), green rain falling top → bottom. Runs continuously, ignores triggers |
| 5 | **Stairs Disco** | 1 full segment | 2D effect **GEQ** (fx 139), bars rising from the bottom, custom palette. Runs continuously, ignores triggers |
| 6 | **Stairs Danger** | 1 full segment | Solid red, everything lit. Used for five seconds at a time by Home Assistant |
| 7 | **Stairs Off** | 1 full segment | Master power off, **staircase logic off** — so the buttons and sensors do nothing at all until another preset is applied |
| 8 | **zz Trigger Bottom** | — | `{"staircase": {"bottom-sensor": true}}`: the same as pressing the bottom button |
| 9 | **zz Trigger Top** | — | `{"staircase": {"top-sensor": true}}`: the same as pressing the top button |

The `zz` prefix keeps the two trigger presets at the end of the dropdown in
Home Assistant and the WLED app, away from the ones you'd pick by hand.

## How it works

Presets 1–3 and 7 leave **master power off** and every segment dark: they set the
stage and wait for a trigger. The usermod brings the power up when a sweep starts
and drops it when the last step has faded (patch P6 and the fade fix in
[Part 4](../04-behaviour-patches/README.md)).

Presets 4–6 are the opposite: master power **on**, one lit segment, staircase
logic **off**. Nothing is waiting for a button, so a stray trigger does nothing.

Two layouts do all of it — [one segment per step, or one segment for the lot](../../shared/README.md#one-segment-per-step-on-a-2d-matrix):

```python
# Sweep / Rainbow: segment n is row n counted from the bottom
{"id": n, "start": 0, "stop": 8, "startY": 63 - n, "stopY": 64 - n, "col": [...], "on": False, "sel": n == 0}

# All / Matrix / Disco / Danger / Off: one segment over the whole matrix,
# and every other segment given "stop": 0 so WLED drops it
{"id": 0, "start": 0, "stop": 8, "startY": 0, "stopY": 64, "on": True, "sel": True}
```

The rainbow's colours are hue 0 → 0.75 spread across the rows, so the top step
lands on violet rather than wrapping back to red:

```python
r, g, b = colorsys.hsv_to_rgb((row / (rows - 1)) * 0.75, 1, 1)
```

**Matrix is tuned, not left on defaults.** Three settings do all the work, and
two of them are easy to read backwards:

| Setting | Value | What it does |
|---|---|---|
| Speed | **128** | The firmware turns this into `(256 - speed) >> 1` = **64 ms per row**, so a drop takes about 4 s to fall 64 steps |
| Spawning rate | **36** | A new drop starts on `(36 + 1) / 256` of steps — about **nine drops** on the stairs at once. The default 128 puts thirty-odd up there, which on a tall matrix is a solid green wall |
| Trail | **26** | Counter-intuitive: it maps to a *fade* amount, so a **lower** number means a **longer** trail. 26 keeps 79% of each pixel's brightness per step, which reads as roughly **ten steps** of tail |
| Custom colour | **off** | With it on, the effect uses the segment colours and you get a flat dark-green rain. Off, it uses its own near-white head and mid-green trail — the classic look |

The [demo](https://sygad.github.io/wled-staircase/) runs that same arithmetic, so
what you see there is what the stairs do.

**Disco needs a palette file.** `pal: 200` is WLED's first *custom* palette slot
(custom palette IDs count down from 200), which means
[`device/palette0.json`](../../device/palette0.json) must be uploaded to the
controller — red, yellow, green, cyan, blue across the GEQ bars. Without it the
bars fall back to the default palette.

## What I changed

1. **Only segment 0 is selected** in every preset. WLED 16 copies a colour across
   all selected segments, which turned the rainbow solid red the first time.
   [The full story](../../shared/README.md#why-only-segment-0-is-selected).
2. **Written through the API, never saved from the UI.** The UI writes back what
   it currently has selected and drops the `staircase` block, which breaks both
   the rainbow and the mode switching. The generator script is the only thing
   that writes these presets.
3. **Instant switching.** Every preset sets `"tt": 0`, so changing mode doesn't
   fade one picture into another — it cuts.
4. **`"ib": true, "sb": true`** on all of them: include brightness and segment
   bounds, so a preset fully defines the state it wants instead of inheriting
   whatever was there before.

> ⚠️ Never re-save presets 1–7 from the WLED UI. If you have, regenerate them:
> `python3 tools/make_staircase.py --rows 64 --width 8 --ip <ip> --apply`.

## Add just this part

```bash
# generate and push presets 1-9
python3 tools/make_staircase.py --rows 64 --width 8 --ip <ip> --apply

# the Disco palette (or use Config -> Security & Updates -> Manual palette upload)
curl -F 'data=@out/palette0.json;filename=/palette0.json' http://<ip>/upload

# reboot so the palette is picked up
curl -X POST -H "Content-Type: application/json" -d '{"rb":true}' http://<ip>/json/state
```

Then try each one from the WLED UI. Presets 1, 2, 3 and 7 should look like
*nothing happened* — that's correct, they're waiting. Tap **zz Trigger Bottom**
to see a sweep.

[Part 8 · Testing](../08-testing/README.md) checks all nine, and what each one
does to the controller's state, in one command.

---

[← Part 5 · WLED settings](../05-wled-settings/README.md) · [All parts](../../README.md#the-parts) · [Part 7 · Home Assistant →](../07-home-assistant/README.md)
