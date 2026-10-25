#!/usr/bin/env python3
"""Check a matrix staircase controller: settings, presets, and the sweep itself.

  python3 parts/08-testing/check_device.py --host 192.168.0.42
  python3 parts/08-testing/check_device.py --host 192.168.0.42 --rows 48 --width 10
  python3 parts/08-testing/check_device.py --host 192.168.0.42 --sweep     # also times a real sweep

Read-only unless you pass --sweep or --presets, which switch presets and leave the
controller on preset 1 at the end.

Explained in: parts/08-testing/README.md
"""
import argparse, json, sys, time, urllib.request

WARM, RED, GREEN, VIOLET = [255, 160, 60], [255, 0, 0], [0, 255, 0], [128, 0, 255]
# preset -> (power on?, one full segment?, effect id, first colour)
LIT = {4: (True, True, 153, GREEN), 5: (True, True, 139, None), 6: (True, True, 0, RED)}
DARK = {1: WARM, 2: RED, 3: WARM, 7: WARM, 10: [0, 0, 0]}
NAMES = {1: "Stairs Sweep", 2: "Stairs Rainbow", 3: "Stairs All", 4: "Stairs Matrix",
         5: "Stairs Disco", 6: "Stairs Danger", 7: "Stairs Off",
         8: "zz Trigger Bottom", 9: "zz Trigger Top", 10: "zz Danger Off"}

passes = fails = 0


def check(ok, label, detail=""):
    global passes, fails
    if ok:
        passes += 1
        print(f"  ok    {label}")
    else:
        fails += 1
        print(f"  FAIL  {label}{': ' + detail if detail else ''}")
    return ok


def get(host, path):
    req = urllib.request.Request(f"http://{host}{path}", headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=10).read())


def post(host, obj, path="/json/state"):
    # WLED needs the JSON content type; without it the body is read as form data
    req = urllib.request.Request(f"http://{host}{path}", json.dumps(obj).encode(),
                                 {"Content-Type": "application/json"})
    return urllib.request.urlopen(req, timeout=15).read().decode()


