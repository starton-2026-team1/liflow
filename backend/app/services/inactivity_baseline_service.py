import math
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.sensor_event_repository import list_person_sensor_events_between

LOOKBACK_DAYS = 14
DAYTIME_START_HOUR = 6
DAYTIME_END_HOUR = 22
MIN_INTERVAL_COUNT = 20
FALLBACK_THRESHOLD_MINUTES = 6 * 60
MIN_THRESHOLD_MINUTES = 60
MAX_THRESHOLD_MINUTES = 12 * 60
THRESHOLD_BUFFER_MINUTES = 30


@dataclass(frozen=True)
class InactivityBaseline:
    average_interval_minutes: int | None
    percentile_95_minutes: int | None
    threshold_minutes: int
    interval_count: int
    is_personalized: bool


def calculate_inactivity_baseline(
    event_times: list[datetime], configured_threshold_minutes: int
) -> InactivityBaseline:
    daytime_times = sorted(
        event_time
        for event_time in event_times
        if DAYTIME_START_HOUR <= event_time.hour < DAYTIME_END_HOUR
    )
    intervals = [
        round((current - previous).total_seconds() / 60)
        for previous, current in zip(daytime_times, daytime_times[1:], strict=False)
        if previous.date() == current.date() and current > previous
    ]
    if len(intervals) < MIN_INTERVAL_COUNT:
        return InactivityBaseline(
            average_interval_minutes=None,
            percentile_95_minutes=None,
            threshold_minutes=max(
                configured_threshold_minutes, FALLBACK_THRESHOLD_MINUTES
            ),
            interval_count=len(intervals),
            is_personalized=False,
        )

    intervals.sort()
    percentile_index = math.ceil(len(intervals) * 0.95) - 1
    percentile_95 = intervals[percentile_index]
    threshold = max(
        configured_threshold_minutes,
        MIN_THRESHOLD_MINUTES,
        percentile_95 + THRESHOLD_BUFFER_MINUTES,
    )
    return InactivityBaseline(
        average_interval_minutes=round(sum(intervals) / len(intervals)),
        percentile_95_minutes=percentile_95,
        threshold_minutes=min(threshold, MAX_THRESHOLD_MINUTES),
        interval_count=len(intervals),
        is_personalized=True,
    )


async def get_inactivity_baseline(
    session: AsyncSession,
    person_id: int,
    configured_threshold_minutes: int,
    now: datetime,
) -> InactivityBaseline:
    events = await list_person_sensor_events_between(
        session, person_id, now - timedelta(days=LOOKBACK_DAYS), now
    )
    return calculate_inactivity_baseline(
        [event.detected_at for event in events], configured_threshold_minutes
    )


def format_duration(minutes: int) -> str:
    hours, remaining_minutes = divmod(max(0, minutes), 60)
    if hours and remaining_minutes:
        return f"{hours}시간 {remaining_minutes}분"
    if hours:
        return f"{hours}시간"
    return f"{remaining_minutes}분"
