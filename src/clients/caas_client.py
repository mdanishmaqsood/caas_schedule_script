"""
CaaS API Client for automation tasks
"""
import json
import logging
import requests
import time
from datetime import datetime, timezone
from src.config import SIGNIN_URL, AVAILABLE_TASKS_URL, START_WORK_URL, CREDENTIALS, DEFAULT_HEADERS
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

    def should_auto_accept(self, work):
        """Check if a task should be auto-accepted based on time and keywords"""
        # Server runs in UTC, so 06:00-12:00 UTC = 11:00-17:00 PKT
        current_time = datetime.now(timezone.utc).time()
        start_time = datetime.strptime("06:00", "%H:%M").time()
        end_time = datetime.strptime("12:00", "%H:%M").time()
        
        if not (start_time <= current_time <= end_time):
            logger.info(f"Outside auto-accept time window. Current time: {current_time}")
            return False
        
        frontend_keywords = ["react", "next", "next.js", "figma", "frontend", "design"]
        backend_keywords = ["django", "python", "fastapi", "backend"]
        
        text_to_check = (
            f"{work.get('title', '')} "
            f"{work.get('description', '')} "
            f"{' '.join(work.get('skills', []))}"
        ).lower()
        
        has_frontend = any(keyword.lower() in text_to_check for keyword in frontend_keywords)
        has_backend = any(keyword.lower() in text_to_check for keyword in backend_keywords)
        
        if has_frontend or has_backend:
            logger.info("Task matches auto-accept criteria (frontend or backend keywords found)")
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
            #response.raise_for_status()
            
            data = response.json()
            #print(data)
            if data.get('status') == 'ok':
                logger.info("Successfully retrieved available tasks")
                
                work = data.get("data", {}).get("work")
                if work:
                    task_id = work.get('id')
                    
                    self.mattermost.log_task_to_history(work)
                    
                    last_task_id = self.mattermost.get_last_task_id()
                    is_already_accepted = self.mattermost.get_accepted_task_status()
                    
                    if last_task_id == task_id and is_already_accepted:
                        logger.info(f"Task {task_id} is already accepted, waiting for completion...")
                        return data
                    
                    if self.should_auto_accept(work):
                        logger.info(f"Task {task_id} qualifies for auto-acceptance")
                        
                        if self.accept_task(task_id):
                            logger.info(f"Successfully accepted task {task_id}, sending notification...")
                            self.mattermost.send_task_accepted_notification(data)
                            return data
                        else:
                            logger.error("Failed to auto-accept task, no notification sent")
                            return data
                    else:
                        logger.info("Task does not qualify for auto-acceptance, no notification sent")
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