#!/usr/bin/env python3
"""
CaaS Task Check Script
This script can be run directly or via cron job
"""

import logging
import sys
from datetime import datetime, timezone, timedelta
from src.clients.caas_client import CaaSClient

# Pakistan timezone is UTC+5
PAKISTAN_TZ = timezone(timedelta(hours=5))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('caas_check.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger()

def main():
    """Main function to run the CaaS check"""
    try:
        logger.info("Starting CaaS automation check...")
        
        # Initialize client
        client = CaaSClient()
        
        # Login
        logger.info("Attempting to login to CaaS...")
        if not client.login():
            logger.info("Failed to login to CaaS")
            return
        
        # Get available tasks and send notifications
        logger.info("Checking for available tasks...")
        tasks = client.get_available_tasks_and_send_notification()
        if tasks:
            logger.info("Successfully checked for tasks and sent notifications")
        else:
            logger.info("No tasks available")

        # Check Pakistan time (UTC+5) for daily summary
        now_pakistan = datetime.now(PAKISTAN_TZ)
        # Send at 6:00 PM Pakistan time
        if now_pakistan.hour == 18 and now_pakistan.minute == 0:
            logger.info("Attempting to send daily summary at 6:00 PM Pakistan time...")
            client.mattermost.send_daily_summary()

        # Weekly cleanup on Sunday at 11:00 AM Pakistan time
        if now_pakistan.weekday() == 6 and now_pakistan.hour == 11 and now_pakistan.minute == 0:
            if client.mattermost.should_cleanup_weekly():
                logger.info("Attempting weekly cleanup on Sunday at 11:00 AM Pakistan time...")
                client.mattermost.cleanup_json_files_weekly()
            
    except Exception as e:
        logger.info(f"Error in main: {str(e)}")
        raise

if __name__ == "__main__":
    main() 