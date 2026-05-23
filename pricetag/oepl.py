"""Push images to a tag via the OpenEPaperLink AP HTTP API.

Architecture:
    PC ── HTTP POST /imgupload ──> ESP32-S3 (OEPL AP) ── BLE ──> Tag

The AP exposes a multipart endpoint at `/imgupload`. We POST the BWR image
(or just the RGB preview — the AP dithers if needed) and the tag's MAC.

Wiki: https://github.com/OpenEPaperLink/OpenEPaperLink/wiki/Image-upload
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import TYPE_CHECKING

import urllib.request

if TYPE_CHECKING:
    from PIL.Image import Image


class OEPLError(RuntimeError):
    pass


def push(img: "Image", *, ap_url: str, mac: str, dither: bool = False) -> None:
    """Upload a PIL image to a tag via the OEPL AP.

    - ap_url:  Base URL of the AP, e.g. "http://192.168.1.42"
    - mac:     Tag MAC, e.g. "00000197E5CB3B38" (no separators)
    - dither:  True for photos/grayscale, False for crisp text/UI.
    """
    if not ap_url:
        raise OEPLError("ap_url is empty. Set [oepl].ap_url in config.toml.")
    if not mac:
        raise OEPLError("mac is empty. Set [oepl].tag_mac in config.toml.")

    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=92)
    payload = buf.getvalue()

    boundary = "----PriceTagBoundary"
    parts: list[bytes] = []
    parts.append(_form_field(boundary, "mac", mac))
    parts.append(_form_field(boundary, "dither", "1" if dither else "0"))
    parts.append(_form_file(boundary, "file", "tag.jpg", "image/jpeg", payload))
    parts.append(f"--{boundary}--\r\n".encode())
    body = b"".join(parts)

    url = ap_url.rstrip("/") + "/imgupload"
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Content-Length": str(len(body)),
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            if resp.status != 200:
                raise OEPLError(f"AP returned HTTP {resp.status}: {resp.read()[:200]!r}")
    except urllib.error.URLError as e:
        raise OEPLError(f"Could not reach AP at {url}: {e}") from e


def _form_field(boundary: str, name: str, value: str) -> bytes:
    return (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
        f"{value}\r\n"
    ).encode()


def _form_file(boundary: str, name: str, filename: str, content_type: str, content: bytes) -> bytes:
    head = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'
        f"Content-Type: {content_type}\r\n\r\n"
    ).encode()
    return head + content + b"\r\n"