def usermod_enabled(info):
    # the Usermods button offers "disable" while the staircase logic is running
    return "enabled:false" in info.get("u", {}).get("staircase", [""])[0]


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--host", required=True, help="controller IP or name.local")
    p.add_argument("--rows", type=int, default=64)
    p.add_argument("--width", type=int, default=8)
    p.add_argument("--data-pin", type=int, default=12)
    p.add_argument("--bottom-pin", type=int, default=4)
    p.add_argument("--top-pin", type=int, default=5)
    p.add_argument("--step-ms", type=int, default=100)
    p.add_argument("--presets", action="store_true", help="switch through every preset and check each one")
    p.add_argument("--sweep", action="store_true", help="trigger a sweep and time it (implies --presets)")
    a = p.parse_args()

    si = get(a.host, "/json/si")
    info, cfg = si["info"], get(a.host, "/json/cfg")

    print(f"\n{info['name']} — WLED {info['ver']} ({info.get('release', '?')}) on {info.get('arch')}")

    print("\nFirmware")
    check(info["leds"]["maxseg"] >= a.rows, f"{a.rows} segments available",
          f"only {info['leds']['maxseg']} (rebuild with -D MAX_NUM_SEGMENTS={a.rows})")
    check("staircase" in info.get("u", {}), "Animated Staircase usermod present")

    print("\nLED output")
    led = cfg["hw"]["led"]
    check(led["total"] == a.rows * a.width, f"{a.rows * a.width} LEDs", f"found {led['total']}")
    check(led["ins"][0]["pin"][0] == a.data_pin, f"data on GPIO {a.data_pin}",
          f"on GPIO {led['ins'][0]['pin'][0]}")
    m = info["leds"].get("matrix") or {}
    check(m.get("w") == a.width and m.get("h") == a.rows,
          f"2D matrix {a.width} wide x {a.rows} high", f"found {m}")
    panel = (led.get("matrix") or {}).get("panels", [{}])[0]
    check(panel.get("b") is True, "first LED at the bottom", "panel is top-start; tick 'bottom' in 2D setup")
    check(led["maxpwr"] > 0, "power limiter set", "no limit set — size it to your supply")

    print("\nStaircase usermod")
    um = cfg["um"]["staircase"]
    check(um["bottomPIRorTrigger_pin"] == a.bottom_pin, f"bottom trigger on GPIO {a.bottom_pin}",
          f"on {um['bottomPIRorTrigger_pin']}")
    check(um["topPIRorTrigger_pin"] == a.top_pin, f"top trigger on GPIO {a.top_pin}",
          f"on {um['topPIRorTrigger_pin']}")
    check(um["toggle-on-off"] is True, "toggle-on-off on", "off: the rows stay dark on a trigger")
    check(um["segment-delay-ms"] == a.step_ms, f"{a.step_ms} ms per step",
          f"{um['segment-delay-ms']} ms")
    check(um["on-time-s"] >= 1, f"on-time {um['on-time-s']} s")
    if "fade-in-ms" in um:
        check(0 <= um["fade-in-ms"] <= 10000 and 0 <= um["fade-out-ms"] <= 10000,
              f"All fades {um['fade-in-ms']} ms up, {um['fade-out-ms']} ms down")
    else:
        check(False, "patch P7 present (fade-in-ms / fade-out-ms)",
              "this firmware has no fade settings — All will snap on and off")
    check(cfg["def"]["ps"] == 1, "boots into preset 1", f"boots into preset {cfg['def']['ps']}")

    print("\nTrigger inputs idle")
    st = si["state"]
    sensors = get(a.host, "/json/state").get("staircase", {})
    check(sensors.get("bottom-sensor") is False and sensors.get("top-sensor") is False,
          "both inputs read 'not triggered'",
          f"{sensors} — a button is held, miswired, or the pin is floating the wrong way")

    print("\nPresets")
    stored = get(a.host, "/presets.json")
    for n, name in NAMES.items():
        check(stored.get(str(n), {}).get("n") == name, f"preset {n} is '{name}'",
              f"found {stored.get(str(n), {}).get('n')!r}")
    tt_in, tt_out = stored.get("6", {}).get("tt"), stored.get("10", {}).get("tt")
    check(tt_in == 2 and tt_out == 5, "Danger fades 0.2 s up, 0.5 s down (tt 2 and tt 5)",
          f"preset 6 tt {tt_in!r}, preset 10 tt {tt_out!r} — Danger will snap on or off")

    if a.presets or a.sweep:
        print("\nEach preset, applied")
        for n in sorted(DARK) + sorted(LIT):
            post(a.host, {"ps": n})
            time.sleep(1.2)
            d = get(a.host, "/json/si")
            s, i = d["state"], d["info"]
            if n in DARK:
                ok = not s["on"] and not [g for g in s["seg"] if g.get("on")]
                check(ok, f"{n} {NAMES[n]}: dark, waiting for a trigger",
                      f"power {s['on']}, {len([g for g in s['seg'] if g.get('on')])} segments lit")
                if n != 10:  # zz Danger Off deliberately carries no staircase block
                    check(usermod_enabled(i), f"{n} {NAMES[n]}: staircase logic on",
                          "the hardware buttons would be dead")
                if n in (1, 2, 7):
                    # Stairs Off has to carry the rows too: it is the resting state, and
                    # All, Matrix, Disco and Danger all collapse them into one segment
                    check(len(s["seg"]) == a.rows, f"{n} {NAMES[n]}: {a.rows} row segments",
                          f"{len(s['seg'])} — a trigger would light the whole staircase as one block")
                    check(s["seg"][0]["col"][0] == DARK[n], f"{n} {NAMES[n]}: bottom row colour")
                    if n == 2:
                        check(s["seg"][a.rows - 1]["col"][0] == VIOLET,
                              f"{n} {NAMES[n]}: top row violet",
                              f"{s['seg'][a.rows - 1]['col'][0]}")
            else:
                on, single, fx, col = LIT[n]
                check(s["on"] == on and s["seg"][0].get("on") and s["seg"][0]["fx"] == fx,
                      f"{n} {NAMES[n]}: lit, effect {fx}",
                      f"power {s['on']}, fx {s['seg'][0]['fx']}")
                check(not usermod_enabled(i), f"{n} {NAMES[n]}: staircase logic off")
                if col:
                    check(s["seg"][0]["col"][0] == col, f"{n} {NAMES[n]}: colour {col}",
                          f"{s['seg'][0]['col'][0]}")

    if a.presets or a.sweep:
        # The bug this guards: Danger collapses the 64 rows into one full-matrix red
        # segment, and Home Assistant then parks the controller on Stairs Off. If that
        # preset does not rebuild the rows, every later hardware-button press lights the
        # whole staircase solid red instead of sweeping.
        print("\nRecovery from Danger")
        post(a.host, {"ps": 6})
        time.sleep(1.2)
        collapsed = len(get(a.host, "/json/state")["seg"])
        check(collapsed == 1, "Danger collapses the rows into one segment", f"{collapsed} segments")
        post(a.host, {"ps": 7})
        time.sleep(1.2)
        s = get(a.host, "/json/state")
        check(len(s["seg"]) == a.rows and s["seg"][0]["col"][0] == WARM,
              f"Stairs Off rebuilds the {a.rows} rows in warm white",
              f"{len(s['seg'])} segments, bottom row {s['seg'][0]['col'][0]}")

    if a.sweep:
        print("\nA real sweep (preset 1, triggered from the bottom)")
        post(a.host, {"ps": 1})
        time.sleep(1.5)
        t0 = time.time()
        post(a.host, {"ps": 8})
        lit_at = {}
        while time.time() - t0 < a.rows * a.step_ms / 1000 + 2:
            s = get(a.host, "/json/state")
            lit_at[round(time.time() - t0, 1)] = sum(1 for g in s["seg"] if g.get("on"))
            time.sleep(0.4)
        peak = max(lit_at.values())
        check(peak == a.rows, f"every one of the {a.rows} rows lit", f"peak was {peak}")
        half = a.rows * a.step_ms / 2000
        near = [t for t, c in lit_at.items() if c >= a.rows // 2]
        check(near and abs(min(near) - half) < max(1.5, half * 0.4),
              f"half the rows lit around {half:.1f} s in",
              f"first reached at {min(near) if near else 'never'} s")
        print(f"  rows lit over time: {lit_at}")
        post(a.host, {"ps": 1})

    print(f"\n{passes} passed, {fails} failed")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
