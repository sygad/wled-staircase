# Home Assistant (optional)

The staircase works fully from the physical buttons. Home Assistant adds:

- a dashboard card showing whether the stairs are lit
- **Bottom** and **Top** buttons that run a sweep from your phone
- an **effect dropdown**: Sweep, Rainbow or All

---

## Requirements

| | Needed? | Notes |
|---|---|---|
| **WLED integration** | **Required** | Built into Home Assistant. Everything on this page depends on it |
| **Bubble Card** | Optional | A custom card from HACS. Built on v3.4.1. Without it, use the built-in card version |
| **HA-MCP** | Required for the Claude Code setup | Lets Claude Code create the helper, automation and dashboard card. Not needed if you set Home Assistant up by hand with the steps below |
| **HACS** | For Bubble Card and HA-MCP | https://hacs.xyz |

---

## Connect Claude Code to Home Assistant (HA-MCP)

The [Build Your Own Version](../README.md#build-your-own-version) prompt sets up Home Assistant for you. To do that, Claude Code needs a connection to your Home Assistant through an **MCP server**. I use **[HA-MCP](https://github.com/homeassistant-ai/ha-mcp)**, installed from HACS.

Set this up **before** you paste the prompt. Claude Code only picks up a new MCP server when it starts.

1. **Install it:** **HACS → search "HA-MCP" → Download**, then restart Home Assistant.
2. **Add the integration:** **Settings → Devices & services → Add integration → HA-MCP Server**.
3. **Copy the connect URL:** open the integration's **Configure** screen and copy the URL. No access token is needed.
4. **Add it to Claude Code** (paste your URL):
   ```bash
   claude mcp add --transport http home-assistant <your-connect-URL>
   ```
5. **Check it:** start Claude Code, run `/mcp`, and make sure **home-assistant** shows as connected.

HA-MCP can also run as a Home Assistant add-on, in Docker, or with `uvx`. Its [Setup Wizard](https://github.com/homeassistant-ai/ha-mcp) shows the steps for each. Only add one connection to the same Home Assistant. Two entries for the same server can make the connection hang.

> Without an MCP connection, you can still do everything on this page by hand. Claude Code just can't do it for you.

---

## Step 1: Add the WLED integration

1. Make sure the device has its final name first (see [flash-and-test.md, step 4](flash-and-test.md#step-4-load-the-staircase-settings)).
2. In Home Assistant go to **Settings → Devices & services**. The WLED device usually appears as **Discovered**. Click **Add**.
3. If it doesn't appear: **Add integration → WLED** → enter the device's IP address.
4. Open the integration's **Configure** options and turn on **Keep main light**. Without it the main light entity can disappear when the "All" effect reduces the strip to a single segment.

### Entity names

Home Assistant builds entity IDs from the device name. For a device named **Staircase Lights**:

| Entity | Used for |
|---|---|
| `light.staircase_lights_main` | Master on/off (shown on the dashboard card) |
| `select.staircase_lights_preset` | Picking presets (effects and button triggers) |

The YAML files in `home-assistant/` use `DEVICE` as a placeholder, e.g. `select.DEVICE_preset`. `tools/make_wled_config.py` writes copies with your name filled in to `out/home-assistant/`. To do it by hand, replace `DEVICE` with your name in lower case, with spaces as underscores (e.g. `staircase_lights`).

> **Name the device before Home Assistant discovers it.** The entity IDs are set at discovery. If you rename the device afterwards, the old IDs stay and the automation won't match. To fix that, delete the device from the WLED integration and add it again.

---

## Step 2: Create the effect dropdown helper

File: [`home-assistant/helpers.yaml`](../home-assistant/helpers.yaml)

1. **Settings → Devices & services → Helpers → Create helper → Dropdown**
2. Name: **Staircase Effect**. Icon: `mdi:stairs`
3. Options, in this order: **All**, **Sweep**, **Rainbow**
4. Check the entity ID is `input_select.staircase_effect`

---

## Step 3: Create the automation

File: [`home-assistant/automation.yaml`](../home-assistant/automation.yaml)

1. **Settings → Automations & scenes → Create automation → Create new automation**
2. Three-dot menu → **Edit in YAML**
3. Paste the file contents, with `DEVICE` replaced, and save.

What it does:

| When | It does |
|---|---|
| You pick **All / Sweep / Rainbow** in the dropdown | Sets the WLED preset to Staircase All / Warm / Rainbow |
| WLED changes preset by itself (e.g. back to Sweep after a power cut) | Updates the dropdown to match |

It runs in `queued` mode, so quick changes are applied in order.

---

## Step 4: Add the dashboard card

Pick **one**.

### Option A: Bubble Card

File: [`home-assistant/dashboard-bubble-card.yaml`](../home-assistant/dashboard-bubble-card.yaml)

1. Install Bubble Card: **HACS → search "Bubble Card" → Download**, then reload the browser.
2. Edit your dashboard → **Add card → Manual** → paste the file (with `DEVICE` replaced).

You get one card showing the staircase light, with sub-buttons **Bottom**, **Top** and an **effect dropdown**.

### Option B: Built-in cards only

File: [`home-assistant/dashboard-default.yaml`](../home-assistant/dashboard-default.yaml)

1. Edit your dashboard → **Add card → Manual** → paste the file (with `DEVICE` replaced).

You get the same controls from standard cards: a light tile, **Bottom** and **Top** buttons, and an effect tile with a dropdown.

---

## How the dashboard buttons work

The Bottom and Top buttons select the WLED presets **zz Trigger Bottom** and **zz Trigger Top**. Those presets contain only `{"staircase":{"bottom-sensor":true}}` (or top), which the usermod treats exactly like a physical button press.

You can do the same from anywhere:

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"staircase":{"bottom-sensor":true}}' http://<ip>/json/state
```

These triggers only work while the physical buttons read "not pressed", i.e. with the pull-down resistors fitted.
