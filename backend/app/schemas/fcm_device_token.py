from typing import Literal

from pydantic import BaseModel, Field


class FcmDeviceTokenCreate(BaseModel):
    token: str = Field(min_length=20, max_length=512)
    platform: Literal["android"] = "android"


class FcmDeviceTokenDelete(BaseModel):
    token: str = Field(min_length=20, max_length=512)
