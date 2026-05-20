"""Read Claude usage data."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal


@dataclass
class Block:
    label: str
    sub: str
    resets: str
    percent: float


@dataclass
class Usage:
    blocks: list[Block]
    timestamp: datetime


WEEKDAY_ZH = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]


def chinese_date(dt: datetime) -> str:
    return f"{WEEKDAY_ZH[dt.weekday()]} · {dt.month}月{dt.day}日"


def _next_5h_reset(now: datetime) -> str:
    # Claude session blocks reset every 5 hours from session start.
    # Without session-start info, fall back to "next round 5h slot".
    hour = ((now.hour // 5) + 1) * 5
    if hour >= 24:
        hour -= 24
    return f"{hour:02d}:00"


def _next_thursday_0700(now: datetime) -> str:
    # Weekly resets on Thu 07:00 (Claude Max default).
    days_ahead = (3 - now.weekday()) % 7
    if days_ahead == 0 and now.hour >= 7:
        days_ahead = 7
    target = now + timedelta(days=days_ahead)
    return f"{['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][target.weekday()]} 07:00"


def mock_usage(now: datetime) -> Usage:
    return Usage(
        blocks=[
            Block("SESSION", "5H", f"resets {_next_5h_reset(now)}", 13.0),
            Block("WEEKLY", "ALL", f"resets {_next_thursday_0700(now)}", 6.0),
            Block("WEEKLY", "SONNET", f"resets {_next_thursday_0700(now)}", 0.0),
        ],
        timestamp=now,
    )


def _try_ccusage_statusline() -> dict | None:
    try:
        result = subprocess.run(
            ["npx", "--yes", "ccusage", "statusline", "--json"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0 or not result.stdout.strip():
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None


def ccusage_usage(now: datetime) -> Usage:
    """Read live usage from ccusage.

    ccusage's JSON schema evolves; we read what's present and fall back to
    sensible defaults for anything missing. Run with --mock first to verify
    layout, then point at real data.
    """
    data = _try_ccusage_statusline()
    if data is None:
        # Caller decides whether to error or fall back to mock.
        raise RuntimeError(
            "ccusage not reachable. Install with `npm i -g ccusage` or pass --mock."
        )

    session_pct = float(_pluck(data, "session.usagePercentage", "block.usagePercentage") or 0)
    weekly_all_pct = float(_pluck(data, "weekly.all.usagePercentage", "weeklyAll") or 0)
    weekly_sonnet_pct = float(_pluck(data, "weekly.sonnet.usagePercentage", "weeklySonnet") or 0)

    session_reset = _pluck(data, "session.resets", "block.resets") or _next_5h_reset(now)
    weekly_reset = _pluck(data, "weekly.all.resets", "weeklyResets") or _next_thursday_0700(now)

    return Usage(
        blocks=[
            Block("SESSION", "5H", f"resets {session_reset}", session_pct),
            Block("WEEKLY", "ALL", f"resets {weekly_reset}", weekly_all_pct),
            Block("WEEKLY", "SONNET", f"resets {weekly_reset}", weekly_sonnet_pct),
        ],
        timestamp=now,
    )


def _pluck(d: dict, *paths: str):
    for path in paths:
        cur = d
        ok = True
        for key in path.split("."):
            if isinstance(cur, dict) and key in cur:
                cur = cur[key]
            else:
                ok = False
                break
        if ok:
            return cur
    return None


def get_usage(source: Literal["ccusage", "mock"], now: datetime | None = None) -> Usage:
    now = now or datetime.now()
    if source == "mock":
        return mock_usage(now)
    return ccusage_usage(now)
