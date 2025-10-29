import requests
import json

# Test token generation with role
url = "http://127.0.0.1:8000/api/token/"
data = {
    "email": "student1@school.com",
    "password": "student1@school.com",
    "role": "Student"  # Role is now required
}

response = requests.post(url, json=data)

print("Status Code:", response.status_code)
print("\nResponse:")
print(json.dumps(response.json(), indent=2))

# If successful, decode the access token to see the payload
if response.status_code == 200:
    import jwt
    token_data = response.json()
    access_token = token_data.get('access')
    
    # Decode without verification to see payload (for testing only)
    decoded = jwt.decode(access_token, options={"verify_signature": False})
    print("\nDecoded Access Token Payload:")
    print(json.dumps(decoded, indent=2))
