"""Timezone helpers for Pakistan Standard Time (PKT)."""

from datetime import datetime, timedelta, timezone
from typing import Union

PAKISTAN_TZ = timezone(timedelta(hours=5))


def now_pakistan() -> datetime:
    return datetime.now(PAKISTAN_TZ)


def pakistan_date_iso() -> str:
    return now_pakistan().date().isoformat()


def convert_utc_to_pakistan_time(utc_datetime: Union[str, datetime]) -> datetime:
    if isinstance(utc_datetime, str):
        utc_datetime = datetime.fromisoformat(utc_datetime)
    return utc_datetime.astimezone(PAKISTAN_TZ)
