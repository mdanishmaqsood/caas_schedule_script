"""
Mattermost client for sending notifications
"""

import json
import logging
import requests
import os
from datetime import datetime, timezone, timedelta
from src.config import MATTERMOST_CONFIG
from .task_history import TaskHistory
from .notification_formatter import format_task_message, format_daily_summary

# Pakistan timezone is UTC+5
PAKISTAN_TZ = timezone(timedelta(hours=5))

logger = logging.getLogger()


class MattermostClient:
    def __init__(self):
        self.webhook_url = MATTERMOST_CONFIG["webhook_url"]
        self.last_task_file = "src/data/last_task.json"
        self.daily_summary_file = "src/data/last_summary_date.json"
        self.daily_cleanup_file = "src/data/last_cleanup_date.json"
        self.task_history = TaskHistory()
        self._initialize_json_files()
    
    def _initialize_json_files(self):
        """Create JSON files with default values if they don't exist"""
        try:
            os.makedirs("src/data", exist_ok=True)
            files = {
                self.last_task_file: {"last_task_id": None, "accepted": False, "cancelled": False},
                self.task_history.history_file: [],
                self.daily_summary_file: {"last_summary_date": None},
                self.daily_cleanup_file: {"last_cleanup_date": None}
            }
            for path, default_data in files.items():
                if not os.path.exists(path):
                    with open(path, "w") as f:
                        json.dump(default_data, f)
                    logger.info(f"Created {path}")
        except Exception as e:
            logger.error(f"Error initializing JSON files: {str(e)}")

    def send_message(self, message, attachments=None):
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
            if not os.path.exists(self.last_task_file) or os.path.getsize(self.last_task_file) == 0:
                return None
            with open(self.last_task_file, "r") as f:
                content = f.read().strip()
                if not content:
                    return None
                data = json.loads(content)
                return data.get("last_task_id")
        except (json.JSONDecodeError, ValueError):
            return None
        except Exception as e:
            logger.error(f"Error reading last task ID: {str(e)}")
            return None

    def save_last_task_id(self, task_id, accepted=False, cancelled=False):
        """Save the last task ID to the storage file"""
        try:
            os.makedirs(os.path.dirname(self.last_task_file), exist_ok=True)
            temp_file = self.last_task_file + ".tmp"
            with open(temp_file, "w") as f:
                json.dump({"last_task_id": task_id, "accepted": accepted, "cancelled": cancelled}, f)
            if os.path.exists(self.last_task_file):
                os.remove(self.last_task_file)
            os.rename(temp_file, self.last_task_file)
        except Exception as e:
            logger.error(f"Error saving last task ID: {str(e)}")
    
    def get_accepted_task_status(self):
        """Get the accepted status of the last task"""
        try:
            if not os.path.exists(self.last_task_file) or os.path.getsize(self.last_task_file) == 0:
                return False
            with open(self.last_task_file, "r") as f:
                content = f.read().strip()
                if not content:
                    return False
                data = json.loads(content)
                return data.get("accepted", False)
        except (json.JSONDecodeError, ValueError):
            return False
        except Exception as e:
            logger.error(f"Error reading accepted status: {str(e)}")
            return False
    
    def get_cancelled_task_status(self):
        """Check if the last task was manually cancelled"""
        try:
            if not os.path.exists(self.last_task_file) or os.path.getsize(self.last_task_file) == 0:
                return False
            with open(self.last_task_file, "r") as f:
                content = f.read().strip()
                if not content:
                    return False
                data = json.loads(content)
                return data.get("cancelled", False)
        except (json.JSONDecodeError, ValueError):
            return False
        except Exception as e:
            logger.error(f"Error reading cancelled status: {str(e)}")
            return False
    
    def mark_task_as_cancelled(self, task_id):
        """Mark a task as manually cancelled to prevent re-acceptance"""
        try:
            self.save_last_task_id(task_id, accepted=False, cancelled=True)
            logger.info(f"Task {task_id} marked as cancelled")
        except Exception as e:
            logger.error(f"Error marking task as cancelled: {str(e)}")

    def log_task_to_history(self, work):
        """Log a task to the history file"""
        self.task_history.log_task(work)

    def has_task_been_notified(self, task_id):
        """Check if a task notification has already been sent"""
        return self.task_history.has_task(task_id)

    def send_task_notification(self, tasks):
        """Send a formatted notification about available tasks"""
        if not tasks or not tasks.get("data", {}).get("work"):
            return

        work = tasks["data"]["work"]
        task_id = work.get("id")
        if self.has_task_been_notified(task_id):
            logger.info(f"Task {task_id} already notified, skipping")
            return

        if self.send_message(format_task_message(work, task_id)):
            self.save_last_task_id(task_id, accepted=False)
            self.log_task_to_history(work)
            logger.info(f"Task {task_id} notification sent")

    def send_task_accepted_notification(self, tasks):
        """Send a notification that a task has been auto-accepted"""
        if not tasks or not tasks.get("data", {}).get("work"):
            return

        work = tasks["data"]["work"]
        task_id = work.get("id")
        if self.has_task_been_notified(task_id):
            logger.info(f"Task {task_id} already notified, skipping accepted notification")
            return

        if self.send_message(format_task_message(work, task_id, is_accepted=True)):
            self.save_last_task_id(task_id, accepted=True)
            self.log_task_to_history(work)
            logger.info(f"Task {task_id} marked as accepted and notification sent")

    def send_daily_summary(self):
        """Send daily summary of tasks from last 24 hours"""
        if not self.should_send_daily_summary():
            logger.info("Daily summary already sent today")
            return False
        
        try:
            summary = self.task_history.get_last_24_hours_summary()
            if not summary:
                logger.info("No task history available")
                return False
            
            total_tasks = sum(len(tasks) for tasks in summary.values())
            if total_tasks == 0:
                message = "📊 **Daily Task Summary (Last 24 Hours)**\n\n✅ No tasks were received in the last 24 hours.\n\n_All clear!_"
                if self.send_message(message):
                    self.mark_daily_summary_sent()
                    logger.info("Daily summary sent: No tasks in last 24 hours")
                    return True
                return False
            
            if self.send_message(format_daily_summary(summary)):
                self.mark_daily_summary_sent()
                logger.info("Daily summary sent successfully")
                return True
            return False
        except Exception as e:
            logger.error(f"Error sending daily summary: {str(e)}")
            return False

    def should_send_daily_summary(self):
        """Check if daily summary should be sent (once per day) using Pakistan time"""
        try:
            today = datetime.now(PAKISTAN_TZ).date().isoformat()
            if os.path.exists(self.daily_summary_file):
                with open(self.daily_summary_file, "r") as f:
                    return json.load(f).get('last_summary_date') != today
            return True
        except Exception as e:
            logger.error(f"Error checking daily summary status: {str(e)}")
            return False

    def mark_daily_summary_sent(self):
        """Mark that daily summary has been sent today using Pakistan date"""
        try:
            os.makedirs(os.path.dirname(self.daily_summary_file), exist_ok=True)
            with open(self.daily_summary_file, "w") as f:
                json.dump({"last_summary_date": datetime.now(PAKISTAN_TZ).date().isoformat()}, f)
        except Exception as e:
            logger.error(f"Error marking daily summary as sent: {str(e)}")

    def should_cleanup_end_of_day(self):
        """Check if end-of-day cleanup should be performed (once per day) using Pakistan time"""
        try:
            today = datetime.now(PAKISTAN_TZ).date().isoformat()
            if os.path.exists(self.daily_cleanup_file):
                with open(self.daily_cleanup_file, "r") as f:
                    content = f.read().strip()
                    if not content:
                        return True
                    return json.loads(content).get('last_cleanup_date') != today
            return True
        except (json.JSONDecodeError, ValueError):
            logger.warning("Cleanup tracking file corrupted or empty, allowing cleanup")
            return True
        except Exception as e:
            logger.error(f"Error checking cleanup status: {str(e)}")
            return False

    def mark_daily_cleanup_done(self):
        """Mark that end-of-day cleanup has been performed today using Pakistan date"""
        try:
            os.makedirs(os.path.dirname(self.daily_cleanup_file), exist_ok=True)
            with open(self.daily_cleanup_file, "w") as f:
                json.dump({"last_cleanup_date": datetime.now(PAKISTAN_TZ).date().isoformat()}, f)
        except Exception as e:
            logger.error(f"Error marking cleanup as done: {str(e)}")

    def cleanup_json_files_end_of_day(self):
        """Cleanup all JSON files at end of day (11:59 PM Pakistan time)"""
        try:
            os.makedirs("src/data", exist_ok=True)
            logger.info("Starting JSON files cleanup at end of day...")

            self.task_history.clear_history()
            logger.info("Cleared task_history.json - now empty []")

            with open(self.last_task_file, "w") as f:
                json.dump({"last_task_id": None, "accepted": False, "cancelled": False}, f)
            logger.info("Reset last_task.json to defaults")

            with open(self.daily_summary_file, "w") as f:
                json.dump({"last_summary_date": datetime.now(PAKISTAN_TZ).date().isoformat()}, f)
            logger.info("Updated last_summary_date.json to today's Pakistan date")

            self.mark_daily_cleanup_done()
            logger.info("Recorded end-of-day cleanup completion")

            logger.info("All JSON files cleaned up successfully - ready for new tasks!")
        except Exception as e:
            logger.error(f"Error cleaning JSON files at end of day: {str(e)}")

