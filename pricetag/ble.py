"""BLE push to a Hanshow Nebular tag flashed with atc1441 OEPL firmware.

Status: SKELETON. The exact GATT service/characteristic UUIDs and chunking
protocol come from atc1441's WebBluetooth uploader. We'll fill these in once
the tag is flashed and reachable — the JS source at
https://github.com/atc1441/ATC_TLSR_Paper/blob/main/Tools/Image_Uploader.html
is what we'll port.

Until then, push() raises NotImplementedError and the CLI prints the rendered
PNG path instead.
"""

from __future__ import annotations

import asyncio
import io
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PIL.Image import Image


# Placeholders — replace once verified against the WebFlasher.
SERVICE_UUID = "00001805-0000-1000-8000-00805f9b34fb"  # not real, do not ship
IMAGE_CHAR_UUID = "0000ffff-0000-1000-8000-00805f9b34fb"  # not real, do not ship


def image_to_oepl_payload(img: "Image") -> bytes:
    """Pack a 1-bit PIL image as packed MSB-first bytes (LSB row-major).

    OEPL/atc1441 firmware expects a tight bit-packed buffer. Endianness and
    row-padding need to match the WebFlasher's behavior — port from JS to
    confirm before relying on this.
    """
    if img.mode != "1":
        img = img.convert("1")
    w, h = img.size
    if w % 8 != 0:
        raise ValueError(f"Width must be multiple of 8 for bit packing, got {w}.")
    raw = img.tobytes()  # PIL packs 1-bit MSB-first already
    return raw


async def push(img: "Image", mac: str, *, timeout: float = 30.0) -> None:
    """Connect to the tag over BLE and upload the image. Not yet implemented."""
    raise NotImplementedError(
        "BLE push not wired up yet. Once you flash the tag with atc1441's firmware:\n"
        "  1) Open https://atc1441.github.io/ATC_TLSR_Paper_Image_Upload.html in Chrome\n"
        "  2) Pair to your tag (MAC " + mac + ")\n"
        "  3) Upload the PNG produced by `python main.py --mock --save out.png`\n"
        "Once that works end-to-end, we'll port the JS protocol into this file."
    )


def push_blocking(img: "Image", mac: str) -> None:
    asyncio.run(push(img, mac))
