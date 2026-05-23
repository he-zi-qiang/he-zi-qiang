"""Entry point: render Claude usage and (eventually) push it to the tag."""

from __future__ import annotations

import argparse
import sys
import tomllib
from datetime import datetime
from pathlib import Path

from render import Theme, render, split_bw_red
from usage import get_usage


def load_config(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("rb") as f:
        return tomllib.load(f)


def main() -> int:
    parser = argparse.ArgumentParser(description="Drive a Hanshow Nebular price tag with Claude usage.")
    parser.add_argument("--config", type=Path, default=Path(__file__).parent / "config.toml")
    parser.add_argument("--mock", action="store_true", help="Use mock usage data (no ccusage call).")
    parser.add_argument("--save", type=Path, default=Path(__file__).parent / "out" / "tag.png",
                        help="Where to write the rendered PNG.")
    parser.add_argument("--push", action="store_true", help="Push to the tag via the OEPL AP (requires flashed firmware + ESP32 AP).")
    parser.add_argument("--dither", action="store_true", help="Tell the AP to dither the image (better for photos, worse for text).")
    args = parser.parse_args()

    cfg = load_config(args.config)
    if not cfg:
        example = Path(__file__).parent / "config.example.toml"
        print(f"No config.toml found; using defaults. Copy {example.name} -> config.toml to customize.")
        cfg = load_config(example)

    display = cfg.get("display", {})
    fonts = cfg.get("fonts", {})
    theme = Theme(
        width=display.get("width", 400),
        height=display.get("height", 300),
        title=display.get("title", "Claude Max"),
        footer=display.get("footer", "powered by 何梓强"),
        serial=display.get("serial", "42000E43"),
        mascot_path=display.get("mascot_path", ""),
        cjk_font=fonts.get("cjk", Theme.cjk_font),
        mono_font=fonts.get("mono", Theme.mono_font),
    )

    source = "mock" if args.mock else cfg.get("usage", {}).get("source", "ccusage")
    try:
        usage = get_usage(source)
    except RuntimeError as e:
        print(f"[!] {e}", file=sys.stderr)
        return 2

    img = render(usage, theme)

    args.save.parent.mkdir(parents=True, exist_ok=True)
    img.save(args.save)
    print(f"Rendered {img.size[0]}x{img.size[1]} (RGB) -> {args.save}")

    # Also write split BW + Red channels — these are what BWR e-paper firmware needs.
    bw_path = args.save.with_name(args.save.stem + "_bw.png")
    red_path = args.save.with_name(args.save.stem + "_red.png")
    bw, red = split_bw_red(img)
    bw.save(bw_path)
    red.save(red_path)
    print(f"  channels: {bw_path.name}, {red_path.name}")

    if args.push:
        oepl_cfg = cfg.get("oepl", {})
        ap_url = oepl_cfg.get("ap_url", "")
        mac = oepl_cfg.get("tag_mac", "")
        if not ap_url or not mac:
            print("[!] Set [oepl].ap_url and [oepl].tag_mac in config.toml first.", file=sys.stderr)
            return 3
        from oepl import push, OEPLError
        try:
            push(img, ap_url=ap_url, mac=mac, dither=args.dither)
            print(f"Pushed to {mac} via {ap_url}.")
        except OEPLError as e:
            print(f"[!] {e}", file=sys.stderr)
            return 4

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
