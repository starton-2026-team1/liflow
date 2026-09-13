from hashlib import sha256

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.push_subscription import PushSubscription


def endpoint_digest(endpoint: str) -> str:
    return sha256(endpoint.encode("utf-8")).hexdigest()


async def save_push_subscription(
    session: AsyncSession, *, user_id: int, endpoint: str, p256dh: str, auth: str
) -> PushSubscription:
    digest = endpoint_digest(endpoint)
    subscription = await session.scalar(
        select(PushSubscription).where(PushSubscription.endpoint_hash == digest)
    )
    if subscription is None:
        subscription = PushSubscription(
            user_id=user_id, endpoint_hash=digest, endpoint=endpoint, p256dh=p256dh, auth=auth
        )
        session.add(subscription)
    else:
        subscription.user_id = user_id
        subscription.endpoint = endpoint
        subscription.p256dh = p256dh
        subscription.auth = auth
    await session.flush()
    await session.refresh(subscription)
    return subscription


async def list_push_subscriptions(session: AsyncSession, user_id: int) -> list[PushSubscription]:
    result = await session.scalars(
        select(PushSubscription).where(PushSubscription.user_id == user_id)
    )
    return list(result.all())


async def delete_push_subscription(session: AsyncSession, user_id: int, endpoint: str) -> None:
    await session.execute(
        delete(PushSubscription).where(
            PushSubscription.user_id == user_id,
            PushSubscription.endpoint_hash == endpoint_digest(endpoint),
        )
    )


async def delete_push_subscription_by_id(session: AsyncSession, subscription_id: int) -> None:
    await session.execute(delete(PushSubscription).where(PushSubscription.id == subscription_id))
