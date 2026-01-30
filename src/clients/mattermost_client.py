"""
Mattermost client for sending notifications
"""

import json
import logging
import requests
import os
from datetime import datetime
from src.config import MATTERMOST_CONFIG
from .task_history import TaskHistory
from .notification_formatter import format_task_message, format_daily_summary

logger = logging.getLogger()


class MattermostClient:
    def __init__(self):
        self.webhook_url = MATTERMOST_CONFIG["webhook_url"]
        self.last_task_file = "src/data/last_task.json"
        self.daily_summary_file = "src/data/last_summary_date.json"
        self.task_history = TaskHistory()
        self._initialize_json_files()
    
    def _initialize_json_files(self):
        """Create JSON files with default values if they don't exist"""
        try:
            os.makedirs("src/data", exist_ok=True)
            files = {
                self.last_task_file: {"last_task_id": None, "accepted": False},
                self.task_history.history_file: [],
                self.daily_summary_file: {"last_summary_date": None}
            }
            for path, default_data in files.items():
                if not os.path.exists(path):
                    with open(path, "w") as f:
                        json.dump(default_data, f)
                    logger.info(f"Created {path}")
        except Exception as e:
            logger.error(f"Error initializing JSON files: {str(e)}")

    def send_message(self, message, attachments=None):
        """
        Send a message to Mattermost channel

        Args:
            message (str): The message text to send
            attachments (list, optional): List of attachments for rich formatting
        """
        if not self.webhook_url:
            logger.error("Mattermost webhook URL not configured")
            return False

        try:
            logger.info("Preparing Mattermost message...")
            payload = {
                "text": f"{message}",
            }

            if attachments:
                payload["attachments"] = attachments

            response = requests.post(
                self.webhook_url,
                data=json.dumps(payload),
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()

            logger.info("Successfully sent message to Mattermost")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send message to Mattermost: {str(e)}")
            return False

    def get_last_task_id(self):
        """Get the last task ID from the storage file"""
        try:
            if os.path.exists(self.last_task_file):
                with open(self.last_task_file, "r") as f:
                    data = json.load(f)
                    return data.get("last_task_id")
            return None
        except Exception as e:
            logger.error(f"Error reading last task ID: {str(e)}")
            return None

    def save_last_task_id(self, task_id, accepted=False):
        """Save the last task ID to the storage file"""
        try:
            os.makedirs(os.path.dirname(self.last_task_file), exist_ok=True)
            with open(self.last_task_file, "w") as f:
                json.dump({"last_task_id": task_id, "accepted": accepted}, f)
        except Exception as e:
            logger.error(f"Error saving last task ID: {str(e)}")
    
    def get_accepted_task_status(self):
        """Get the accepted status of the last task"""
        try:
            if os.path.exists(self.last_task_file):
                with open(self.last_task_file, "r") as f:
                    data = json.load(f)
                    return data.get("accepted", False)
            return False
        except Exception as e:
            logger.error(f"Error reading accepted status: {str(e)}")
            return False

    def log_task_to_history(self, work):
        """Log a task to the history file"""
        self.task_history.log_task(work)

    def send_task_notification(self, tasks):
        """Send a formatted notification about available tasks"""
        if not tasks or not tasks.get("data", {}).get("work"):
            return

        work = tasks["data"]["work"]
        task_id = work.get("id")
        last_task_id = self.get_last_task_id()
        
        if last_task_id == task_id:
            logger.info(f"Same task {task_id}, skipping notification")
            return

        if self.send_message(format_task_message(work, task_id)):
            self.save_last_task_id(task_id, accepted=False)
            logger.info(f"Task {task_id} notification sent")

    def send_task_accepted_notification(self, tasks):
        """Send a notification that a task has been auto-accepted"""
        if not tasks or not tasks.get("data", {}).get("work"):
            return

        work = tasks["data"]["work"]
        task_id = work.get("id")

        if self.send_message(format_task_message(work, task_id, is_accepted=True)):
            self.save_last_task_id(task_id, accepted=True)
            logger.info(f"Task {task_id} marked as accepted and notification sent")

    def send_daily_summary(self):
        """Send daily summary of tasks from last 24 hours"""
        if not self.should_send_daily_summary():
            logger.info("Daily summary already sent today")
            return False
        
        summary = self.task_history.get_last_24_hours_summary()
        if not summary:
            logger.info("No task history available")
            return False
        
        total_tasks = sum(len(tasks) for tasks in summary.values())
        if total_tasks == 0:
            logger.info("No tasks in last 24 hours")
            return False
        
        if self.send_message(format_daily_summary(summary)):
            self.mark_daily_summary_sent()
            logger.info("Daily summary sent successfully")
            self.task_history.cleanup_old_tasks()
            return True
        return False

    def should_send_daily_summary(self):
        """Check if daily summary should be sent (once per day)"""
        try:
            today = datetime.now().date().isoformat()
            if os.path.exists(self.daily_summary_file):
                with open(self.daily_summary_file, "r") as f:
                    return json.load(f).get('last_summary_date') != today
            return True
        except Exception as e:
            logger.error(f"Error checking daily summary status: {str(e)}")
            return False

    def mark_daily_summary_sent(self):
        """Mark that daily summary has been sent today"""
        try:
            os.makedirs(os.path.dirname(self.daily_summary_file), exist_ok=True)
            with open(self.daily_summary_file, "w") as f:
                json.dump({"last_summary_date": datetime.now().date().isoformat()}, f)
        except Exception as e:
            logger.error(f"Error marking daily summary as sent: {str(e)}")
