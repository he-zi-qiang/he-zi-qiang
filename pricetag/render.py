"""Render Claude usage as a tri-color (BWR) price-tag image for Nebular 4.2"."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from PIL import Image, ImageDraw, ImageFont

from usage import Block, Usage, chinese_date

# Tri-color palette. Order matters: index 0 = white, 1 = black, 2 = red.
PALETTE_RGB = [
    (255, 255, 255),
    (0, 0, 0),
    (220, 30, 30),
]
WHITE, BLACK, RED = PALETTE_RGB


@dataclass
class Theme:
    width: int = 400
    height: int = 300
    title: str = "Claude Max"
    footer: str = "powered by 何梓强"
    serial: str = "42000E43"
    cjk_font: str = "/System/Library/Fonts/PingFang.ttc"
    mono_font: str = "/System/Library/Fonts/Menlo.ttc"
    mascot_path: str = ""  # optional PNG to drop in the top-left


def _load_font(path: str, size: int, fallbacks: Sequence[str] = ()) -> ImageFont.FreeTypeFont:
    for candidate in (path, *fallbacks):
        if candidate and os.path.exists(candidate):
            try:
                return ImageFont.truetype(candidate, size)
            except OSError:
                continue
    return ImageFont.load_default(size)


def render(usage: Usage, theme: Theme) -> Image.Image:
    """Render to RGB; downstream converts to the BW + Red channels the panel expects."""
    W, H = theme.width, theme.height
    img = Image.new("RGB", (W, H), WHITE)
    d = ImageDraw.Draw(img)

    cjk_fallbacks = (
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    )
    mono_fallbacks = (
        "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
    )

    f_title = _load_font(theme.cjk_font, 30, cjk_fallbacks)
    f_date = _load_font(theme.cjk_font, 18, cjk_fallbacks)
    f_label = _load_font(theme.mono_font, 14, mono_fallbacks)
    f_pct = _load_font(theme.mono_font, 22, mono_fallbacks)
    f_footer = _load_font(theme.cjk_font, 10, cjk_fallbacks)

    # Mascot top-left (image asset or fallback sparkle).
    _draw_mascot(img, x=8, y=4, size=48, mascot_path=theme.mascot_path)

    # Title — red, like the example.
    _center_text(d, theme.title, W // 2, 6, f_title, fill=RED)

    # Date below title
    _center_text(d, chinese_date(usage.timestamp), W // 2, 44, f_date, fill=BLACK)

    # Separator under date
    d.line([(10, 72), (W - 10, 72)], fill=BLACK, width=1)

    # Three usage blocks
    y = 82
    row_h = (H - y - 40) // 3
    for block in usage.blocks:
        _draw_block(d, block, x=12, y=y, w=W - 24, h=row_h, f_label=f_label, f_pct=f_pct)
        y += row_h

    # Footer separator
    d.line([(10, H - 38), (W - 10, H - 38)], fill=BLACK, width=1)
    _center_text(d, theme.footer, W // 2, H - 34, f_footer, fill=BLACK)

    # Pseudo-barcode + serial
    _draw_barcode(d, x=8, y=H - 18, w=160, h=14, serial=theme.serial)
    d.text((176, H - 16), theme.serial, fill=BLACK, font=f_footer)

    return img


def _draw_block(
    d: ImageDraw.ImageDraw,
    block: Block,
    *,
    x: int,
    y: int,
    w: int,
    h: int,
    f_label: ImageFont.FreeTypeFont,
    f_pct: ImageFont.FreeTypeFont,
) -> None:
    label = f"{block.label} · {block.sub}"
    d.text((x, y), label, fill=BLACK, font=f_label)
    reset_w = d.textlength(block.resets, font=f_label)
    d.text((x + w - reset_w, y), block.resets, fill=BLACK, font=f_label)

    bar_y = y + 22
    bar_h = 14
    bar_w = w - 70
    d.rectangle([(x, bar_y), (x + bar_w, bar_y + bar_h)], outline=BLACK, width=1)
    pct = max(0.0, min(100.0, block.percent))
    fill_w = int((bar_w - 2) * pct / 100)
    if fill_w > 0:
        # Fill in red when over 80%, otherwise black. Visual signal for "watch out".
        fill_color = RED if pct >= 80 else BLACK
        d.rectangle(
            [(x + 1, bar_y + 1), (x + 1 + fill_w, bar_y + bar_h - 1)],
            fill=fill_color,
        )

    pct_str = f"{int(round(pct))}%"
    pct_color = RED if pct >= 80 else BLACK
    pct_w = d.textlength(pct_str, font=f_pct)
    d.text((x + w - pct_w, bar_y - 4), pct_str, fill=pct_color, font=f_pct)


def _center_text(d: ImageDraw.ImageDraw, text: str, cx: int, y: int, font, *, fill=BLACK) -> None:
    tw = d.textlength(text, font=font)
    d.text((cx - tw / 2, y), text, fill=fill, font=font)


def _draw_barcode(d: ImageDraw.ImageDraw, *, x: int, y: int, w: int, h: int, serial: str) -> None:
    seed = sum(ord(c) for c in serial)
    bars = [1 + ((seed * (i + 1)) % 4) for i in range(40)]
    total = sum(bars) + len(bars)
    cur = x
    scale = w / total
    for i, bw in enumerate(bars):
        bw_px = max(1, int(bw * scale))
        if i % 2 == 0:
            d.rectangle([(cur, y), (cur + bw_px, y + h)], fill=BLACK)
        cur += bw_px + max(1, int(scale))
        if cur > x + w:
            break


def _draw_mascot(img: Image.Image, *, x: int, y: int, size: int, mascot_path: str) -> None:
    """If a mascot PNG exists, paste it; otherwise draw a Claude-style sparkle."""
    if mascot_path and Path(mascot_path).exists():
        m = Image.open(mascot_path).convert("RGBA")
        m.thumbnail((size, size), Image.Resampling.LANCZOS)
        img.paste(m, (x, y), m)
        return
    _draw_sparkle(img, cx=x + size // 2, cy=y + size // 2, r=size // 2 - 2)


def _draw_sparkle(img: Image.Image, *, cx: int, cy: int, r: int) -> None:
    """8-petal Anthropic-style sparkle in red. Placeholder until a real asset is dropped in."""
    d = ImageDraw.Draw(img)
    waist = max(3, r // 4)
    short = int(r * 0.55)
    # Four long cardinal petals
    long_petals = [
        [(cx, cy - r), (cx + waist, cy), (cx, cy + r), (cx - waist, cy)],
        [(cx - r, cy), (cx, cy - waist), (cx + r, cy), (cx, cy + waist)],
    ]
    for poly in long_petals:
        d.polygon(poly, fill=RED)
    # Four short diagonal petals
    diag_offset = int(short * 0.7)
    diag_waist = max(2, waist // 2)
    for dx, dy in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
        tip = (cx + dx * diag_offset, cy + dy * diag_offset)
        # Build a small diamond around the diagonal axis
        # Perpendicular direction (-dy, dx)
        perp = (-dy * diag_waist, dx * diag_waist)
        d.polygon(
            [
                (cx, cy),
                (cx + perp[0], cy + perp[1]),
                tip,
                (cx - perp[0], cy - perp[1]),
            ],
            fill=RED,
        )


def split_bw_red(img: Image.Image) -> tuple[Image.Image, Image.Image]:
    """Split a tri-color RGB render into two 1-bit panels: BW and Red.

    Tri-color e-paper firmware (incl. atc1441's BWR build) needs two buffers:
      - BW channel: 1 where the pixel should be black, 0 elsewhere.
      - R  channel: 1 where the pixel should be red,   0 elsewhere.
    White pixels are 0 in both.
    """
    if img.mode != "RGB":
        img = img.convert("RGB")
    w, h = img.size
    bw = Image.new("1", (w, h), 0)
    red = Image.new("1", (w, h), 0)
    px = img.load()
    bw_px = bw.load()
    red_px = red.load()
    for j in range(h):
        for i in range(w):
            r, g, b = px[i, j]
            # Classify by which palette entry is closest.
            if r > 180 and g < 100 and b < 100:
                red_px[i, j] = 1
            elif r + g + b < 384:  # darker half -> black
                bw_px[i, j] = 1
    return bw, red
