"""
Mattermost client for sending notifications
"""

import json
import logging
import requests
import os
from src.config import MATTERMOST_CONFIG

# Configure logging for CloudWatch
logger = logging.getLogger()


class MattermostClient:
    def __init__(self):
        self.webhook_url = MATTERMOST_CONFIG["webhook_url"]
        self.last_task_file = "src/data/last_task.json"

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
                "text": message,
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

    def save_last_task_id(self, task_id):
        """Save the last task ID to the storage file"""
        try:
            os.makedirs(os.path.dirname(self.last_task_file), exist_ok=True)
            with open(self.last_task_file, "w") as f:
                json.dump({"last_task_id": task_id}, f)
        except Exception as e:
            logger.error(f"Error saving last task ID: {str(e)}")

    def send_task_notification(self, tasks):
        """
        Send a formatted notification about available tasks

        Args:
            tasks (dict): The tasks data from CaaS API
        """
        if not tasks or not tasks.get("data", {}).get("work"):
            return

        work = tasks["data"]["work"]
        task_id = work.get("id")

        # Check if this is the same task as last time
        last_task_id = self.get_last_task_id()
        if last_task_id == task_id:
            logger.info("Same task as last time, skipping notification")
            return

        # Format the message with task details
        message = (
            "🎯 **New Task Available!**\n\n"
            f"**Title:** {work.get('title', 'N/A')}\n"
            f"**Task ID:** {task_id}\n"
            f"**Priority:** {work.get('priority', 'N/A')}\n"
            f"**Skills Required:** {', '.join(work.get('skills', ['N/A']))}\n\n"
            f"**Description:**\n{work.get('description', 'No description available')}\n\n"
            f"**Repository:** {work.get('repoUrl', 'N/A')}\n"
            f"**Branch:** {work.get('branchName', 'N/A')}\n"
        )

        # Send the message
        if self.send_message(message):
            # Save the new task ID
            self.save_last_task_id(task_id)
