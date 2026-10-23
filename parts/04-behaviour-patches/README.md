[← Part 3 · Firmware](../03-firmware/README.md) · [All parts](../../README.md#the-parts) · [Part 5 · WLED settings →](../05-wled-settings/README.md)

# Part 4 · The six behaviour patches

Everything that makes the stairs behave the way they should, rather than the way
the stock usermod behaves. Six numbered changes, P1 to P6, plus the WLED 16
refinements that stop a 64-segment sweep from stuttering.

## At a glance

| | |
|---|---|
| **Built from** | WLED's [Animated Staircase usermod](https://github.com/wled/WLED/tree/main/usermods/Animated_Staircase), EUPL-1.2 |
| **Files in this folder** | `patches/0001-allow-overriding-MAX_NUM_SEGMENTS.patch` · `patches/0002-staircase-v2-behaviour.patch` |
| **Applies to** | a clean WLED 16.0.1 checkout: `git apply patches/*.patch` |
| **Gated by** | `-D STAIRCASE_V2` for P3–P6, so a build without the flag behaves exactly as stock |
| **Proved by** | the preset-to-preset test in [Part 8](../08-testing/README.md) |

## The six patches

| # | What it does | Gated? |
|---|---|---|
| P1 | Minimum on-time drops from 10 s to 1 s | no |
| P2 | The off-sweep runs in the direction of the latest trigger | no |
| P3 | The on-time starts when the sweep finishes, not when the button is pressed | `STAIRCASE_V2` |
| P4 | Trigger inputs are active-low: a button to ground, no resistors | `STAIRCASE_V2` |
| P5 | While the stairs are lit, the opposite sensor is ignored | `STAIRCASE_V2` |
| P6 | Presets can switch the staircase logic on and off cleanly | `STAIRCASE_V2` |

P1 and P2 are improvements anyone would want, so they are unconditional. P3–P6
change behaviour that an existing setup may be relying on — the trigger polarity
most of all — so they sit behind the build flag and leave an unflagged build
behaving exactly as stock.

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
#ifdef STAIRCASE_V2
  return digitalRead(pin) == LOW;      // button to ground
#else
  return digitalRead(pin);             // PIR pulling the pin high
#endif
}
```

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

So under `STAIRCASE_V2`, `enable()` leaves master power and the state update to
the preset, and simply returns to a clean standby:

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

### 7. Three fixes for 64 segments on WLED 16

These live inside the `STAIRCASE_V2` blocks too. None of them changes behaviour
on paper; all three were visible on the stairs.

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
2. Build with `-D STAIRCASE_V2` to get P3–P6, or without it for P1 and P2 only.
3. Prove it on the board, not on paper:
   `python3 parts/08-testing/check_device.py --host <ip> --sweep`.

---

[← Part 3 · Firmware](../03-firmware/README.md) · [All parts](../../README.md#the-parts) · [Part 5 · WLED settings →](../05-wled-settings/README.md)
