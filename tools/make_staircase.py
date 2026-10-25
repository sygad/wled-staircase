#!/usr/bin/env python3
"""Build the WLED settings, presets and palette for a matrix staircase.

Writes (into --out, default ./out):
  cfg-update.json   LED output, 2D matrix, power limit, usermod settings
                    (including the All preset's fade times), boot preset
  presets.json      presets 1-10, ready to upload as /presets.json
  palette0.json     the GEQ palette the Disco preset uses

Nothing is sent anywhere unless you pass --ip, and then only with --apply.

  python3 tools/make_staircase.py --rows 64 --width 8
  python3 tools/make_staircase.py --rows 48 --width 10 --step-ms 150 --on-time 8
  python3 tools/make_staircase.py --ip 192.168.0.42 --apply

Explained in: parts/05-wled-settings/README.md and parts/06-presets/README.md
"""
import argparse, colorsys, json, os, sys, time, urllib.request

WARM = [255, 160, 60]          # the Sweep / All colour
GEQ_PALETTE = [0, "FF0000", 60, "FFFF00", 119, "00FF00", 178, "00FFFF", 238, "0000FF", 255, "0000FF"]
MATRIX_FX, GEQ_FX = 153, 139   # effect IDs: "Matrix" and "GEQ"
CUSTOM_PALETTE_0 = 200         # WLED custom palette IDs count down from 200


def rainbow(row, rows):
    """Red at the bottom row through to violet at the top."""
    r, g, b = colorsys.hsv_to_rgb((row / (rows - 1)) * 0.75, 1, 1)
    return [round(r * 255), round(g * 255), round(b * 255)]


def row_segments(rows, width, colour_for):
    """One segment per step: segment n is row n counted from the bottom."""
    return [{"id": i, "start": 0, "stop": width, "startY": rows - 1 - i, "stopY": rows - i,
             "grp": 1, "spc": 0, "fx": 0,
             "col": [colour_for(i), [0, 0, 0], [0, 0, 0]], "on": False, "sel": i == 0}
            for i in range(rows)]


def full_segment(rows, width, extra):
    """One segment covering the whole matrix; every other segment switched off."""
    seg = {"id": 0, "start": 0, "stop": width, "startY": 0, "stopY": rows,
           "grp": 1, "spc": 0, "on": True, "sel": True}
    seg.update(extra)
    return [seg] + [{"id": i, "stop": 0} for i in range(1, rows)]


def presets(rows, width, bri, danger_in=200, danger_out=500):
    r, f = (lambda c: row_segments(rows, width, c)), (lambda e: full_segment(rows, width, e))
    return {
        1: ("Stairs Sweep",   {"tt": 0, "on": False, "bri": bri, "seg": r(lambda i: WARM),
                               "staircase": {"enabled": True}}),
        2: ("Stairs Rainbow", {"tt": 0, "on": False, "bri": bri, "seg": r(lambda i: rainbow(i, rows)),
                               "staircase": {"enabled": True}}),
        3: ("Stairs All",     {"tt": 0, "on": False, "bri": bri,
                               "seg": f({"fx": 0, "col": [WARM, [0, 0, 0], [0, 0, 0]], "on": False}),
                               "staircase": {"enabled": True}}),
        # Matrix: speed 128 = 64 ms per row, spawning rate 36 puts about nine
        # drops on the stairs at once, trail 26 is a slow fade so each one
        # reads about ten steps long. Custom colour ON with pure greens: the
        # effect's own colours are a near-white head and a red-and-blue-tinted
        # trail. These are gamma-corrected on the way out, so the trail lands
        # at about (0, 105, 0) on the LEDs.
        4: ("Stairs Matrix",  {"tt": 0, "on": True, "bri": bri,
                               "seg": f({"fx": MATRIX_FX, "sx": 128, "ix": 36, "c1": 26, "o1": True,
                                         "col": [[0, 255, 0], [0, 170, 0], [0, 0, 0]]}),
                               "staircase": {"enabled": False}}),
        5: ("Stairs Disco",   {"tt": 0, "on": True, "bri": bri,
                               "seg": f({"fx": GEQ_FX, "o1": False, "pal": CUSTOM_PALETTE_0, "c1": 255}),
                               "staircase": {"enabled": False}}),
        # Danger is applied and cleared by Home Assistant, not by the usermod, so its
        # fades are the preset's own transition time: tt is in units of 100 ms.
        6: ("Stairs Danger",  {"tt": danger_in // 100, "on": True, "bri": bri,
                               "seg": f({"fx": 0, "col": [[255, 0, 0], [0, 0, 0], [0, 0, 0]]}),
                               "staircase": {"enabled": False}}),
        # Master power off, but the staircase logic stays ENABLED, so the wall buttons
        # keep working when Home Assistant parks the stairs. It carries the row
        # layout as well, in Sweep's warm white: All, Matrix, Disco and Danger all
        # collapse the 64 rows into one full-matrix segment, and this is the resting
        # state Home Assistant returns to, so it is what rebuilds them. Without that
        # the wall buttons light the whole staircase in the last mode's colour -
        # solid red, after a Danger.
        7: ("Stairs Off",     {"tt": 0, "on": False, "seg": r(lambda i: WARM),
                               "staircase": {"enabled": True}}),
        8: ("zz Trigger Bottom", {"staircase": {"bottom-sensor": True}}),
        9: ("zz Trigger Top",    {"staircase": {"top-sensor": True}}),
        # Stairs Off, but fading instead of cutting: how Danger finishes. No staircase
        # key at all, so it never touches whether the usermod is enabled.
        10: ("zz Danger Off",    {"tt": danger_out // 100, "on": False,
                               "seg": f({"fx": 0, "col": [[0, 0, 0], [0, 0, 0], [0, 0, 0]], "on": False})}),
    }


