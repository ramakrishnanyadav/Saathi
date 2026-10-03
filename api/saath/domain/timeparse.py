"""Relative date and time resolution with timezone awareness and injected clock."""

from __future__ import annotations

from datetime import datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo

# Configurable default hours for times of day (in house local time)
DEFAULT_HOURS = {
    "morning": time(9, 0),  # subah: 09:00
    "subah": time(9, 0),
    "afternoon": time(14, 0),  # dopahar: 14:00
    "dopahar": time(14, 0),
    "evening": time(18, 0),  # shaam: 18:00
    "shaam": time(18, 0),
    "night": time(21, 0),  # raat: 21:00
    "raat": time(21, 0),
    "default": time(18, 0),  # default to 18:00 if unspecified
}

WEEKDAYS = {
    "monday": 0,
    "somwar": 0,
    "tuesday": 1,
    "mangalwar": 1,
    "wednesday": 2,
    "budhwar": 2,
    "thursday": 3,
    "guruwar": 3,
    "brihaspatiwar": 3,
    "friday": 4,
    "shukrawar": 4,
    "saturday": 5,
    "shaniwar": 5,
    "sunday": 6,
    "ravivar": 6,
}


def resolve_symbolic_time(
    spec: dict[str, Any] | str,
    base_time_ms: int,
    house_tz_str: str = "Asia/Kolkata",
) -> int:
    """
    Resolves symbolic time expressions into a UTC epoch millisecond timestamp.

    Arguments:
        spec: dictionary from parser (e.g. {"rel": "tomorrow", "time_of_day": "evening"})
              or a symbolic string ("kal", "parso", "today", "shaam", etc.)
        base_time_ms: the base time (usually message occurred_at or clock.now_ms()) in UTC ms.
        house_tz_str: IANA timezone string for the household.

    Returns:
        UTC epoch millisecond integer.
    """
    if not spec:
        return None

    try:
        tz = ZoneInfo(house_tz_str)
    except Exception:
        tz = ZoneInfo("Asia/Kolkata")

    base_dt = datetime.fromtimestamp(base_time_ms / 1000.0, tz=tz)

    rel_term = ""
    time_of_day = "default"
    explicit_hour = None
    explicit_minute = None
    days_offset = 0

    if isinstance(spec, str):
        cleaned = spec.lower().strip()
        # Check compound phrases like "kal shaam", "parso subah"
        parts = cleaned.split()
        if len(parts) == 1:
            rel_term = parts[0]
        elif len(parts) >= 2:
            rel_term = parts[0]
            time_of_day = parts[1]
    elif isinstance(spec, dict):
        rel_term = str(spec.get("rel", "")).lower().strip()
        time_of_day = str(spec.get("time_of_day", "default")).lower().strip()
        explicit_hour = spec.get("hour")
        explicit_minute = spec.get("minute")
        if "days_offset" in spec:
            days_offset = int(spec["days_offset"])

    # Resolve days offset
    if rel_term in ("today", "aaj"):
        days_offset = 0
    elif rel_term in ("tomorrow", "kal"):
        days_offset = 1
    elif rel_term in ("day_after_tomorrow", "parso"):
        days_offset = 2
    elif rel_term in ("narso", "in_3_days"):
        days_offset = 3
    elif rel_term in WEEKDAYS:
        target_wd = WEEKDAYS[rel_term]
        current_wd = base_dt.weekday()
        # Find next occurrence (if today is target weekday and evening, next week)
        diff = (target_wd - current_wd) % 7
        if diff == 0:
            diff = 7
        days_offset = diff
    elif rel_term.startswith("+") and rel_term.endswith("d"):
        try:
            days_offset = int(rel_term[1:-1])
        except ValueError:
            days_offset = 1
    elif (
        not rel_term
        and days_offset == 0
        and time_of_day in DEFAULT_HOURS
        and time_of_day != "default"
    ):
        # If only time of day specified without relative day, e.g. "shaam"
        # If specified time already passed today, assume tomorrow
        target_t = DEFAULT_HOURS[time_of_day]
        days_offset = 1 if base_dt.time() > target_t else 0

    target_date = base_dt.date() + timedelta(days=days_offset)

    # Resolve target time
    if explicit_hour is not None:
        target_time = time(int(explicit_hour), int(explicit_minute or 0))
    elif time_of_day in DEFAULT_HOURS:
        target_time = DEFAULT_HOURS[time_of_day]
    else:
        target_time = DEFAULT_HOURS["default"]

    local_resolved_dt = datetime.combine(target_date, target_time, tzinfo=tz)
    return int(local_resolved_dt.timestamp() * 1000)
