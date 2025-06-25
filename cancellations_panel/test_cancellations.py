import os
import sys
import json
import requests
import time
from datetime import datetime, timedelta
from main import (
    CancellationCreate, 
    QuickRebookingSuggestionCreate, 
    CancellationReason,
    WorkerResponse,
    ShiftResponse,
    WorkerCreate,
    ShiftCreate,
    ShiftStatus
)

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_cancellations_panel():
    print("Testing Cancellations Panel API...")
    print("\nWaiting for server to start...")
    time.sleep(2)
    
    try:
        # Create test worker
        print("\nCreating test worker...")
        worker_data = WorkerCreate(
            name="Test Worker",
            status=True,
            is_standby=False
        )
        response = requests.post(
            "http://localhost:8003/workers",
            json=worker_data.model_dump()
        )
        if response.status_code != 200:
            print(f"\nFailed to create worker. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return
        
        worker = response.json()
        print("\nSuccessfully created worker:")
        print(json.dumps(worker, indent=2))
        worker_id = worker["id"]
        
        # Create test shift
        print("\nCreating test shift...")
        now = datetime.now()
        shift_data = ShiftCreate(
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=3),
            status=ShiftStatus.ACTIVE,
            worker_id=worker_id,
            notes="Test shift"
        )
        # Convert datetime objects to ISO format
        shift_dict = shift_data.model_dump()
        shift_dict["start_time"] = shift_dict["start_time"].isoformat()
        shift_dict["end_time"] = shift_dict["end_time"].isoformat()
        response = requests.post(
            "http://localhost:8003/shifts",
            json=shift_dict
        )
        if response.status_code != 200:
            print(f"\nFailed to create shift. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return
        
        shift = response.json()
        print("\nSuccessfully created shift:")
        print(json.dumps(shift, indent=2))
        shift_id = shift["id"]
        
        # Create test cancellation
        print("\nCreating test cancellation...")
        cancellation_data = CancellationCreate(
            shift_id=shift_id,
            worker_id=worker_id,
            reason=CancellationReason.LATE_CANCELLATION,
            reason_detail="Worker cancelled last minute",
            cancellation_time=datetime.now()
        )
        # Convert datetime objects to ISO format
        cancellation_dict = cancellation_data.model_dump()
        cancellation_dict["cancellation_time"] = cancellation_dict["cancellation_time"].isoformat()
        response = requests.post(
            "http://localhost:8003/cancellations",
            json=cancellation_dict
        )
        if response.status_code != 200:
            print(f"\nFailed to create cancellation. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return
        
        print("\nSuccessfully created cancellation:")
        print(json.dumps(response.json(), indent=2))
        cancellation_id = response.json()["id"]
        
        # Get cancellations
        print("\nGetting cancellations...")
        response = requests.get(
            "http://localhost:8003/cancellations",
            params={
                "status": "auto_replied",
                "worker_id": worker_id
            }
        )
        if response.status_code != 200:
            print(f"\nFailed to get cancellations. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return
        
        print("\nFound cancellations:")
        print(json.dumps(response.json(), indent=2))
        
        # Blacklist worker
        print("\nBlacklisting worker...")
        response = requests.put(
            f"http://localhost:8003/cancellations/{cancellation_id}/blacklist"
        )
        if response.status_code != 200:
            print(f"\nFailed to blacklist worker. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return
        
        print("\nWorker blacklisted successfully:")
        print(json.dumps(response.json(), indent=2))
        
        # Create rebooking suggestion
        print("\nCreating rebooking suggestion...")
        suggestion_data = QuickRebookingSuggestionCreate(
            original_shift_id=shift_id,
            suggested_worker_id=worker_id,
            suggestion_time=datetime.now()
        )
        # Convert datetime objects to ISO format
        suggestion_dict = suggestion_data.model_dump()
        suggestion_dict["suggestion_time"] = suggestion_dict["suggestion_time"].isoformat()
        response = requests.post(
            "http://localhost:8003/rebooking-suggestions",
            json=suggestion_dict
        )
        if response.status_code != 200:
            print(f"\nFailed to create rebooking suggestion. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return
        
        print("\nSuccessfully created rebooking suggestion:")
        print(json.dumps(response.json(), indent=2))
        
    except Exception as e:
        print(f"\nError occurred: {str(e)}")
        print(f"Response status code: {response.status_code if 'response' in locals() else 'N/A'}")
        print(f"Response content: {response.text if 'response' in locals() else 'N/A'}")

if __name__ == "__main__":
    test_cancellations_panel()
