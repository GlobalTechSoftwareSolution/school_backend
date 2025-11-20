import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

URL = "https://minio.globaltechsoftwaresolutions.cloud:9000/school-media/images/t001/profile.jpg"

print(f"Testing (No SSL): {URL}")
try:
    response = requests.head(URL, timeout=5, verify=False)
    print(f"Response Code: {response.status_code}")
except Exception as e:
    print(f"Error: {e}")
