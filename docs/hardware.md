# Hardware

## Parts list

| Qty | Part | Notes |
|---|---|---|
| 1 | **Wemos D1 Mini ESP32** (ESP32-WROOM-32) | 4 MB flash, no PSRAM. Mine has a CH9102X USB chip. Any classic ESP32 dev board works |
| 1 | **WS2812B LED strip** | GRB colour order. I used 15 LEDs per stair on 33 stairs = 495 LEDs |
| 1 | **5 V power supply** for the LEDs | Size it for your LED count (see below) |
| 2 | **Momentary push buttons** | One at the bottom of the stairs, one at the top. PIR sensors can replace them later with no config changes |
| 1 | **330 Ω resistor** | In series with the LED data line, close to the strip |
| 2 | **10 kΩ resistors** | Pull-downs on the two button inputs. **Required** |
| — | Wire, connectors, USB data cable | The USB cable must carry data, not just charge |

## Photo

> 📷 *Build photo coming soon.*
<!-- TODO: add images/build-photo.jpg and replace the line above with: ![Build photo](../images/build-photo.jpg) -->

## Wiring

![Wiring diagram](../images/wiring.svg)

### Step by step

1. **LED power.** Connect the power supply **+5V** to the strip **+5V**, and **GND** to the strip **GND**.
2. **Common ground.** Connect an ESP32 **GND** pin to the power supply **GND**. Without this the LED data signal won't work.
3. **LED data.** Connect ESP32 **GPIO 2** → **330 Ω resistor** → strip **DIN** (data in) on the **bottom** stair. Check the arrows on the strip: data flows away from DIN.
4. **Button power.** Connect ESP32 **3V3** to one leg of **both** buttons.
5. **Top button.** Connect the other leg of the top button to **GPIO 18**. Also connect GPIO 18 to **GND** through a **10 kΩ** resistor.
6. **Bottom button.** Connect the other leg of the bottom button to **GPIO 19**. Also connect GPIO 19 to **GND** through a **10 kΩ** resistor.

### How the buttons work

- Not pressed: the 10 kΩ resistor holds the pin at 0 V (LOW, "not pressed").
- Pressed: the button connects the pin to 3.3 V (HIGH, "pressed").

The firmware enables the ESP32's internal pull-*up* resistors on these pins. Those are weak (about 45 kΩ), so the 10 kΩ pull-downs win and the pin still reads LOW when the button isn't pressed. **Without the pull-downs, both pins read HIGH all the time, so the staircase thinks both buttons are held down and never reacts.**

### If the direction is wrong

If the bottom button lights the stairs from the top, the GPIO 18 and GPIO 19 wires are swapped. Swap them back, or swap the pin numbers in WLED → Config → Usermods.

## Powering the ESP32

On the desk, the ESP32 is powered by USB. On the stairs, you can keep a USB power supply on it, or feed the LED supply's 5 V into the ESP32's **5V** (VBUS) pin. **Don't do both at the same time.** Unplug the 5 V wire before connecting USB to a computer.

## Sizing the power supply

Each WS2812B LED draws up to about 60 mA at full white. In practice:

- **Worst case:** LEDs × 60 mA. For 495 LEDs that's about 30 A.
- **Real use** (warm white, brightness 128 of 255): a fraction of that.

WLED's brightness limiter keeps the current inside what your supply can handle. Set it in **WLED → Config → LED Preferences → Maximum current** to about **85% of your supply's rating** (e.g. 8500 mA for a 10 A supply).

For long runs, also feed power into the far end of the strip (power injection) so the top stairs don't look dimmer or yellow.
