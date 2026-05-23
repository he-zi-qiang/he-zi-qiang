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

## Firmware: OEPL TLSR (NOT atc1441 ATC_Paper.bin)

atc1441's single `ATC_Paper.bin` is built for 2.13" Stellar tags — flashing it
on a 4.2" BWR Nebular leaves the chip alive but the display driver wrong.

Use OpenEPaperLink's TLSR firmware instead. The build that matches Nebular
420R-N is in OEPL releases — `Tag_*Nebular*4.2*BWR*.bin` or similar (check
the latest release notes; community ports land there).

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
9. Click **Select Firmware**, pick the **OEPL Nebular 420 BWR `.bin`**
10. Click **Write to Flash**
11. After "done", click **Soft Reset MCU** — the tag should show OEPL boot screen
12. Disconnect, desolder wires, reassemble

## ESP32-S3 AP setup

The tag talks BLE to an ESP32-S3 acting as the OEPL access point, which in
turn exposes an HTTP API to your PC.

**Hardware**: ESP32-S3-N16R8 (16MB Flash + 8MB PSRAM). Cheaper variants
without 8MB PSRAM will not support OTA updates.

**Flashing the AP**:

1. Plug ESP32-S3 into Windows USB
2. Chrome → <https://install.openepaperlink.de/>
3. Pick "ESP32-S3 BLE-only" build
4. Connect to COM port, click Install
5. After flash, the ESP32 advertises a WiFi network `OpenEPaperLink`
6. Connect your laptop to it, point browser to `192.168.4.1`, configure your
   home WiFi
7. ESP32 reboots onto your WiFi; check your router for its IP (or it
   advertises mDNS as `openepaperlink.local`)
8. Browse to its IP → OEPL web UI

## Pairing the tag

Power the tag (battery or USB). Within ~30 seconds it shows up in the AP's
web UI under "tags" with its MAC. Copy that MAC into `config.toml`'s
`[oepl].tag_mac`.

## Battery handling

The user's tag has a damaged + tab (broke off during disassembly).
Two options after flashing:

1. **Resolder + tab to PCB pad** — quick touch of iron (max 2 sec) on the foil tab
2. **External power only** — wire VCC/GND to a 3.3V supply (e.g. USB module),
   skip the battery entirely. Better for high-refresh use cases like this
   (Claude usage doesn't fit a tag's days-between-updates power budget).

## Battery handling

The user's tag has a damaged + tab (broke off during disassembly).
Two options after flashing:

1. **Resolder + tab to PCB pad** — quick touch of iron (max 2 sec) on the foil tab
2. **External power only** — wire VCC/GND to a 3.3V supply (e.g. USB module),
   skip the battery entirely. Better for high-refresh use cases like this
   (Claude usage doesn't fit a tag's days-between-updates power budget).
