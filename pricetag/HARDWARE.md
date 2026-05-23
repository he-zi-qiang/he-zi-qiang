# Hardware: Nebular-420R-N flashing wiring

This is the **official** wiring per atc1441's UART flasher (see
`docs/wiring_official.jpg` for the source image from
[atc1441/ATC_TLSR_Paper](https://github.com/atc1441/ATC_TLSR_Paper)).

## Tag identification

- Board silkscreen: `HS_Nebular420_v32`
- MCU: **TLSR8258** (Telink, BLE 5.0, supported by atc1441 tools)
- Battery: pouch Li-Po (single cell). **+ tab is fragile — handle carefully.**

## Test points

Manufacturer-labeled 2×3 grid on the bottom-left of the PCB:

```
GND   NRST  TXD
VCC   RXD   SWS
```

For SWire flashing only **4 of these** are used: GND, NRST, SWS, VCC.

## Wiring (USB-TTL → PCB)

```
USB-TTL                     PCB
─────────                   ───────
3V3   ──────────────────→   VCC      (only if battery is disconnected/broken)
TXD   ──────────────────→   SWS      (direct, no resistor)
RXD                         not used
RTS#  ──────────────────→   NRST     (RTS#, NOT DTR)
GND   ──────────────────→   GND
```

No resistor required (the v0.2 flasher is TX-only / "TX-SWS only").

## USB-TTL requirements

- Chip: FT232 / CP2102 (driver auto-installs on Win10/11 and macOS)
- **LEVEL SEL jumper must be on 3V3** — 5V kills the TLSR8258
- RTS# must be exposed (most FT232 boards have it on the auxiliary header)

## Flashing procedure

1. **Move LEVEL SEL jumper to 3V3** (skip = dead chip)
2. **Remove the yellow transit cap** from the main 4-pin header
3. **Solder 4 thin wires** to the PCB test points: GND, NRST, SWS, VCC
4. **Connect** to USB-TTL per the table above (RX stays unconnected)
5. **Plug USB-TTL to PC**, confirm POWER LED + COM port in Device Manager
6. **Open Chrome / Edge** →
   <https://atc1441.github.io/ATC_TLSR_Paper_UART_Flasher.html>
7. Click **Open**, pick the COM port (baud 460800, atime 3 sec defaults are fine)
8. Click **Unlock Flash** — should succeed
9. Click **Select Firmware**, pick the BWR OEPL `.bin`
10. Click **Write to Flash**
11. After "done", click **Soft Reset MCU** — the tag should show a blank panel
12. Disconnect, desolder wires, reassemble

## After flashing

- The tag is now an open BLE device
- BLE MAC is visible in the WebFlasher log OR via a BLE scanner on Mac/PC
- Use <https://atc1441.github.io/ATC_TLSR_Paper_Image_Upload.html> to push images
- Or wire that protocol into `ble.py` for automated server-side pushing

## Battery handling

The user's tag has a damaged + tab (broke off during disassembly).
Two options after flashing:

1. **Resolder + tab to PCB pad** — quick touch of iron (max 2 sec) on the foil tab
2. **External power only** — wire VCC/GND to a 3.3V supply (e.g. USB module),
   skip the battery entirely. Better for high-refresh use cases like this
   (Claude usage doesn't fit a tag's days-between-updates power budget).
