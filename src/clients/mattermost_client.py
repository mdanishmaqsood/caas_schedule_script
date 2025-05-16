"""
Mattermost client for sending notifications
"""
import json
import logging
import requests
from src.config import MATTERMOST_CONFIG

# Configure logging for CloudWatch
logger = logging.getLogger()

class MattermostClient:
    def __init__(self):
        self.webhook_url = MATTERMOST_CONFIG["webhook_url"]

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

    def send_task_notification(self, tasks):
        """
        Send a formatted notification about available tasks

        Args:
            tasks (dict): The tasks data from CaaS API
        """
        if tasks:
            logger.info("Sending notification for available tasks...")
            message = "🎯 New tasks available!\n\n"
            return self.send_message(message) 

        else:
            pass
            # logger.info("No tasks available, sending notification...")
            # message = "❌ No tasks available at the moment"
            # return self.send_message(message)