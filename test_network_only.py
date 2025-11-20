import requests
import sys

URL = "https://minio.globaltechsoftwaresolutions.cloud:9000/school-media/images/t001/profile.jpg"

print(f"Starting network test for: {URL}")
try:
    print("Sending HEAD request...")
    response = requests.head(URL, timeout=5)
    print(f"Response Code: {response.status_code}")
    print("Network check PASSED.")
except Exception as e:
    print(f"Network check FAILED: {e}")
