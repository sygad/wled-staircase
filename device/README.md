# device

The real controller's own backup files, exactly as WLED's **Backup configuration**
and **Backup presets** buttons produce them. This is the "whole thing in one
place" copy; the numbered parts explain it piece by piece.

| File | What it is | Explained in |
|---|---|---|
| `cfg.json` | Every WLED setting on the live controller | [Part 5 · WLED settings](../parts/05-wled-settings/README.md) |
| `presets.json` | Presets 1–9, byte-for-byte what the controller runs | [Part 6 · The nine presets](../parts/06-presets/README.md) |
| `palette0.json` | The custom palette the Disco preset's GEQ bars use | [Part 6 · The nine presets](../parts/06-presets/README.md) |

Two values are placeholders rather than mine: the Wi-Fi SSID
(`CHANGE-ME-WIFI-SSID`) and the mDNS hostname (`wled-staircase`). Wi-Fi passwords
are never in a WLED backup.

One value is deliberately not what my controller reported when this was taken:
`um.staircase.enabled` is **true** here. The controller said `false`, because it
was daylight and Home Assistant had applied Stairs Off — and shipping that would
hand you a config that boots with the staircase logic disabled and the buttons
dead. Read the warning in [Part 5](../parts/05-wled-settings/README.md): it is
the same trap in a different hat.

`fade-in-ms` and `fade-out-ms` appear here because the controller reports its
live settings, but on my board they are still the firmware's own defaults rather
than saved values — see the warning in
[Part 5](../parts/05-wled-settings/README.md) before saving a config to change
that.

**Don't restore `cfg.json` onto your own board as it is** — the LED count, pins
and power limit are mine. Generate yours instead:

```bash
python3 ../tools/make_staircase.py --rows <your steps> --width <your LEDs per step>
```

`presets.json` *can* be uploaded as it is, if your staircase is also 64 steps of
8 LEDs: Config → Security & Updates → Restore presets.