def preset_file(rows, width, bri, danger_in=200, danger_out=500):
    """The same presets as a /presets.json file (slot 0 is WLED's reserved empty slot)."""
    out = {"0": {}}
    for n, (name, body) in presets(rows, width, bri, danger_in, danger_out).items():
        out[str(n)] = dict(body, n=name, ib=True, sb=True)
    return out


def cfg_update(a):
    leds = a.rows * a.width
    return {
        "id": {"name": a.name},
        "hw": {"led": {
            "total": leds, "maxpwr": a.max_ma, "fps": 42,
            "matrix": {"mpc": 1, "panels": [{"b": True, "r": False, "v": False, "s": a.serpentine,
                                             "x": 0, "y": 0, "h": a.rows, "w": a.width}]},
            "ins": [{"start": 0, "len": leds, "pin": [a.data_pin], "order": a.colour_order,
                     "rev": False, "skip": 0, "type": 22, "ref": False, "rgbwm": 0, "freq": 0,
                     "maxpwr": a.max_ma, "ledma": a.led_ma}],
        }},
        "um": {"staircase": {
            "enabled": True, "segment-delay-ms": a.step_ms, "on-time-s": a.on_time,
            "fade-in-ms": a.fade_in, "fade-out-ms": a.fade_out,
            "useTopUltrasoundSensor": False, "topPIRorTrigger_pin": a.top_pin, "topEcho_pin": -1,
            "useBottomUltrasoundSensor": False, "bottomPIRorTrigger_pin": a.bottom_pin,
            "bottomEcho_pin": -1, "top-dist-cm": 50, "bottom-dist-cm": 50, "toggle-on-off": True,
        }},
        "def": {"ps": 1, "on": False, "bri": a.brightness},
    }


