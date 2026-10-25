[← Part 6 · The ten presets](../06-presets/README.md) · [All parts](../../README.md#the-parts) · [Part 8 · Testing →](../08-testing/README.md)

# Part 7 · Home Assistant

Optional. The stairs work on their own: the buttons are wired to the controller
and it boots into Sweep. Home Assistant adds the PIRs, a day/night rule, a mode
dropdown and the red "Danger" flash — and all it ever does is pick a preset by
name.

## At a glance

| | |
|---|---|
| **Built from** | the [WLED integration](https://www.home-assistant.io/integrations/wled/) (built in), three helpers, three automations, one script, and [Bubble Card](https://github.com/Clooos/Bubble-Card) for the nicer card |
| **Files in this folder** | `helpers.yaml` · `automation-pir-trigger.yaml` · `automation-danger.yaml` · `automation-apply-state.yaml` · `script-software-trigger.yaml` · `dashboard-bubble-card.yaml` · `dashboard-built-in-cards.yaml` |
| **Also needs** | two occupancy sensors (any kind Home Assistant can see), an `alarm_control_panel` for Danger only |
| **Reads** | two PIRs, `sun.sun`, an alarm panel, a house-wide motion toggle |
| **Writes** | `select.<your wled device>_preset` — nothing else |
| **Tested with** | Home Assistant 2026.10.2, Bubble Card v3.4.2 |

Every file is marked up with `# CHANGE:` where an entity ID is mine rather than
yours. Search for `CHANGE`.

## How it works

```
PIR / card button ─┐
                   ├─> a preset name ─> WLED Staircase ─> the stairs
mode / night mode ─┘
```

**These are stair lights for the dark.** In daylight they do nothing at all —
there is no point lighting a staircase you can already see. One rule decides
whether they are live:

> **Active** = the sun is **below the horizon**, or **Night mode** is on.

Two modes sit outside that rule entirely. **Matrix** and **Disco** are the fun
ones: they run from the moment you select them, day or night, and they ignore
every trigger. Pick another mode to stop one.

> **There is no Power toggle.** There used to be, as a master switch. It turned
> out to duplicate the day/night window for the card buttons and the house motion
> toggle for the sensors, while making the card about the installation rather
> than about the staircase. It was removed, along with its helper. The trade:
> with no master off, the only way to stop Matrix or Disco is to pick another
> mode.

- **Night is the sun, not a clock.** The condition reads `sun.sun`, which Home
  Assistant works out from your latitude and longitude, so the stairs follow
  sunset and sunrise through the year with nothing to adjust. Outside those
  hours Home Assistant holds the controller on **Stairs Off**, and the motion
  sensors and card buttons do nothing. The hardware buttons still work, and so
  does Danger.
- **Night mode forces the window open.** It is a manual override of that sun
  condition: switch it on and the stairs behave exactly as if the sun had set —
  on a dark winter afternoon, in a windowless stairwell, or to show somebody how
  it works. It **latches**, staying on until you switch it off, so it is not a
  timer and not a brightness setting. The helper is still called
  `stairs_s3_moon`; only the label on the cards says Night mode.
- The **house motion toggle** (`input_boolean.motion_sensors` here) is my own
  whole-house "ignore the sensors" switch. It gates the **motion sensors only**,
  so it appears in the PIR automation and **nowhere else** — one condition, in
  one file. It is deliberately absent from Apply state, where parking the stairs
  over it would take the selected mode down with it and leave Night mode unable to mean
  "behave as if it were night"; and absent from Danger, because silencing routine
  lighting is not the same as declining to be told somebody is on the stairs.
  Delete that condition if you don't have such a switch.

### The four ways in, gated differently

This is the part worth getting right, and the original build got it wrong.

| Path | What it is for | Gated by |
|---|---|---|
| **The motion sensors** | **How the stairs are actually used.** You walk up or down and they light | The house motion toggle **and** (night **or** Night mode) |
| **Danger** | A warning that somebody is on the stairs while the house is armed | The alarm being **armed home**. **Nothing else at all** |
| **The card's Top / Bottom buttons** | Trying a mode out from your phone | night **or** Night mode |
| **The hardware buttons** (GPIO 4/5) | Proving the controller and the LEDs work, and nothing else | **Nothing.** Not the hour, not the motion toggle, not the alarm, not Home Assistant |

**The motion sensors are the real interface.** Everything else is for setting the
stairs up, testing them, or warning you. The sensors are gated the most heavily
because they are the ones that fire on their own: in daylight a lit staircase is
pointless, and the house motion toggle means "don't let motion switch lights on".

**Danger is above all of it.** The alarm can be armed at four in the afternoon as
easily as at midnight, so a warning that only worked in the evening would not be
a warning. It ignores the sun, it ignores Night mode, and it ignores the house
motion toggle — switching the sensors off is about routine lighting, not about
whether you get told somebody is on the stairs. The armed alarm is its only
condition. A warning with conditions on it is not a warning.

The card's **Top** button fires it too, when the alarm is armed: without that it
could only ever be set off by walking into the top PIR, which makes it
untestable from a phone.

**The hardware buttons are a diagnostic, not a control.** Two buttons on the
controller itself, locked away, used perhaps twice a year. Their one job is to
answer a single question with no dependencies: *are the LEDs and the controller
working?* So the firmware never second-guesses a physical press — not by the
hour, not by the alarm, not by any Home Assistant state, because the point of
them is the morning Home Assistant is down, Zigbee has dropped, or an automation
has gone strange. The one case where a press does nothing is while **Matrix**,
**Disco** or **Danger** is running, because those switch the staircase logic off
— and all three have the LEDs lit anyway, which answers the question on sight.

> ### ⚠️ How this used to work, if you built an earlier version
>
> **Stairs Off** used to set the staircase logic **off**, and a disabled usermod
> ignores *everything* — both hardware buttons, both sensors and the trigger presets
> alike. Since Home Assistant applies Stairs Off whenever the stairs aren't
> active, the hardware buttons were dead for most of the day. It sent me looking for
> a wiring fault that didn't exist, twice.
>
> The flag was never needed. The only inputs physically wired to the usermod are
> the two buttons — the sensors are Zigbee and reach the controller only as
> trigger presets that Home Assistant chooses to send, so the automations already
> gate them. Disabling the logic added no gating and cost the one path that is
> supposed to survive Home Assistant being down.
>
> **Stairs Off now sets the logic `enabled: true`**, so it also repairs the flag
> if Matrix, Disco or Danger left it off. Those three still switch it off while
> they run, which is the one case where a hardware button does nothing.
>
> ### ⚠️ And it has to carry the row layout
>
> Fixing the flag alone leaves a second fault, which took a Danger test to find.
> **All, Matrix, Disco and Danger each collapse the 64 row segments into one
> segment covering the whole matrix**, and that is how the controller stays until
> something rebuilds them. Stairs Off is what Home Assistant parks the stairs on,
> so if it carries no `seg` block the rows are never rebuilt: the next hardware-button
> press lights the whole staircase at once, in the last mode's colour. After a
> Danger that is solid red, on every press, for as long as the stairs stay parked.
>
> So **preset 7 carries the 64 rows** in Sweep's warm white. The trade is that
> parking the stairs drops the All layout: with mode **All** and the stairs
> parked, a hardware button sweeps rather than fading everything together. Reopening
> the window reapplies the mode's own preset, so All is itself again. For a
> fallback whose job is to prove the hardware works, a sweep is the better thing
> to land on.
>
> If you are updating, regenerate preset 7:
> `python3 tools/make_staircase.py --rows 64 --width 8 --ip <ip> --apply`.

## The two helpers

| Entity | Type | Purpose |
|---|---|---|
| `input_boolean.stairs_s3_moon` | toggle | **Night mode** on the cards. Keeps the stairs live when the sun is up |
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

Top PIR while the alarm is `armed_home` → **Stairs Danger** (everything red),
wait 5 s, **zz Danger Off** to fade the red away, then re-run automation 3 to put
the previous mode back.

- Visual only. No notification, by design.
- **It fades, but faster than All: 0.2 s up and 0.5 s down**, because the point of
  it is immediacy. Danger never goes through the usermod, so it can't use the
  firmware's `fade-in-ms`/`fade-out-ms` (patch P7); the times are the two presets'
  own transition times instead — `tt` 2 on Stairs Danger, `tt` 5 on zz Danger Off,
  which is Stairs Off with a fade. Retune them in
  [`tools/make_staircase.py`](../../tools/make_staircase.py)
  (`--danger-in` / `--danger-out`), not here.
- The 5 s hold starts when the fade-in **begins**, so the ramp counts towards the
  five seconds — the same convention patch P7 uses for All. The 600 ms delay after
  the fade-out exists so the fade finishes before automation 3 applies the next
  preset on top of it.
- **The armed alarm is its only condition.** It overrides Matrix and Disco, and
  it deliberately ignores the sun, Night mode and the house motion toggle: an
  alarm armed in the afternoon has to warn you in the afternoon. Switching the
  motion sensors off silences routine lighting, not this. The card's Top button
  reaches it through the script.
- **Recovering the row layout is part of the chain.** Stairs Danger lights the
  matrix as one segment, so the final step — re-running automation 3 — is what
  gets the 64 rows back, by way of the mode's preset or Stairs Off. Leave that
  step in.
- **Mode: `single`, `max_exceeded: silent`.** Somebody repeatedly tripping the
  sensor shouldn't stack five-second flashes or fill the log.
- Restoring the previous mode is `automation.trigger` on automation 3 with
  `skip_condition: true`, so there is exactly **one** place in the whole system
  that knows how to work out the right preset.

### 3 · Apply state (`automation-apply-state.yaml`)

The only automation that decides a preset from scratch. It runs when Night mode,
the mode or day/night change, when Home Assistant starts, and when the controller
comes back from `unavailable`.

| Situation | Result |
|---|---|
| Mode is Matrix or Disco | `Stairs Matrix` / `Stairs Disco` — they run day or night |
| Daylight without Night mode | Stairs Off |
| Otherwise | `Stairs {{ the mode }}` — Sweep, All or Rainbow |

The order matters: the Matrix/Disco branch is tested before the daylight one, so
daylight does not park them.

- **Mode: `restart`.** Flipping two toggles quickly should settle on the last
  answer, not queue up three preset changes.
- The preset name is built from the dropdown option (`Stairs {{ states(...) }}`),
  which is why the presets are named *Stairs Sweep*, *Stairs All* and so on:
  one template instead of a five-way choose.
- The `from: unavailable` trigger is what re-applies everything after a power cut
  at the controller — it boots into Sweep on its own, then Home Assistant puts
  the real mode back.

## The script

### `script-software-trigger.yaml`

The card's **Top** / **Bottom** buttons call this rather than selecting the
trigger preset directly, which is what gives them their own gate: night, or Night
mode. It takes one field, `direction` (`top` or `bottom`).

It deliberately does **not** check the house motion toggle — see
[the four ways in](#the-four-ways-in-gated-differently) above. Without this
script the card buttons would fire in broad daylight, which is the one thing the
day/night rule is there to prevent.

**Its first step hands Danger the stairs.** If `direction` is `top` and the alarm
is `armed_home`, the script triggers the Danger automation and stops — before the
day/night check, because Danger outranks everything. Without that step Danger
could only ever be set off by the Zigbee top PIR, which makes it impossible to
try from the card and makes the card look broken when you are testing with the
alarm on.

## The cards

Two versions of the same four controls — Night mode, Top, Bottom and the mode
dropdown.

| File | Needs | Looks like |
|---|---|---|
| `dashboard-bubble-card.yaml` | Bubble Card v3.x from HACS | One card: name row with the Night mode button, and a bottom row of Top / Bottom / mode |
| `dashboard-built-in-cards.yaml` | nothing | Four plain cards: a tile, two buttons and a tile with the select feature |

The card is deliberately about the **staircase** and nothing else: no master
switch, no brightness, no colours. Top and Bottom call the script rather than the
preset select, so they carry the same day/night gate wherever you put them.

## What I changed

1. **Nothing sends colours or effects.** Early versions pushed segment JSON from
   Home Assistant and raced the firmware. Now Home Assistant only ever picks a
   preset name ([why](../../shared/README.md#presets-are-the-interface)).
2. **One decision point.** Danger doesn't try to remember what was on before; it
   re-triggers automation 3, which recalculates. Fewer states to get out of step.
3. **The master switch went.** A Power toggle duplicated gates that already
   existed and made the card about the installation rather than the staircase.
4. **The buttons on the controller are a diagnostic**, not a control. The PIRs
   are the interface ([Part 2](../02-wiring/README.md#the-two-buttons-are-a-diagnostic)).

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
3. Create the two helpers from `helpers.yaml` (Settings → Devices & services →
   Helpers, or paste the YAML into `configuration.yaml`).
4. Add the script: Settings → Automations & scenes → Scripts → **Add script** → ⋮ →
   **Edit in YAML**, paste `script-software-trigger.yaml`.
5. For each of the three automations: Settings → Automations → **Create new** →
   ⋮ → **Edit in YAML**, paste the file, then fix every `# CHANGE:` line to point
   at your own entities.
6. Add one of the two cards to a dashboard. Start it in a scratch view, as I did,
   before putting it on a real page.
7. Check it: switch **Night mode** on and off, change the mode, and watch
   `select.<device>_preset` follow. The stairs themselves shouldn't light at all
   while you do that — the preset only sets the stage.

If you don't have PIRs, skip automations 1 and 2 and keep automation 3: you still
get the mode dropdown, the day/night rule and the dashboard buttons.

---

[← Part 6 · The ten presets](../06-presets/README.md) · [All parts](../../README.md#the-parts) · [Part 8 · Testing →](../08-testing/README.md)
