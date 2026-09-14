from pydantic import BaseModel, Field, HttpUrl


class PushSubscriptionKeys(BaseModel):
    p256dh: str = Field(min_length=1, max_length=255)
    auth: str = Field(min_length=1, max_length=255)


class PushSubscriptionCreate(BaseModel):
    endpoint: HttpUrl
    keys: PushSubscriptionKeys


class PushSubscriptionDelete(BaseModel):
    endpoint: HttpUrl


class WebPushConfiguration(BaseModel):
    enabled: bool
    public_key: str | None = None
