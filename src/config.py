"""
Configuration settings for CaaS automation
"""
import os
from datetime import datetime

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API URLs
BASE_URL = os.getenv('CAAS_BASE_URL', "https://prod.bh.caas.ai/backend/api/v1")
SIGNIN_URL = f"{BASE_URL}/signin"
AVAILABLE_TASKS_URL = f"{BASE_URL}/work/available"
START_WORK_URL = f"{BASE_URL}/work/start"

# User credentials
CREDENTIALS = {
    "email": os.getenv('CAAS_EMAIL'),
    "password": os.getenv('CAAS_PASSWORD')
}

# Headers
DEFAULT_HEADERS = {
    'content-type': 'application/json',
    'priority': 'u=1, i',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0',
    'origin': 'https://app.caas.ai',
    'referer': 'https://app.caas.ai/'
}

# Mattermost Configuration
MATTERMOST_CONFIG = {
    'webhook_url': os.getenv('MATTERMOST_WEBHOOK_URL'),
}


WEEKDAY_TO_INDEX = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


def _parse_time(value, fallback):
    try:
        return datetime.strptime(value, "%H:%M").time()
    except (TypeError, ValueError):
        return datetime.strptime(fallback, "%H:%M").time()


def _parse_days(value, fallback):
    raw_value = value if value is not None else fallback
    days = set()
    for day_name in [day.strip().lower() for day in raw_value.split(",") if day.strip()]:
        if day_name in WEEKDAY_TO_INDEX:
            days.add(WEEKDAY_TO_INDEX[day_name])
    if days:
        return days
    return {WEEKDAY_TO_INDEX[day.strip().lower()] for day in fallback.split(",") if day.strip().lower() in WEEKDAY_TO_INDEX}


AUTO_ACCEPT_CONFIG = {
    "enabled_days": _parse_days(
        os.getenv("AUTO_ACCEPT_ENABLED_DAYS"),
        "monday,tuesday,wednesday,thursday,friday,saturday,sunday",
    ),
    "extended_days": _parse_days(
        os.getenv("AUTO_ACCEPT_EXTENDED_DAYS"),
        "thursday,friday",
    ),
    "default_start": _parse_time(os.getenv("AUTO_ACCEPT_DEFAULT_START", "07:00"), "07:00"),
    "default_end": _parse_time(os.getenv("AUTO_ACCEPT_DEFAULT_END", "17:00"), "17:00"),
    "extended_start": _parse_time(os.getenv("AUTO_ACCEPT_EXTENDED_START", "06:00"), "06:00"),
    "extended_end": _parse_time(os.getenv("AUTO_ACCEPT_EXTENDED_END", "22:00"), "22:00"),
}


def get_auto_accept_window(weekday):
    if weekday in AUTO_ACCEPT_CONFIG["extended_days"]:
        return AUTO_ACCEPT_CONFIG["extended_start"], AUTO_ACCEPT_CONFIG["extended_end"]
    return AUTO_ACCEPT_CONFIG["default_start"], AUTO_ACCEPT_CONFIG["default_end"]