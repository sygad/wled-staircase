[← Part 6 · The nine presets](../06-presets/README.md) · [All parts](../../README.md#the-parts) · [Part 8 · Testing →](../08-testing/README.md)

# Part 7 · Home Assistant

Optional. The stairs work on their own: the buttons are wired to the controller
and it boots into Sweep. Home Assistant adds the PIRs, a day/night rule, a mode
dropdown and the red "Danger" flash — and all it ever does is pick a preset by
name.

## At a glance

| | |
|---|---|
| **Built from** | the [WLED integration](https://www.home-assistant.io/integrations/wled/) (built in), three helpers, three automations, and [Bubble Card](https://github.com/Clooos/Bubble-Card) for the nicer card |
| **Files in this folder** | `helpers.yaml` · `automation-pir-trigger.yaml` · `automation-danger.yaml` · `automation-apply-state.yaml` · `dashboard-bubble-card.yaml` · `dashboard-built-in-cards.yaml` |
| **Also needs** | two occupancy sensors (any kind Home Assistant can see), an `alarm_control_panel` for Danger only |
| **Reads** | two PIRs, `sun.sun`, an alarm panel, a house-wide motion toggle |
| **Writes** | `select.<your wled device>_preset` — nothing else |
| **Tested with** | Home Assistant 2026.10.2, Bubble Card v3.4.2 |

Every file is marked up with `# CHANGE:` where an entity ID is mine rather than
yours. Search for `CHANGE`.

## How it works

```
PIR / button ─┐
              ├─> a preset name ─> WLED Staircase ─> the stairs
mode / power ─┘
```

**These are stair lights for the dark.** In daylight they do nothing at all —
there is no point lighting a staircase you can already see. One rule decides
whether they are live:

> **Active** = Power **on** and the house motion toggle **on** and (the sun is
> **below the horizon** or Moon is **on**).

- **Night is the sun, not a clock.** The condition reads `sun.sun`, which Home
  Assistant works out from your latitude and longitude, so the stairs follow
  sunset and sunrise through the year with nothing to adjust. Outside those
  hours Home Assistant holds the controller on **Stairs Off**, and the buttons
  do nothing.
- **Moon forces night mode on.** It is a manual override of that sun condition:
  switch it on and the stairs behave exactly as if the sun had set — on a dark
  winter afternoon, in a windowless stairwell, or to show somebody how it works.
  It **latches**, staying on until you switch it off, so it is not a timer and
  not a brightness setting.
- **Power** is absolute, and sits above both. Off means Stairs Off, buttons
  dead, and the mode reset to Sweep.
- The **house motion toggle** (`input_boolean.motion_sensors` here) is my own
  whole-house "ignore the sensors" switch. Delete that condition if you don't
  have one.

> ### ⚠️ Outside that window the buttons are dead, and that is deliberate
>
> When the stairs aren't active, Home Assistant holds the controller on **Stairs
> Off** — and that preset switches the staircase logic **off**. A disabled
> usermod ignores *everything*: both wall buttons, both motion sensors and the
> trigger presets alike. So in daylight, with Moon off, pressing the button at
> the bottom of the stairs does nothing at all.
>
> This is the most confusing thing in the build. It has already sent me looking
> for a wiring fault that didn't exist.
>
> **To test anything out of hours, switch Moon on first.** That holds the window
> open, so Home Assistant leaves the stairs on a live preset and the buttons
> answer again. Switch it off when you've finished. Without it you are measuring
> a deaf device.

## The three helpers

| Entity | Type | Purpose |
|---|---|---|
| `input_boolean.stairs_s3_power` | toggle | The master switch for the whole thing |
| `input_boolean.stairs_s3_moon` | toggle | Force night mode: keeps the stairs live when the sun is up |
| `input_select.stairs_s3_mode` | dropdown | Sweep · All · Rainbow · Matrix · Disco |

**Danger is deliberately not in the dropdown.** It is not a mode you choose; it
is something that happens to the stairs for five seconds and then undoes itself.

## The three automations

### 1 · PIR trigger (`automation-pir-trigger.yaml`)

Bottom or top PIR → select `zz Trigger Bottom` or `zz Trigger Top`, which is the
same as somebody pressing that button.

- Only in **Sweep, All or Rainbow**. Matrix and Disco run continuously and ignore
  triggers, so there is nothing to start.
- A top PIR while the alarm is `armed_home` is skipped here and handled by the
  Danger automation instead.
- **Mode: `queued`, max 4.** Two people on the stairs produce overlapping
  triggers, and the firmware is happy to be re-triggered (patch P5); dropping
  them would lose a trigger, and `restart` would cut one short.

### 2 · Danger (`automation-danger.yaml`)

Top PIR while the alarm is `armed_home` and the stairs are active → **Stairs
Danger** (everything red), wait 5 s, then re-run automation 3 to put the previous
mode back.

- Visual only. No notification, by design.
- It overrides Matrix and Disco, and it still obeys Power, the time window and
  the motion toggle.
- **Mode: `single`, `max_exceeded: silent`.** Somebody repeatedly tripping the
  sensor shouldn't stack five-second flashes or fill the log.
- Restoring the previous mode is `automation.trigger` on automation 3 with
  `skip_condition: true`, so there is exactly **one** place in the whole system
  that knows how to work out the right preset.

### 3 · Apply state (`automation-apply-state.yaml`)

The only automation that decides a preset from scratch. It runs when Power, Moon,
the mode, the motion toggle or day/night change, when Home Assistant starts, and
when the controller comes back from `unavailable`.

| Situation | Result |
|---|---|
| Power off | Stairs Off, and the mode dropdown reset to Sweep |
| Not active (daylight without Moon, or motion off) | Stairs Off |
| Active | `Stairs {{ the mode }}` — Sweep, All, Rainbow, Matrix or Disco |

- **Mode: `restart`.** Flipping three toggles quickly should settle on the last
  answer, not queue up four preset changes.
- The preset name is built from the dropdown option (`Stairs {{ states(...) }}`),
  which is why the presets are named *Stairs Sweep*, *Stairs All* and so on:
  one template instead of a five-way choose.
- The `from: unavailable` trigger is what re-applies everything after a power cut
  at the controller — it boots into Sweep on its own, then Home Assistant puts
  the real mode back.

## The cards

Two versions of the same four controls — Power, Moon, Top, Bottom and the mode
dropdown.

| File | Needs | Looks like |
|---|---|---|
| `dashboard-bubble-card.yaml` | Bubble Card v3.x from HACS | One card: name row with Moon and Power buttons, and a bottom row of Top / Bottom / mode |
| `dashboard-built-in-cards.yaml` | nothing | Five plain cards: two tiles, two buttons and a tile with the select feature |

The Top and Bottom buttons call `select.select_option` on the WLED preset select
directly, so they work even if the automations are disabled.

## What I changed

1. **Nothing sends colours or effects.** Early versions pushed segment JSON from
   Home Assistant and raced the firmware. Now Home Assistant only ever picks a
   preset name ([why](../../shared/README.md#presets-are-the-interface)).
2. **One decision point.** Danger doesn't try to remember what was on before; it
   re-triggers automation 3, which recalculates. Fewer states to get out of step.
3. **Mode resets to Sweep when Power goes off**, so the stairs never come back
   from a day of being off in Disco.

## Add just this part

1. **Name the controller first**, in WLED → Config → User Interface. Home
   Assistant builds entity IDs from the name when it discovers the device and
   will not change them later.
2. Settings → Devices & services → the **WLED** integration will have found it;
   add it. Nothing here needs the light entities — the automations and cards only
   ever touch the preset select — but if you plan to control the strip as a light
   as well, turn on **Keep main light** in the integration's options: with the
   single-segment presets (All, Matrix, Disco, Danger, Off) the main light entity
   can otherwise go unavailable.
3. Create the three helpers from `helpers.yaml` (Settings → Devices & services →
   Helpers, or paste the YAML into `configuration.yaml`).
4. For each of the three automations: Settings → Automations → **Create new** →
   ⋮ → **Edit in YAML**, paste the file, then fix every `# CHANGE:` line to point
   at your own entities.
5. Add one of the two cards to a dashboard. Start it in a scratch view, as I did,
   before putting it on a real page.
6. Check it: flip Power off and on, change the mode, and watch
   `select.<device>_preset` follow. The stairs themselves shouldn't light at all
   while you do that — the preset only sets the stage.

If you don't have PIRs, skip automations 1 and 2 and keep automation 3: you still
get the mode dropdown, the day/night rule and the dashboard buttons.

---

[← Part 6 · The nine presets](../06-presets/README.md) · [All parts](../../README.md#the-parts) · [Part 8 · Testing →](../08-testing/README.md)
