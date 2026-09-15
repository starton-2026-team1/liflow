from datetime import datetime, timedelta

from app.services.inactivity_baseline_service import (
    FALLBACK_THRESHOLD_MINUTES,
    calculate_inactivity_baseline,
    format_duration,
)


def test_calculates_personalized_threshold_from_two_week_history() -> None:
    start = datetime(2026, 9, 1, 6)
    event_times = []
    for day in range(14):
        day_start = start + timedelta(days=day)
        event_times.extend(day_start + timedelta(minutes=75 * index) for index in range(8))

    baseline = calculate_inactivity_baseline(event_times, 30)

    assert baseline.is_personalized is True
    assert baseline.average_interval_minutes == 75
    assert baseline.percentile_95_minutes == 75
    assert baseline.threshold_minutes == 105
    assert baseline.interval_count == 98


def test_ignores_overnight_intervals() -> None:
    event_times = []
    for day in range(14):
        date = datetime(2026, 9, 1) + timedelta(days=day)
        event_times.extend(
            [
                date.replace(hour=21),
                date.replace(hour=21, minute=20),
                date.replace(hour=21, minute=40),
            ]
        )

    baseline = calculate_inactivity_baseline(event_times, 30)

    assert baseline.is_personalized is True
    assert baseline.average_interval_minutes == 20
    assert baseline.percentile_95_minutes == 20
    assert baseline.threshold_minutes == 60


def test_uses_six_hour_safe_fallback_when_history_is_insufficient() -> None:
    baseline = calculate_inactivity_baseline(
        [datetime(2026, 9, 14, 9), datetime(2026, 9, 14, 10)], 30
    )

    assert baseline.is_personalized is False
    assert baseline.threshold_minutes == FALLBACK_THRESHOLD_MINUTES


def test_formats_korean_duration() -> None:
    assert format_duration(45) == "45분"
    assert format_duration(130) == "2시간 10분"
    assert format_duration(180) == "3시간"
