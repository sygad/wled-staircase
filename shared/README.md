[All parts](../README.md#the-parts)

# Shared tricks

Five things that several parts rely on. Each one cost a long evening to work out,
so they're written down once here instead of being repeated in every page.

| Section | Used by |
|---|---|
| [One segment per step, on a 2D matrix](#one-segment-per-step-on-a-2d-matrix) | [5 WLED settings](../parts/05-wled-settings/README.md) · [6 Presets](../parts/06-presets/README.md) |
| [Why only segment 0 is selected](#why-only-segment-0-is-selected) | [6 Presets](../parts/06-presets/README.md) |
| [The JSON API, and the Content-Type trap](#the-json-api-and-the-content-type-trap) | [6 Presets](../parts/06-presets/README.md) · [8 Testing](../parts/08-testing/README.md) |
| [Power: one source at a time](#power-one-source-at-a-time) | [1 Hardware](../parts/01-hardware/README.md) · [2 Wiring](../parts/02-wiring/README.md) |
| [Presets are the interface](#presets-are-the-interface) | [6 Presets](../parts/06-presets/README.md) · [7 Home Assistant](../parts/07-home-assistant/README.md) |

---

## One segment per step, on a 2D matrix

The staircase usermod lights one **segment** at a time, in segment-ID order. The
panels are one 8 × 64 matrix, and a step is one row of 8 LEDs. So each row gets
its own segment, and segment IDs must count **from the bottom of the stairs**.

In the matrix the first LED is bottom-left, so y = 63 is the bottom row:

```python
# segment n covers row n counted from the bottom
{"id": n, "start": 0, "stop": 8, "startY": 63 - n, "stopY": 64 - n}
```

Get that backwards and a press at the bottom lights the top of the stairs. It is
the single easiest thing to get wrong, and the easiest to check: trigger a sweep
and watch which end lights first.

Effects that cover the whole staircase at once (Matrix, Disco, Danger) use the
opposite layout — **one** segment over the full 8 × 64 area, with every other
segment given `"stop": 0` so WLED drops it.

## Why only segment 0 is selected

In WLED 16, a colour sent to a group of selected segments is copied to **all** of
them. Save a preset from the UI with 64 segments selected and every row ends up
the same colour — which is how the rainbow preset turned solid red.

So every preset here sets `"sel": true` on segment 0 only:

```python
{"id": i, ..., "sel": i == 0}
```

The colours still differ per row, because each segment carries its own `col`.
This is also why presets 1–7 must never be re-saved from the WLED UI: the UI
writes back what it has selected.

## The JSON API, and the Content-Type trap

Everything here is set through `/json/state` and `/json/cfg` rather than the UI,
because it is repeatable and reviewable. One catch: **curl defaults to form
encoding**, and WLED then parses the body as rubbish and silently ignores it.

```bash
# right
curl -X POST -H "Content-Type: application/json" -d '{"ps":1}' http://<ip>/json/state
# wrong: no error, no effect
curl -X POST -d '{"ps":1}' http://<ip>/json/state
```

Python's `urllib` needs the same header passed explicitly — every script in this
repo does it in one helper, `post()`.

## Power: one source at a time

The controller can be fed from USB or from the LED supply's 5 V rail. Never
both: two 5 V sources back-feeding each other is how boards and laptop USB ports
die.

- On the stairs: the 5 V supply, with the USB lead unplugged.
- At the desk: USB, with the 5 V wire off the board.

512 WS2812B LEDs draw up to 28 A at full white. The supply here is 20 A, so the
power limiter is set to 17 A (about 85 % of it) and the far end of the chain
gets its own power injection. The warm white the sweep uses, with every step
lit, comes to about 17.5 A, so the limiter trims it by a few percent; full white
would be cut by about 40 %. Either way the limiter is what stops the LEDs from
overloading the supply or browning out the run. **Set the limiter from the number on your
supply's label**, not from what you think you bought.

## Presets are the interface

Nothing in Home Assistant sends colours, effects or segment layouts to the
controller. It selects a **preset** by name, and the preset carries everything:
segments, colours, effect, master power, and whether the staircase logic is on.

That keeps the two halves independent:

- the stairs work with Home Assistant switched off, because the buttons and the
  boot preset live on the controller;
- Home Assistant can be rebuilt without touching the controller, because all it
  ever does is pick a name from a list.
