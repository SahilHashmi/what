import os
import sys
import json
import requests
import time
from datetime import datetime, timedelta
from main import ShiftCreate, ShiftFlag, WorkerCreate

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_booking_manager():
    print("Testing Booking Manager API...")
    print("\nWaiting for server to start...")
    time.sleep(2)
    
    try:
        # Create test worker
        print("\nCreating test worker...")
        worker_data = WorkerCreate(
            name="John Doe",
            status=True,
            is_standby=False
        )
        response = requests.post(
            "http://localhost:8002/workers",
            json=worker_data.model_dump()
        )
        if response.status_code == 200:
            print("\nSuccessfully created worker:")
            print(json.dumps(response.json(), indent=2))
            worker_id = response.json()["id"]
        else:
            print(f"\nFailed to create worker. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return
            
        # Create test shift
        print("\nCreating test shift...")
        start_time = datetime.now() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=2)
        shift_data = ShiftCreate(
            start_time=start_time,
            end_time=end_time,
            worker_id=worker_id,
            flag=ShiftFlag.NORMAL,
            notes="Test shift"
        )
        response = requests.post(
            "http://localhost:8002/shifts",
            json=shift_data.model_dump()
        )
        if response.status_code == 200:
            print("\nSuccessfully created shift:")
            print(json.dumps(response.json(), indent=2))
            shift_id = response.json()["id"]
        else:
            print(f"\nFailed to create shift. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return
            
        # Get available workers for a shift
        print("\nGetting available workers...")
        future_start = datetime.now() + timedelta(days=1)
        future_end = future_start + timedelta(hours=2)
        response = requests.get(
            "http://localhost:8002/shifts/available-workers",
            params={
                "shift_start": future_start.isoformat(),
                "shift_end": future_end.isoformat()
            }
        )
        if response.status_code == 200:
            print("\nAvailable workers:")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"\nFailed to get available workers. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return
            
        # Update shift status
        print("\nUpdating shift status...")
        response = requests.put(
            f"http://localhost:8002/shifts/{shift_id}",
            json={"status": "cancelled"}
        )
        if response.status_code == 200:
            print("\nShift status updated:")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"\nFailed to update shift status. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"\nError occurred: {str(e)}")
        print(f"Response status code: {response.status_code if 'response' in locals() else 'N/A'}")
        print(f"Response content: {response.text if 'response' in locals() else 'N/A'}")

if __name__ == "__main__":
    test_booking_manager()