def post(ip, obj, path="/json/state"):
    # WLED needs the JSON content type; without it the body is read as form data
    req = urllib.request.Request(f"http://{ip}{path}", json.dumps(obj).encode(),
                                 {"Content-Type": "application/json"})
    return urllib.request.urlopen(req, timeout=20).read().decode()


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--rows", type=int, default=64, help="steps / matrix height (default 64)")
    p.add_argument("--width", type=int, default=8, help="LEDs per step / matrix width (default 8)")
    p.add_argument("--name", default="WLED Staircase", help="WLED device name")
    p.add_argument("--data-pin", type=int, default=12)
    p.add_argument("--bottom-pin", type=int, default=4)
    p.add_argument("--top-pin", type=int, default=5)
    p.add_argument("--step-ms", type=int, default=100, help="milliseconds per step (default 100)")
    p.add_argument("--on-time", type=int, default=5, help="seconds fully lit, after the sweep (default 5)")
    p.add_argument("--fade-in", type=int, default=500, help="ms for the All preset to fade up (default 500)")
    p.add_argument("--fade-out", type=int, default=2000, help="ms for the All preset to fade away (default 2000)")
    p.add_argument("--danger-in", type=int, default=200, help="ms for Danger to fade up (default 200)")
    p.add_argument("--danger-out", type=int, default=500, help="ms for Danger to fade away (default 500)")
    p.add_argument("--max-ma", type=int, default=26000, help="power limit in mA, ~85%% of your supply")
    p.add_argument("--led-ma", type=int, default=55, help="mA per LED at full white (default 55)")
    p.add_argument("--brightness", type=int, default=255)
    p.add_argument("--colour-order", type=int, default=0, help="0 = GRB (WS2812B), 1 = RGB")
    p.add_argument("--straight", dest="serpentine", action="store_false",
                   help="panel is wired straight, not serpentine")
    p.add_argument("--out", default="out")
    p.add_argument("--ip", help="controller address, for --apply")
    p.add_argument("--apply", action="store_true", help="send the settings and presets to --ip")
    a = p.parse_args()

    if a.rows * a.width > 1024:
        p.error("that is a lot of LEDs for one output; split it across pins by hand")
    if a.on_time < 1:
        p.error("the usermod's minimum on-time is 1 s")
    if not (0 <= a.fade_in <= 10000 and 0 <= a.fade_out <= 10000):
        p.error("the fades are clamped to 0-10000 ms by the firmware")
    for name, ms in (("--danger-in", a.danger_in), ("--danger-out", a.danger_out)):
        if not (0 <= ms <= 65500 and ms % 100 == 0):
            p.error(f"{name} is a preset transition time: 0-65500 ms, in whole 100 ms steps")

    os.makedirs(a.out, exist_ok=True)
    files = {
        "cfg-update.json": cfg_update(a),
        "presets.json": preset_file(a.rows, a.width, a.brightness, a.danger_in, a.danger_out),
        "palette0.json": {"palette": GEQ_PALETTE},
    }
    for name, obj in files.items():
        with open(os.path.join(a.out, name), "w") as fh:
            json.dump(obj, fh, indent=1)
        print(f"wrote {os.path.join(a.out, name)}")

    sweep = a.rows * a.step_ms / 1000
    print(f"\n{a.rows} steps x {a.width} LEDs = {a.rows * a.width} LEDs"
          f"\nsweep {sweep:.1f} s on, {a.on_time} s lit, {sweep:.1f} s off"
          f" ({2 * sweep + a.on_time:.1f} s per trigger)"
          f"\nAll: fades up over {a.fade_in / 1000:.1f} s, holds, fades away over {a.fade_out / 1000:.1f} s"
          f"\nDanger: fades up over {a.danger_in / 1000:.1f} s, holds, fades away over {a.danger_out / 1000:.1f} s"
          f"\nworst-case draw {a.rows * a.width * a.led_ma / 1000:.1f} A, limited to {a.max_ma / 1000:.1f} A")

    if not a.apply:
        print("\nNothing sent. Upload by hand, or re-run with --ip <address> --apply")
        return
    if not a.ip:
        p.error("--apply needs --ip")

    print(f"\nsending to {a.ip}")
    print("  cfg   ", post(a.ip, files["cfg-update.json"], "/json/cfg"))
    for n, (name, body) in presets(a.rows, a.width, a.brightness, a.danger_in, a.danger_out).items():
        print(f"  preset {n} {name:18s}", post(a.ip, dict(body, psave=n, n=name, o=True, ib=True, sb=True)))
        time.sleep(1.5)
    print("\nUpload the palette by hand (Config -> Security & Updates -> Manual palette upload),")
    print(f"or:  curl -F 'data=@{a.out}/palette0.json;filename=/palette0.json' http://{a.ip}/upload")
    print("Then reboot:  curl -X POST -H 'Content-Type: application/json' -d '{\"rb\":true}'"
          f" http://{a.ip}/json/state")


if __name__ == "__main__":
    sys.exit(main())
