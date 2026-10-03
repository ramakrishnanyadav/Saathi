"""Unit tests for domain relative time parser across boundaries and timezones."""

from datetime import datetime
from zoneinfo import ZoneInfo

from saath.domain.timeparse import resolve_symbolic_time


def dt_to_ms(dt: datetime) -> int:
    return int(dt.timestamp() * 1000)


def test_kal_and_parso_in_kolkata():
    """Test 'kal' and 'parso' in Asia/Kolkata timezone."""
    tz = ZoneInfo("Asia/Kolkata")
    base_dt = datetime(2026, 10, 2, 10, 0, 0, tzinfo=tz)  # Friday morning
    base_ms = dt_to_ms(base_dt)

    # Kal default time is 18:00
    kal_ms = resolve_symbolic_time("kal", base_ms, "Asia/Kolkata")
    kal_dt = datetime.fromtimestamp(kal_ms / 1000.0, tz=tz)
    assert kal_dt.year == 2026
    assert kal_dt.month == 10
    assert kal_dt.day == 3
    assert kal_dt.hour == 18
    assert kal_dt.minute == 0

    # Parso subah (morning: 09:00)
    parso_ms = resolve_symbolic_time({"rel": "parso", "time_of_day": "subah"}, base_ms, "Asia/Kolkata")
    parso_dt = datetime.fromtimestamp(parso_ms / 1000.0, tz=tz)
    assert parso_dt.year == 2026
    assert parso_dt.month == 10
    assert parso_dt.day == 4  # Sunday
    assert parso_dt.hour == 9
    assert parso_dt.minute == 0


def test_month_and_year_boundary():
    """Test transitions over month end and year end."""
    tz = ZoneInfo("Asia/Kolkata")
    
    # Month boundary: Oct 31 -> Nov 1
    oct31_dt = datetime(2026, 10, 31, 15, 0, tzinfo=tz)
    res_nov = resolve_symbolic_time("kal", dt_to_ms(oct31_dt), "Asia/Kolkata")
    nov1_dt = datetime.fromtimestamp(res_nov / 1000.0, tz=tz)
    assert nov1_dt.month == 11
    assert nov1_dt.day == 1

    # Year boundary: Dec 31 -> Jan 1
    dec31_dt = datetime(2026, 12, 31, 20, 0, tzinfo=tz)
    res_jan = resolve_symbolic_time("kal", dt_to_ms(dec31_dt), "Asia/Kolkata")
    jan1_dt = datetime.fromtimestamp(res_jan / 1000.0, tz=tz)
    assert jan1_dt.year == 2027
    assert jan1_dt.month == 1
    assert jan1_dt.day == 1


def test_leap_day_boundary():
    """Test leap day boundary in 2024: Feb 28 -> Feb 29 -> March 1."""
    tz = ZoneInfo("Asia/Kolkata")
    feb28_dt = datetime(2024, 2, 28, 12, 0, tzinfo=tz)
    res_feb29 = resolve_symbolic_time("kal", dt_to_ms(feb28_dt), "Asia/Kolkata")
    feb29_dt = datetime.fromtimestamp(res_feb29 / 1000.0, tz=tz)
    assert feb29_dt.year == 2024
    assert feb29_dt.month == 2
    assert feb29_dt.day == 29

    res_mar1 = resolve_symbolic_time("parso", dt_to_ms(feb28_dt), "Asia/Kolkata")
    mar1_dt = datetime.fromtimestamp(res_mar1 / 1000.0, tz=tz)
    assert mar1_dt.year == 2024
    assert mar1_dt.month == 3
    assert mar1_dt.day == 1


def test_weekday_next_occurrence():
    """Test next Monday from a Friday."""
    tz = ZoneInfo("Asia/Kolkata")
    friday_dt = datetime(2026, 10, 2, 10, 0, tzinfo=tz)  # Oct 2, 2026 is Friday
    res_monday = resolve_symbolic_time("monday", dt_to_ms(friday_dt), "Asia/Kolkata")
    monday_dt = datetime.fromtimestamp(res_monday / 1000.0, tz=tz)
    assert monday_dt.weekday() == 0  # Monday
    assert monday_dt.day == 5  # Oct 5
