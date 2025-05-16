"""
Local test script for CaaS automation
"""
import json
from src.clients.caas_client import CaaSClient

def main():
    print("Starting CaaS automation test...")
    
    # Initialize client
    client = CaaSClient()
    
    # Test login
    print("\nTesting login...")
    if client.login():
        print("✅ Login successful!")
    else:
        print("❌ Login failed!")
        return
    
    # Test getting tasks
    print("\nTesting task retrieval...")
    tasks = client.get_available_tasks_and_send_notification()
    if tasks:
        print("✅ Successfully retrieved tasks!")
        print("\nTasks data:")
        print(json.dumps(tasks, indent=2))
    # else:
    #     print("❌ Failed to retrieve tasks!")

if __name__ == "__main__":
    main() 