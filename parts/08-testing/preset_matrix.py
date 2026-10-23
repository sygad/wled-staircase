#!/usr/bin/env python3
"""Switch from every preset to every other one and check the result each time.

This is the test that found the preset-switching bugs patch P6 fixes: a stray
off-sweep, master power being toggled behind the preset's back, and a trigger
that switched the staircase logic back on by itself. Those only showed up in
particular pairs, such as "lit Sweep -> Matrix".

  python3 parts/08-testing/preset_matrix.py --host 192.168.0.42
  python3 parts/08-testing/preset_matrix.py --host 192.168.0.42 --rows 48

It drives the real controller for a few minutes and the LEDs will flash about.
It leaves the controller on preset 1.

Explained in: parts/08-testing/README.md
"""
import argparse, sys, time

from check_device import DARK, LIT, NAMES, VIOLET, get, post, usermod_enabled

TARGETS = [1, 2, 3, 4, 5, 6, 7]


def wrong(preset, state, info, rows):
    """Everything that does not match what this preset promises."""
    seg, errs = state["seg"], []
    lit = [g for g in seg if g.get("on")]
    if preset in DARK:
        if state["on"]:
            errs.append("master power on")
        if lit:
            errs.append(f"{len(lit)} segments lit")
        if usermod_enabled(info) != (preset != 7):
            errs.append("staircase logic " + ("off" if preset != 7 else "on"))
        if preset in (1, 2):
            if len(seg) != rows:
                errs.append(f"{len(seg)} segments, expected {rows}")
            elif seg[0]["col"][0] != DARK[preset]:
                errs.append(f"bottom row {seg[0]['col'][0]}")
            elif preset == 2 and seg[rows - 1]["col"][0] != VIOLET:
                errs.append(f"top row {seg[rows - 1]['col'][0]}")
    else:
        on, single, fx, col = LIT[preset]
        if not state["on"]:
            errs.append("master power off")
        if single and (len(lit) != 1 or not seg[0].get("on")):
            errs.append(f"{len(lit)} segments lit, expected 1")
        if seg[0].get("fx") != fx:
            errs.append(f"effect {seg[0].get('fx')}, expected {fx}")
        if col and seg[0]["col"][0] != col:
            errs.append(f"colour {seg[0]['col'][0]}, expected {col}")
        if usermod_enabled(info):
            errs.append("staircase logic on")
    if state.get("ps") != preset:
        errs.append(f"reports preset {state.get('ps')}")
    return errs


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--host", required=True)
    p.add_argument("--rows", type=int, default=64)
    p.add_argument("--settle", type=float, default=1.2, help="seconds to wait after a preset change")
    a = p.parse_args()

    # plain sources, plus two that are mid-animation when the switch happens
    sources = [(n, NAMES[n], None) for n in TARGETS] + \
              [(1, "Stairs Sweep (mid-sweep)", 8), (3, "Stairs All (lit)", 8)]
    runs = fails = 0

    for src, label, trigger in sources:
        for dst in TARGETS:
            post(a.host, {"ps": src})
            time.sleep(a.settle)
            if trigger:
                post(a.host, {"ps": trigger})
                time.sleep(1.5)
            post(a.host, {"ps": dst})
            time.sleep(0.05)
            errs = []
            for sample in range(3):          # three samples: a stray sweep is brief
                d = get(a.host, "/json/si")
                e = wrong(dst, d["state"], d["info"], a.rows)
                if e:
                    errs.append(f"+{sample * 0.25:.2f}s " + ", ".join(e))
                time.sleep(0.25)
            runs += 1
            if errs:
                fails += 1
                print(f"FAIL  {label:28s} -> {NAMES[dst]:14s} {errs}")

    print(f"\n{runs - fails}/{runs} preset changes correct")

    print("\nAnd a sweep still runs afterwards:")
    post(a.host, {"ps": 1})
    time.sleep(1.5)
    post(a.host, {"ps": 8})
    time.sleep(a.rows * 0.05)                # roughly half a 100 ms/step sweep
    half = sum(1 for g in get(a.host, "/json/state")["seg"] if g.get("on"))
    time.sleep(a.rows * 0.05 + 0.5)
    full = sum(1 for g in get(a.host, "/json/state")["seg"] if g.get("on"))
    print(f"  rows lit halfway through: {half} (expect about {a.rows // 2})")
    print(f"  rows lit at the end:      {full} (expect {a.rows})")
    post(a.host, {"ps": 1})
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
