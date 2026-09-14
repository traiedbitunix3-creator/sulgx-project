"""
اعتبارسنجی initData ارسالی از Telegram Web App طبق مستندات رسمی تلگرام:
https://core.telegram.org/bots/webapps#validating-data-received-via-the-web-app
"""
import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Optional
from urllib.parse import parse_qsl


@dataclass
class TelegramAuthData:
    user_id: int
    username: Optional[str]
    first_name: Optional[str]
    auth_date: int
    raw: dict


def verify_telegram_init_data(
    init_data: str, bot_token: str, max_age_seconds: int = 86400
) -> Optional[TelegramAuthData]:
    """
    initData را اعتبارسنجی می‌کند و در صورت معتبر بودن، اطلاعات کاربر را برمی‌گرداند.
    در صورت نامعتبر بودن (هش اشتباه یا منقضی‌شدن)، None برمی‌گرداند.
    """
    if not bot_token:
        return None

    try:
        parsed = dict(parse_qsl(init_data, strict_parsing=True))
    except ValueError:
        return None

    received_hash = parsed.pop("hash", None)
    if not received_hash:
        return None

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))

    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(computed_hash, received_hash):
        return None

    auth_date = int(parsed.get("auth_date", 0))
    if max_age_seconds and (time.time() - auth_date) > max_age_seconds:
        return None

    user_raw = parsed.get("user")
    if not user_raw:
        return None
    user = json.loads(user_raw)

    return TelegramAuthData(
        user_id=user["id"],
        username=user.get("username"),
        first_name=user.get("first_name"),
        auth_date=auth_date,
        raw=parsed,
    )
