import datetime as dt
from typing import List, Optional

from pydantic import BaseModel, Field


class ConfigOut(BaseModel):
    uuid: str
    name: str
    status: str
    volume_gb: float
    used_volume_gb: float
    remaining_volume_gb: float
    max_connections: int
    expire_date: dt.datetime
    link: str
    subscription_link: Optional[str] = None
    last_connection_at: Optional[dt.datetime] = None

    class Config:
        from_attributes = True


class UserProfileResponse(BaseModel):
    telegram_id: int
    username: Optional[str]
    first_name: Optional[str]
    created_at: dt.datetime


class UserConfigsResponse(BaseModel):
    configs: List[ConfigOut]


class ConfigCreateRequest(BaseModel):
    name: str = Field(default="My Config", max_length=64)
    volume_gb: float = Field(..., gt=0)
    validity_days: int = Field(...)
    max_connections: int = Field(...)


class ConfigCreateResponse(BaseModel):
    config: ConfigOut


class ConfigRenewRequest(BaseModel):
    config_uuid: str
    add_volume_gb: Optional[float] = Field(default=None, gt=0)
    extend_days: Optional[int] = Field(default=None, gt=0)


class ConfigResetLinkRequest(BaseModel):
    config_uuid: str


class ConfigDeleteRequest(BaseModel):
    config_uuid: str
