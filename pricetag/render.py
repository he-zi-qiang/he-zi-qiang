"""Render Claude usage as a 1-bit price-tag image (PIL)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Sequence

from PIL import Image, ImageDraw, ImageFont

from usage import Block, Usage, chinese_date


@dataclass
class Theme:
    width: int = 400
    height: int = 300
    title: str = "Claude Max"
    footer: str = "powered by 何梓强"
    serial: str = "42000E43"
    cjk_font: str = "/System/Library/Fonts/PingFang.ttc"
    mono_font: str = "/System/Library/Fonts/Menlo.ttc"


def _load_font(path: str, size: int, fallbacks: Sequence[str] = ()) -> ImageFont.FreeTypeFont:
    for candidate in (path, *fallbacks):
        if candidate and os.path.exists(candidate):
            try:
                return ImageFont.truetype(candidate, size)
            except OSError:
                continue
    return ImageFont.load_default(size)


def render(usage: Usage, theme: Theme) -> Image.Image:
    W, H = theme.width, theme.height
    # 1-bit: 255 = white, 0 = black. We draw on grayscale then convert at the end.
    img = Image.new("L", (W, H), 255)
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

    # Title — red in the example image, but the panel is BW so just bold black.
    _center_text(d, theme.title, W // 2, 6, f_title)

    # Date
    _center_text(d, chinese_date(usage.timestamp), W // 2, 44, f_date)

    # Separator under date
    d.line([(10, 72), (W - 10, 72)], fill=0, width=1)

    # Three usage blocks
    y = 82
    row_h = (H - y - 40) // 3
    for block in usage.blocks:
        _draw_block(d, block, x=12, y=y, w=W - 24, h=row_h, f_label=f_label, f_pct=f_pct)
        y += row_h

    # Footer separator
    d.line([(10, H - 38), (W - 10, H - 38)], fill=0, width=1)
    _center_text(d, theme.footer, W // 2, H - 34, f_footer)

    # Pseudo-barcode at the bottom-left + serial text
    _draw_barcode(d, x=8, y=H - 18, w=160, h=14, serial=theme.serial)
    d.text((176, H - 16), theme.serial, fill=0, font=f_footer)

    return img.convert("1", dither=Image.Dither.NONE)


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
    d.text((x, y), label, fill=0, font=f_label)
    # Right-aligned reset text
    reset_w = d.textlength(block.resets, font=f_label)
    d.text((x + w - reset_w, y), block.resets, fill=0, font=f_label)

    # Progress bar
    bar_y = y + 22
    bar_h = 14
    bar_w = w - 70
    d.rectangle([(x, bar_y), (x + bar_w, bar_y + bar_h)], outline=0, width=1)
    pct = max(0.0, min(100.0, block.percent))
    fill_w = int((bar_w - 2) * pct / 100)
    if fill_w > 0:
        d.rectangle([(x + 1, bar_y + 1), (x + 1 + fill_w, bar_y + bar_h - 1)], fill=0)

    # Percentage text on the right
    pct_str = f"{int(round(pct))}%"
    pct_w = d.textlength(pct_str, font=f_pct)
    d.text((x + w - pct_w, bar_y - 4), pct_str, fill=0, font=f_pct)


def _center_text(d: ImageDraw.ImageDraw, text: str, cx: int, y: int, font) -> None:
    tw = d.textlength(text, font=font)
    d.text((cx - tw / 2, y), text, fill=0, font=font)


def _draw_barcode(d: ImageDraw.ImageDraw, *, x: int, y: int, w: int, h: int, serial: str) -> None:
    """Deterministic visual barcode from serial (not a real Code128)."""
    seed = sum(ord(c) for c in serial)
    bars = []
    for i in range(40):
        # Pseudo-random widths derived from serial hash.
        bars.append(1 + ((seed * (i + 1)) % 4))
    total = sum(bars) + len(bars)  # +1 per gap
    cur = x
    scale = w / total
    for i, bw in enumerate(bars):
        bw_px = max(1, int(bw * scale))
        if i % 2 == 0:
            d.rectangle([(cur, y), (cur + bw_px, y + h)], fill=0)
        cur += bw_px + max(1, int(scale))
        if cur > x + w:
            break
