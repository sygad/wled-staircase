#!/usr/bin/env python3
"""Check a flashed staircase controller over Wi-Fi. No LEDs needed.

Usage:
  python3 tools/check_device.py --host 192.168.1.50 --stairs 14 --leds-per-stair 20
  python3 tools/check_device.py --host ... --stairs ... --leds-per-stair ... --sweep

--sweep also presses the bottom button through the API and watches the stairs
switch on in order. On a bare ESP32 this needs both trigger pins held LOW: put
a jumper wire from each trigger GPIO to GND (or fit the 10 kOhm pull-downs).

Only uses the Python standard library.
"""
import argparse
import json
import sys
import time
import urllib.request

PRESETS = ["Staircase Warm", "Staircase Rainbow", "Staircase All", "zz Trigger Top", "zz Trigger Bottom"]


def get(host, path):
    with urllib.request.urlopen(f"http://{host}{path}", timeout=10) as r:
        return json.load(r)


def post(host, path, body):
    req = urllib.request.Request(f"http://{host}{path}", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.load(r)


class Checks:
    def __init__(self):
        self.failed = 0

    def check(self, ok, label, hint=""):
        print(("PASS  " if ok else "FAIL  ") + label)
        if not ok:
            self.failed += 1
            if hint:
                print("      -> " + hint)
        return ok


def lit(state):
    return [i for i, s in enumerate(state["seg"]) if s.get("on")]


def sweep_test(host, stairs, c):
    state = get(host, "/json/state")
    sensors = state.get("staircase", {})
    if sensors.get("top-sensor") or sensors.get("bottom-sensor"):
        c.check(False, "Sweep test", "a trigger pin reads HIGH. Jumper both trigger GPIOs to GND first.")
        return
    post(host, "/json/state", {"ps": 1})
    time.sleep(1)
    post(host, "/json/state", {"staircase": {"bottom-sensor": True}})
    order, deadline = [], time.time() + stairs * 0.5 + 5
    while time.time() < deadline and len(order) < stairs:
        for i in lit(get(host, "/json/state")):
            if i not in order:
                order.append(i)
        time.sleep(0.05)
    c.check(len(order) == stairs, f"Bottom press lit all {stairs} stairs (saw {len(order)})")
    c.check(order == sorted(order), "Stairs lit bottom -> top in order",
            "if they lit top -> bottom, the trigger GPIOs are swapped")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--host", required=True, help="IP address or hostname.local")
    p.add_argument("--stairs", type=int, required=True)
    p.add_argument("--leds-per-stair", type=int, required=True)
    p.add_argument("--sweep", action="store_true", help="also run the sweep test (see above)")
    a = p.parse_args()
    c = Checks()

    try:
        info = get(a.host, "/json/info")
    except OSError as e:
        sys.exit(f"Can't reach http://{a.host}: {e}")

    c.check(info.get("ver") == "16.0.1", f"WLED version 16.0.1 (found {info.get('ver')})")
    c.check("Staircase" in str(info.get("release", "")), f"Staircase build (release {info.get('release')})",
            "this is a stock WLED binary without the staircase usermod")
    total = a.stairs * a.leds_per_stair
    c.check(info.get("leds", {}).get("count") == total, f"LED count {total} (found {info.get('leds', {}).get('count')})")

    cfg = get(a.host, "/json/cfg").get("um", {}).get("staircase")
    c.check(cfg is not None, "Animated Staircase usermod present")
    if cfg:
        c.check(cfg.get("enabled") is True, "Usermod enabled")
        c.check(cfg.get("toggle-on-off") is True, "toggle-on-off enabled")
        print(f"      top pin {cfg.get('topPIRorTrigger_pin')}, bottom pin {cfg.get('bottomPIRorTrigger_pin')}, "
              f"{cfg.get('segment-delay-ms')} ms/step, on-time {cfg.get('on-time-s')} s")

    names = {v.get("n") for v in get(a.host, "/presets.json").values()}
    missing = [n for n in PRESETS if n not in names]
    c.check(not missing, "Presets installed", f"missing: {', '.join(missing)}")

    post(a.host, "/json/state", {"ps": 1})
    time.sleep(1.5)
    state = get(a.host, "/json/state")
    c.check(len(state.get("seg", [])) == a.stairs, f"Preset 1 creates {a.stairs} segments (found {len(state.get('seg', []))})",
            "if it stops at 32, the firmware was built without a higher MAX_NUM_SEGMENTS")

    sensors = state.get("staircase", {})
    idle = not sensors.get("top-sensor") and not sensors.get("bottom-sensor")
    c.check(idle, f"Trigger inputs idle (top {sensors.get('top-sensor')}, bottom {sensors.get('bottom-sensor')})",
            "pins read HIGH: fit the 10 kOhm pull-downs, or on a bare board jumper the trigger GPIOs to GND")

    if a.sweep:
        sweep_test(a.host, a.stairs, c)

    print()
    print("All checks passed." if c.failed == 0 else f"{c.failed} check(s) failed.")
    sys.exit(1 if c.failed else 0)


if __name__ == "__main__":
    main()
