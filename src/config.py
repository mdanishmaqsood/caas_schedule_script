"""
Configuration settings for CaaS automation
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API URLs
BASE_URL = os.getenv('CAAS_BASE_URL', "https://prod.bh.caas.ai/backend/api/v1")
SIGNIN_URL = f"{BASE_URL}/signin"
AVAILABLE_TASKS_URL = f"{BASE_URL}/work/available"

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