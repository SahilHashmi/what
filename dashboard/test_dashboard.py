import os
import sys
import json
import requests
import time

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_dashboard_service():
    print("Testing dashboard service...")
    print("\nWaiting for server to start...")
    time.sleep(2)
    
    try:
        # Get dashboard stats
        print("\nGetting dashboard statistics...")
        response = requests.get("http://localhost:8000/dashboard/stats")
        if response.status_code == 200:
            print("\nDashboard Statistics:")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"\nFailed to get dashboard stats. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return
            
        # Test alerts endpoint
        print("\nTesting alerts endpoint...")
        response = requests.get("http://localhost:8000/alerts")
        if response.status_code == 200:
            print("\nAlerts:")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"\nFailed to get alerts. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return
            
        # Test resolving an alert
        if response.json():
            alert_id = response.json()[0]["id"]
            print(f"\nResolving alert {alert_id}...")
            response = requests.post(f"http://localhost:8000/alerts/{alert_id}/resolve")
            if response.status_code == 200:
                print("\nAlert resolution:")
                print(json.dumps(response.json(), indent=2))
            else:
                print(f"\nFailed to resolve alert. Status code: {response.status_code}")
                print(f"Response: {response.text}")
        
    except Exception as e:
        print(f"\nError occurred: {str(e)}")
        print(f"Response status code: {response.status_code if 'response' in locals() else 'N/A'}")
        print(f"Response content: {response.text if 'response' in locals() else 'N/A'}")

if __name__ == "__main__":
    test_dashboard_service()
