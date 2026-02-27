"""
CaaS API Client for automation tasks
"""
import json
import logging
import requests
import time
from datetime import datetime

from ..config import (
    AUTO_ACCEPT_CONFIG,
    AVAILABLE_TASKS_URL,
    CREDENTIALS,
    DEFAULT_HEADERS,
    SIGNIN_URL,
    START_WORK_URL,
    get_auto_accept_window,
)
from ..utils.timezone_utils import now_pakistan
from .mattermost_client import MattermostClient
from .task_keywords import ANDROID_KEYWORDS, BACKEND_KEYWORDS, FRONTEND_KEYWORDS

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
                
                self.headers['authorization'] = f'Bearer {self.access_token}'
                logger.info("Successfully logged in to CaaS")
                return True
            else:
                logger.error(f"Login failed: {data}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Login error: {str(e)}")
            return False

    def accept_task(self, task_id):
        """Accept a task by its ID"""
        if not self.access_token:
            logger.error("Not authenticated. Please login first")
            return False

        try:
            logger.info(f"Attempting to accept task {task_id}...")
            
            payload = {
                "workId": task_id,
                "startTimeEpochMs": int(time.time() * 1000),
                "tzName": "Asia/Karachi"
            }
            
            response = requests.post(
                START_WORK_URL,
                headers=self.headers,
                data=json.dumps(payload)
            )
            response.raise_for_status()
            
            data = response.json()
            if data.get('status') == 'ok':
                logger.info(f"Successfully accepted task {task_id}")
                work_token = data.get('data', {}).get('workToken')
                if work_token:
                    logger.info("Received work token for task")
                return True
            else:
                logger.error(f"Failed to accept task: {data}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error accepting task: {str(e)}")
            return False

    def is_react_native_or_mobile_task(self, work):
        """Check if task is related to React Native, Android, or mobile development based on skills only"""
        skills = [skill.lower() for skill in work.get('skills', [])]

        return any(keyword.lower() in skills for keyword in ANDROID_KEYWORDS)

    def should_auto_accept(self, work):
        """Check if a task should be auto-accepted based on time, day of week, and skills only"""
        current_datetime = now_pakistan()
        current_weekday = current_datetime.weekday()
        if current_weekday not in AUTO_ACCEPT_CONFIG["enabled_days"]:
            logger.info(f"Auto-accept disabled for weekday={current_weekday} via configuration")
            return False

        current_time = current_datetime.time()
        start_time, end_time = get_auto_accept_window(current_weekday)

        if not (start_time <= current_time <= end_time):
            logger.info(
                "Outside auto-accept time window. Current time: %s, window: %s-%s",
                current_time,
                start_time,
                end_time,
            )
            return False

        if self.is_react_native_or_mobile_task(work):
            logger.info("Task rejected: Contains React Native or mobile development keywords in skills")
            return False

        skills = [skill.lower() for skill in work.get('skills', [])]

        has_frontend = any(keyword.lower() in skills for keyword in FRONTEND_KEYWORDS)
        has_backend = any(keyword.lower() in skills for keyword in BACKEND_KEYWORDS)

        if has_frontend or has_backend:
            logger.info("Task matches auto-accept criteria (frontend or backend keywords found in skills)")
            return True

        logger.info("Task does not match auto-accept criteria")
        return False

    def get_available_tasks_and_send_notification(self):
        """Get available tasks from CaaS and send notification"""
        if not self.access_token:
            logger.error("Not authenticated. Please login first")
            return None

        try:
            logger.info("Fetching available tasks...")
            response = requests.get(AVAILABLE_TASKS_URL, headers=self.headers)
            
            data = response.json()
            if data.get('status') == 'ok':
                logger.info("Successfully retrieved available tasks")
                
                work = data.get("data", {}).get("work")
                if work:
                    task_id = work.get('id')
                    
                    last_task_id = self.mattermost.get_last_task_id()
                    is_already_accepted = self.mattermost.get_accepted_task_status()
                    was_cancelled = self.mattermost.get_cancelled_task_status()

                    if last_task_id == task_id and is_already_accepted:
                        logger.info(f"Task {task_id} was previously accepted but now available again - marking as cancelled")
                        self.mattermost.mark_task_as_cancelled(task_id)
                        return data

                    if last_task_id == task_id and was_cancelled:
                        logger.info(f"Task {task_id} was manually cancelled, will not auto-accept again")
                        return data

                    if self.mattermost.has_task_been_notified(task_id):
                        logger.info(f"Task {task_id} already notified, skipping")
                        return data

                    # Check if task qualifies for auto-accept BEFORE sending notification
                    will_auto_accept = self.should_auto_accept(work)
                    
                    if will_auto_accept:
                        logger.info(f"Task {task_id} qualifies for auto-acceptance - sending accepted notification")
                        self.mattermost.send_task_accepted_notification(data)
                        
                        if self.accept_task(task_id):
                            logger.info(f"Successfully accepted task {task_id}")
                        else:
                            logger.error("Failed to auto-accept task")
                    else:
                        logger.info(f"Sending notification for task {task_id} - manual acceptance required")
                        self.mattermost.send_task_notification(data)
                    
                    return data
                
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