#!/usr/bin/env python3
"""Generate WLED presets, config and Home Assistant YAML for any staircase.

Usage:
  python3 tools/make_wled_config.py --name "Staircase Lights" --stairs 14 --leds-per-stair 20

Writes to ./out (change with --out):
  presets.json        upload via WLED -> Config -> Security & Updates -> Restore presets
                      (or: curl -F "data=@presets.json;filename=/presets.json" http://<ip>/upload)
  cfg-update.json     POST to http://<ip>/json/cfg, then reboot
  build-flags.txt     the MAX_NUM_SEGMENTS value the firmware needs
  home-assistant/     the HA YAML with DEVICE replaced by your entity prefix

Only uses the Python standard library.
"""
import argparse
import colorsys
import json
import math
import re
import sys
from pathlib import Path

COLOR_ORDERS = {"GRB": 0, "RGB": 1, "BRG": 2, "RBG": 3, "BGR": 4, "GBR": 5}
STOCK_ESP32_SEGMENTS = 32
TESTED_MAX_SEGMENTS = 48
REPO = Path(__file__).resolve().parent.parent


def slug(text, sep):
    return re.sub(r"[^a-z0-9]+", sep, text.lower()).strip(sep)


def rgb(text):
    parts = [int(p) for p in text.split(",")]
    if len(parts) != 3 or not all(0 <= p <= 255 for p in parts):
        raise argparse.ArgumentTypeError("colour must be R,G,B with values 0-255")
    return parts


def rainbow(n):
    """Red on the bottom stair through to violet on the top stair."""
    cols = []
    for i in range(n):
        hue = (300.0 * i / max(1, n - 1)) / 360.0
        r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
        cols.append([round(r * 255), round(g * 255), round(b * 255)])
    return cols


def stair_segments(n, per, colours):
    # Only segment 0 is selected. WLED 16 copies the first selected segment's
    # colour onto every selected segment when the usermod updates.
    return [
        {"id": i, "start": i * per, "stop": (i + 1) * per, "on": False, "fx": 0,
         "col": [colours[i]], "sel": i == 0}
        for i in range(n)
    ]


def make_presets(a):
    total = a.stairs * a.leds_per_stair
    base = {"on": False, "bri": a.brightness, "mainseg": 0, "staircase": {"enabled": True}}
    warm = [a.colour] * a.stairs
    all_on = [{"id": 0, "start": 0, "stop": total, "on": False, "fx": 0,
               "col": [a.colour], "sel": True}]
    all_on += [{"id": i, "stop": 0} for i in range(1, a.stairs)]  # delete the other segments
    return {
        "0": {},
        "1": {"n": "Staircase Warm", "ql": "1", **base,
              "seg": stair_segments(a.stairs, a.leds_per_stair, warm)},
        "2": {"n": "Staircase Rainbow", "ql": "2", **base,
              "seg": stair_segments(a.stairs, a.leds_per_stair, rainbow(a.stairs))},
        "3": {"n": "Staircase All", "ql": "3", **base, "seg": all_on},
        "6": {"n": "zz Trigger Top", "staircase": {"top-sensor": True}},
        "7": {"n": "zz Trigger Bottom", "staircase": {"bottom-sensor": True}},
    }


def make_cfg(a):
    total = a.stairs * a.leds_per_stair
    return {
        "id": {"name": a.name, "mdns": slug(a.name, "-")},
        "hw": {"led": {"total": total, "maxpwr": a.max_ma, "ins": [{
            "start": 0, "len": total, "pin": [a.data_pin], "order": COLOR_ORDERS[a.color_order],
            "rev": False, "skip": 0, "type": 22, "ref": False, "rgbwm": 0, "freq": 0,
            "maxpwr": a.max_ma, "ledma": 55, "drv": 0, "text": ""}]}},
        "def": {"ps": 1, "on": True, "bri": a.brightness},
        "um": {"staircase": {
            "enabled": True, "segment-delay-ms": a.step_ms, "on-time-s": a.on_time,
            "useTopUltrasoundSensor": False, "topPIRorTrigger_pin": a.top_pin, "topEcho_pin": -1,
            "useBottomUltrasoundSensor": False, "bottomPIRorTrigger_pin": a.bottom_pin,
            "bottomEcho_pin": -1, "top-dist-cm": 50, "bottom-dist-cm": 50, "toggle-on-off": True}},
    }


