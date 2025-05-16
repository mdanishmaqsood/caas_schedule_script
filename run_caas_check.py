#!/usr/bin/env python3
"""
CaaS Task Check Script
This script can be run directly or via cron job
"""
import os
import sys
import logging
from datetime import datetime
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
logger = logging.getLogger(__name__)

def main():
    """Main function to run the CaaS check"""
    try:
        logger.info("Starting CaaS automation check...")
        
        # Initialize client
        client = CaaSClient()
        
        # Login
        logger.info("Attempting to login to CaaS...")
        if not client.login():
            logger.error("Failed to login to CaaS")
            return
        
        # Get available tasks and send notifications
        logger.info("Checking for available tasks...")
        tasks = client.get_available_tasks_and_send_notification()
        if tasks:
            logger.info("Successfully checked for tasks and sent notifications")
        else:
            logger.info("No tasks available")
            
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        raise

if __name__ == "__main__":
    main() 