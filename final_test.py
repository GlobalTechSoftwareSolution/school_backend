import requests
import time

# Base URL for the API
BASE_URL = "http://127.0.0.1:8000/api"

# List of all endpoints to test including the newly updated ones
ENDPOINTS = [
    "users",
    "departments", 
    "subjects",
    "classes",
    "students",
    "teachers",
    "attendance",
    "student_attendance",
    "awards",
    "id_cards",
    "timetable",
    "principals",
    "management",
    "admins",
    "parents",
    "grades",
    "fee_structures",
    "fee_payments",
    "activities",
    "former_members",
    "programs",
    "reports",
    "finance",
    "transport_details",
    "notices",
    "documents",
    "assignments",
    "submitted_assignments",
    "leaves",
    "tasks",
    "projects",
    "issues",
    "holidays"
]

def test_endpoint(endpoint):
    """Test an endpoint with and without pagination"""
    print(f"\n=== Testing {endpoint} ===")
    
    # Test without pagination (should return all records directly)
    try:
        response = requests.get(f"{BASE_URL}/{endpoint}/", timeout=10)
        print(f"Without pagination - Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            # Check if it's paginated (has 'results' key) or not
            if 'results' in data:
                print(f"  ❌ Unexpectedly paginated - Count: {data.get('count', 'N/A')}")
            else:
                print(f"  ✅ Correctly returns all records - Count: {len(data)}")
        else:
            print(f"  ⚠️  Request failed - {response.status_code}")
    except Exception as e:
        print(f"  ⚠️  Error: {e}")
    
    # Small delay to avoid overwhelming the server
    time.sleep(0.1)
    
    # Test with pagination (should return paginated response)
    try:
        response = requests.get(f"{BASE_URL}/{endpoint}/", params={"page": 1, "page_size": 5}, timeout=10)
        print(f"With pagination - Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            # Check if it's paginated (has 'results' key)
            if 'results' in data:
                print(f"  ✅ Correctly paginated - Count: {data.get('count', 'N/A')}, Page size: {len(data.get('results', []))}")
            else:
                print(f"  ❌ Unexpectedly not paginated - Count: {len(data)}")
        else:
            print(f"  ⚠️  Request failed - {response.status_code}")
    except Exception as e:
        print(f"  ⚠️  Error: {e}")

def main():
    print("Testing conditional pagination for all endpoints...")
    print("=" * 50)
    
    success_count = 0
    total_count = len(ENDPOINTS)
    
    for endpoint in ENDPOINTS:
        try:
            test_endpoint(endpoint)
            success_count += 1
        except Exception as e:
            print(f"Failed to test {endpoint}: {e}")
    
    print("\n" + "=" * 50)
    print(f"Testing complete! Successfully tested {success_count}/{total_count} endpoints.")

if __name__ == "__main__":
    main()