def segments_needed(stairs):
    if stairs <= STOCK_ESP32_SEGMENTS:
        return STOCK_ESP32_SEGMENTS
    return int(math.ceil((stairs + 8) / 8.0) * 8)  # a little headroom, multiple of 8


def render_ha(out, entity_prefix):
    src = REPO / "home-assistant"
    dst = out / "home-assistant"
    dst.mkdir(parents=True, exist_ok=True)
    for f in sorted(src.glob("*.yaml")):
        (dst / f.name).write_text(f.read_text().replace("DEVICE", entity_prefix))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--name", required=True, help='device name, e.g. "Staircase Lights"')
    p.add_argument("--stairs", type=int, required=True)
    p.add_argument("--leds-per-stair", type=int, required=True)
    p.add_argument("--data-pin", type=int, default=2)
    p.add_argument("--top-pin", type=int, default=18)
    p.add_argument("--bottom-pin", type=int, default=19)
    p.add_argument("--color-order", default="GRB", choices=COLOR_ORDERS)
    p.add_argument("--colour", type=rgb, default=[255, 160, 60], help="sweep colour R,G,B (default warm white)")
    p.add_argument("--brightness", type=int, default=128)
    p.add_argument("--step-ms", type=int, default=100, help="delay between stairs")
    p.add_argument("--on-time", type=int, default=30, help="seconds the stairs stay lit")
    p.add_argument("--max-ma", type=int, default=4000, help="brightness limiter, ~85%% of the PSU rating")
    p.add_argument("--out", default="out")
    a = p.parse_args()

    if a.stairs < 2 or a.leds_per_stair < 1:
        sys.exit("Need at least 2 stairs and 1 LED per stair.")

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "presets.json").write_text(json.dumps(make_presets(a), separators=(",", ":")))
    (out / "cfg-update.json").write_text(json.dumps(make_cfg(a), indent=2))

    segs = segments_needed(a.stairs)
    (out / "build-flags.txt").write_text(f"-D MAX_NUM_SEGMENTS={segs}\n")

    entity_prefix = slug(a.name, "_")
    render_ha(out, entity_prefix)

    sweep_s = a.stairs * a.step_ms / 1000.0 * 1.2  # measured: 33 stairs at 100 ms took ~4 s
    print(f"Device name      : {a.name}")
    print(f"Hostname         : {slug(a.name, '-')}.local")
    print(f"LEDs             : {a.stairs} stairs x {a.leds_per_stair} = {a.stairs * a.leds_per_stair}")
    print(f"MAX_NUM_SEGMENTS : {segs}" + ("  (stock limit is fine)" if segs == STOCK_ESP32_SEGMENTS else "  (custom build needed)"))
    print(f"Full sweep       : ~{sweep_s:.1f} s at {a.step_ms} ms per stair")
    print(f"HA entities      : light.{entity_prefix}_main, select.{entity_prefix}_preset")
    print(f"Files written to : {out.resolve()}")

    if segs > TESTED_MAX_SEGMENTS:
        print(f"WARNING: {segs} segments has not been tested on an ESP32 without PSRAM. "
              "It may run short of memory.")
    if a.on_time < sweep_s + 1:
        print(f"WARNING: on-time {a.on_time} s leaves little or no time after the ~{sweep_s:.1f} s sweep. "
              f"The far end may never light. Use at least {math.ceil(sweep_s + 1)} s.")


if __name__ == "__main__":
    main()
