"""
CaaS API Client for automation tasks
"""
import json
import logging
import requests
from src.config import SIGNIN_URL, AVAILABLE_TASKS_URL, CREDENTIALS, DEFAULT_HEADERS
from src.clients.mattermost_client import MattermostClient

# Configure logging for CloudWatch
logger = logging.getLogger()

class CaaSClient:
    def __init__(self):
        self.access_token = None
        self.refresh_token = None
        self.user_id = None
        self.headers = DEFAULT_HEADERS.copy()
        self.mattermost = MattermostClient()

    def login(self):
        """Authenticate with CaaS API"""
        try:
            logger.info("Preparing login request...")
            payload = json.dumps(CREDENTIALS)
            response = requests.post(SIGNIN_URL, headers=self.headers, data=payload)
            response.raise_for_status()
            
            data = response.json()
            if data.get('status') == 'ok':
                auth_data = data['data']
                self.access_token = auth_data['accessToken']
                self.refresh_token = auth_data['refreshToken']
                self.user_id = auth_data['userId']
                
                # Update headers with auth token
                self.headers['authorization'] = f'Bearer {self.access_token}'
                logger.info("Successfully logged in to CaaS")
                return True
            else:
                logger.error(f"Login failed: {data}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Login error: {str(e)}")
            return False

    def get_available_tasks_and_send_notification(self):
        """Get available tasks from CaaS and send notification"""
        if not self.access_token:
            logger.error("Not authenticated. Please login first")
            return None

        try:
            logger.info("Fetching available tasks...")
            response = requests.get(AVAILABLE_TASKS_URL, headers=self.headers)
            #response.raise_for_status()
            
            data = response.json()
            #print(data)
            if data.get('status') == 'ok':
                logger.info("Successfully retrieved available tasks")
                # Send notification to Mattermost
                self.mattermost.send_task_notification(data)
                return data
            elif data.get('status') == 'error':
                self.mattermost.send_task_notification("")
                logger.info(f"[X] No tasks available at the moment")
                return None
            else:
                logger.info(f"Error while fetching tasks: {data}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting tasks: {str(e)}")
            return None 