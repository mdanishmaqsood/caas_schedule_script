#!/usr/bin/env python3
"""
CaaS Task Check Script
This script can be run directly or via cron job
"""

import logging
import sys
from datetime import datetime, timezone
from src.clients.caas_client import CaaSClient

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

        current_hour = datetime.now(timezone.utc).hour
        if current_hour == 13:
            logger.info("Attempting to send daily summary...")
            client.mattermost.send_daily_summary()
            
    except Exception as e:
        logger.info(f"Error in main: {str(e)}")
        raise

if __name__ == "__main__":
    main() 