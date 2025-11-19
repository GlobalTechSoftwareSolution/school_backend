"""
Test script for the marks card API endpoint
"""
import requests
import json

# Test the marks card endpoint
url = "http://127.0.0.1:8000/api/marks_card/"
data = {
    "email": "student1@example.com"  # Replace with an actual student email
}

response = requests.post(url, json=data)

print("Status Code:", response.status_code)
print("Response:", response.text)