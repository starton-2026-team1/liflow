from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.weekly_activity_summary import WeeklyActivitySummary


async def get_weekly_activity_summary(
    session: AsyncSession, person_id: int, period_start: date, period_end: date
) -> WeeklyActivitySummary | None:
    return await session.scalar(
        select(WeeklyActivitySummary).where(
            WeeklyActivitySummary.person_id == person_id,
            WeeklyActivitySummary.period_start == period_start,
            WeeklyActivitySummary.period_end == period_end,
        )
    )


async def save_weekly_activity_summary(
    session: AsyncSession,
    cached: WeeklyActivitySummary | None,
    *,
    person_id: int,
    period_start: date,
    period_end: date,
    event_count: int,
    latest_event_at: datetime,
    summary: str,
    provider: str,
    model: str,
) -> WeeklyActivitySummary:
    if cached is None:
        cached = WeeklyActivitySummary(
            person_id=person_id,
            period_start=period_start,
            period_end=period_end,
            event_count=event_count,
            latest_event_at=latest_event_at,
            summary=summary,
            provider=provider,
            model=model,
        )
        session.add(cached)
    else:
        cached.event_count = event_count
        cached.latest_event_at = latest_event_at
        cached.summary = summary
        cached.provider = provider
        cached.model = model
    await session.flush()
    return cached
