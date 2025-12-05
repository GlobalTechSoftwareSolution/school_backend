import requests

# Base URL for the API
BASE_URL = "http://127.0.0.1:8000/api"

def test_holidays():
    """Test the holidays endpoint with and without pagination"""
    print("=== Testing holidays endpoint ===")
    
    # Test without pagination (should return all records directly)
    try:
        response = requests.get(f"{BASE_URL}/holidays/", timeout=10)
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
    
    # Test with pagination (should return paginated response)
    try:
        response = requests.get(f"{BASE_URL}/holidays/", params={"page": 1, "page_size": 5}, timeout=10)
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

if __name__ == "__main__":
    test_holidays()