[← Part 3 · Firmware](../03-firmware/README.md) · [All parts](../../README.md#the-parts) · [Part 5 · WLED settings →](../05-wled-settings/README.md)

# Part 4 · The behaviour patches

Everything that makes the stairs behave the way they should, rather than the way
the stock usermod behaves. Eight numbered changes — P1 to P7 and P9 — plus the
WLED 16 refinements that stop a 64-segment sweep from stuttering.

> The numbering skips P8 because that change turned out not to need firmware:
> Danger's fades come from the two presets' own transition times
> ([Part 6](../06-presets/README.md)), not from the usermod.

## At a glance

| | |
|---|---|
| **Built from** | WLED's [Animated Staircase usermod](https://github.com/wled/WLED/tree/main/usermods/Animated_Staircase), EUPL-1.2 |
| **Files in this folder** | `patches/0001-allow-overriding-MAX_NUM_SEGMENTS.patch` · `patches/0002-staircase-v2-behaviour.patch` |
| **Applies to** | a clean WLED 16.0.1 checkout: `git apply patches/*.patch` |
| **Proved by** | the preset-to-preset test in [Part 8](../08-testing/README.md) |

## The patches

| # | What it does |
|---|---|
| P1 | Minimum on-time drops from 10 s to 1 s |
| P2 | The off-sweep runs in the direction of the latest trigger |
| P3 | The on-time starts when the sweep finishes, not when the button is pressed |
| P4 | Trigger inputs are active-low: a button to ground, no resistors |
| P5 | While the stairs are lit, the opposite sensor is ignored — except in the All layout |
| P6 | Presets can switch the staircase logic on and off cleanly |
| P7 | "All" fades up quickly and down slowly, instead of snapping |
| P9 | Master power comes back on from brightness, so a trigger during a fade-out still lights the stairs |

All of them are unconditional. P4 is the one to be aware of if you adapt this
elsewhere: it inverts the trigger polarity, so it expects a button to ground
rather than a PIR pulling the pin high.

## What I changed

### 1. P1 · A one-second minimum on-time

The usermod clamped `on-time-s` to at least 10 seconds. On stairs that are lit in
6.4 s, 10 s of hold is a long wait for the lights to start clearing.

```c
on_time_ms = min(900, max(1, (int)on_time_ms)) * 1000;   // was max(10, ...)
```

### 2. P2 · The off-sweep follows the trigger

Stock behaviour: the lights always cleared from the top down, whichever end you
came in from. Walking up the stairs, the darkness chased you from behind; walking
down, it ran away in front of you.

The fix is one line. `lastSensor` is the direction the off-sweep uses, and it was
only updated while the stairs were already on:

```c
// before
if (on) lastSensor = topSensorRead; else { ... }
// after: remember the latest trigger's direction, always
lastSensor = bottomSensorRead;
if (!on) { ... }
```

Now a press at the bottom fills bottom → top and clears bottom → top.

### 3. P3 · The on-time starts when the sweep finishes

`autoPowerOff()` measured the hold from the moment of the press, so a 64-step
sweep taking 6.4 s ate most of a 10 s hold, and anything shorter than the sweep
meant the far end never lit at all.

```c
bool fullyOn() { return onIndex == minSegmentId && offIndex == maxSegmentId; }

void autoPowerOff() {
  if (!fullyOn()) return;              // the hold hasn't started yet
  if ((millis() - lastSwitchTime) > on_time_ms) { ... }
}
```

and the clock is reset at the moment the last step lights:

```c
if (on && fullyOn()) lastSwitchTime = millis();
```

The timings in this repo are "sweep, then 5 s with every step lit, then sweep
off" — 17.8 s in total — because of this patch.

### 4. P4 · Active-low trigger inputs

Upstream already sets the trigger pins to `INPUT_PULLUP`, but then reads them as
if a PIR were pulling them **high**. With a plain button to ground that reads
"triggered" the whole time the button is *not* pressed.

```c
bool triggerPinRead(int8_t pin) {
  if (pin < 0) return false;
  return digitalRead(pin) == LOW;      // button to ground
}
```

Upstream read it as `digitalRead(pin)` — a PIR pulling the pin high.

Software triggers are untouched, so Home Assistant's `zz Trigger Bottom` /
`zz Trigger Top` presets still work ([Part 7](../07-home-assistant/README.md)).

### 5. P5 · One direction at a time

With PIRs at both ends, walking up the stairs sets off the top sensor halfway
through the sweep, which reversed the animation mid-walk.

```c
// while on, only the sensor that started it counts (it restarts the on-timer)
if (topSensorRead != bottomSensorRead && on && bottomSensorRead != lastSensor)
  return sensorChanged;
```

The sensor that started the sweep still counts: trip it again and the hold
restarts, so lingering on the stairs keeps the lights on.

**The All layout is exempt**, via the `!singleStep()` guard in the condition
above. All lights every step together, so "direction" means nothing there — and
ignoring the far end only made that button look broken for the seven seconds an
All cycle lasts. In All, either trigger restarts the hold.

### 6. P6 · Presets that switch the logic on and off cleanly

The biggest one, and the one that needed the most testing. Six presets switch the
staircase logic off and run a normal WLED effect instead ([Part 6](../06-presets/README.md)),
and the usermod's own enable/disable did three unwanted things:

- it toggled **master power**, so a preset that wanted the strip on got it turned
  off, or the other way round;
- it played an **off-sweep** on the way out, so switching to Matrix showed 64
  rows draining away first;
- a trigger-only API call (`{"staircase":{"bottom-sensor":true}}`) was treated as
  "enable me", so a trigger could switch the logic back on by itself.

So `enable()` leaves master power and the state update to the preset, and simply
returns to a clean standby:

```c
on = false;
offIndex = onIndex;
for (int i = minSegmentId; i < maxSegmentId; i++) {
  Segment &seg = strip.getSegment(i);
  if (seg.isActive()) seg.setOption(SEG_OPTION_ON, false);
}
```

and the API handler distinguishes the three cases:

```c
} else if (staircase[FPSTR(_enabled)].isNull()) {
  // a trigger-only call must not enable the usermod
}
...
if (en != enabled || (en && staircase[FPSTR(_enabled)].is<bool>())) enable(en);
if (!enabled) return;   // triggers do nothing while disabled
```

The last line matters: it means a stray trigger from Home Assistant while the
stairs are in Matrix or Off mode does nothing at all.

### 7. P7 · "All" fades, and only "All"

The **All** preset puts one segment across the whole staircase
([Part 6](../06-presets/README.md)), so there is no sweep to watch — every step
came on at once and went off at once, which looked like a light switch rather
than something designed. P7 gives that one case a **quick fade up and a slow fade
down**: 0.5 s on, 2 s off.

Two new usermod settings, saved with the rest and clamped to 0–10000 ms:

| Setting | Default | What it does |
|---|---|---|
| `fade-in-ms` | **500** | How long every step takes to come up together |
| `fade-out-ms` | **2000** | How long they take to fade away |

The scope is the interesting part. The fades apply **only when one active segment
covers the whole staircase**:

```c
bool singleStep() { return maxSegmentId - minSegmentId == 1; }

// on the way on, in checkSensors()
strip.setTransition(singleStep() ? fade_in_ms : segment_delay_ms);

// on the way off, in autoPowerOff(), just before on = false
if (singleStep()) strip.setTransition(fade_out_ms);
```

Sweep and Rainbow are left alone on purpose. In those presets each step is its
own segment and `segment-delay-ms` **is** the per-step fade — the 100 ms fade of
one step overlapping the next is exactly what makes a sweep look like a sweep.
Dropping a 500 ms fade in there would smear 64 overlapping steps into mush and
change a mode nobody asked to change.

Measured on the real controller, triggering All twice: the steps are up by about
0.25 s, start fading at 5.3 s, and the strip is dark about 2 s later.

> One honest wrinkle: the on-time starts when the fade-in **begins**, not when it
> finishes, so a 5 s hold really means 0.5 s of ramp and 4.5 s at full brightness.
> It looks right, so it stays.

**Danger fades too, but not from here.** Danger is applied and cleared by Home
Assistant rather than by the usermod, so these two settings never touch it. It
gets the same soft start and finish from the presets' own transition times —
0.2 s up and 0.5 s down, deliberately faster than All, because the whole point
of it is immediacy. See [Part 6](../06-presets/README.md#the-presets) and
[Part 7](../07-home-assistant/README.md).

### 8. P9 · Power back up during a fade-out

The twin of the bug below, and the one that took the longest to find. The
usermod turns master power on when a trigger arrives and the strip is off:

```c
// P9: power back on whenever the master brightness is zero, not just when WLED has
// finished going dark.
if (togglePower && onIndex == offIndex && !bri) toggleOnOff();
```

That test used to read `offMode` instead of `!bri`. **`offMode` only becomes true
once WLED has finished fading to black** — two seconds in the All layout. Trigger
the stairs inside that window and the usermod accepted it, swept the segments,
and left master power off: the staircase stayed completely dark and the button
looked dead. Press it again and the same thing happened.

Only All showed it in practice. Sweep and Rainbow fade out in 100 ms, so the
window is too small to land in. In All, a press one second after the previous
cycle ended hit it every time.

`bri` is the right test because `toggleOnOff()` zeroes it immediately, so it is
true from the instant the power-off starts rather than when the fade finishes.

### 9. The latent bug P7 flushed out

Worth knowing if you adapt this usermod. The power-off guard from the fixes below
waited `2 * segment_delay_ms` — 200 ms here — after the final step before cutting
master power. That was fine while every fade was one step long. Ask for a 2 s
fade-out and the power went off 200 ms in, so the strip snapped to black instead
of fading.

```c
unsigned long fadeOutSettle() {
  return singleStep() ? fade_out_ms + 100 : 2 * segment_delay_ms;
}
```

The bug had been there since the fade fix was written; nothing had ever asked for
a slow fade, so nothing had ever shown it up.

### 10. Three fixes for 64 segments on WLED 16

None of them changes behaviour on paper; all three were visible on the stairs.

| Problem | Fix |
|---|---|
| Every step pushed a full 64-segment state update to the UI and Home Assistant, which stalled the loop and restarted every segment's fade, so rows flashed twice | report only when master power actually changes: `if (bri != briOld) stateUpdated(CALL_MODE_DIRECT_CHANGE);` instead of `colorUpdated()` on every step |
| Loop latency added about 70 ms to every step, so a 100 ms sweep ran at 170 ms | keep a steady rate: `lastTime += segment_delay_ms`, only resyncing to `millis()` if a step is more than two intervals late |
| Switching master power off at the end of the off-sweep restarted the last rows' fades, making them flash twice | wait until the final step's fade has finished: `millis() - lastStepTime > 2 * segment_delay_ms`, then power off and report once |

Each step's fade is also set to exactly one step's length when a sweep starts
(`strip.setTransition(segment_delay_ms)`), so steps fade into each other instead
of snapping.

## Add just this part

1. Clone WLED 16.0.1 and `git apply patches/*.patch`.
2. Copy in `parts/03-firmware/platformio_override.ini` and build `esp32s3_staircase`.
3. Prove it on the board, not on paper:
   `python3 parts/08-testing/check_device.py --host <ip> --sweep`.
4. Adjust the fades if you want to, in **Config → Usermods → Animated
   Staircase**, or with `--fade-in` / `--fade-out` on
   [`tools/make_staircase.py`](../../tools/make_staircase.py).

---

[← Part 3 · Firmware](../03-firmware/README.md) · [All parts](../../README.md#the-parts) · [Part 5 · WLED settings →](../05-wled-settings/README.md)
