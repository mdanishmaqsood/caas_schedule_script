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
        current_hour_pakistan = datetime.now(PAKISTAN_TZ).hour
        # Send at 6 PM Pakistan time (which is 1 PM UTC)
        if current_hour_pakistan == 18:
            logger.info("Attempting to send daily summary at 6 PM Pakistan time...")
            client.mattermost.send_daily_summary()
            
    except Exception as e:
        logger.info(f"Error in main: {str(e)}")
        raise

if __name__ == "__main__":
    main() 