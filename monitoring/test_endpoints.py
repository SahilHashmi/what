import requests
import json

def test_automation_logs():
    print("\nTesting Automation Logs endpoint...")
    response = requests.get('http://127.0.0.1:5000/monitoring/automation-logs')
    print(f"Status Code: {response.status_code}")
    print("Response:")
    print(json.dumps(response.json(), indent=2))

def test_match_rate():
    print("\nTesting Match Rate endpoint...")
    response = requests.get('http://127.0.0.1:5000/monitoring/match-rate')
    print(f"Status Code: {response.status_code}")
    print("Response:")
    print(json.dumps(response.json(), indent=2))

def test_failed_queries():
    print("\nTesting Failed Queries endpoint...")
    response = requests.get('http://127.0.0.1:5000/monitoring/failed-queries')
    print(f"Status Code: {response.status_code}")
    print("Response:")
    print(json.dumps(response.json(), indent=2))

def test_conversation_stats():
    print("\nTesting Conversation Stats endpoint...")
    response = requests.get('http://127.0.0.1:5000/monitoring/conversation-stats')
    print(f"Status Code: {response.status_code}")
    print("Response:")
    print(json.dumps(response.json(), indent=2))

if __name__ == '__main__':
    test_automation_logs()
    test_match_rate()
    test_failed_queries()
    test_conversation_stats()
