import requests
import face_recognition
import io
import sys

URL = "https://minio.globaltechsoftwaresolutions.cloud:9000/school-media/images/t001/profile.jpg"

def test_url():
    print(f"Testing URL: {URL}")
    
    try:
        # 1. Test Download
        print("1. Attempting download...")
        response = requests.get(URL, timeout=10)
        print(f"   Status Code: {response.status_code}")
        print(f"   Content Type: {response.headers.get('content-type')}")
        print(f"   Content Length: {len(response.content)} bytes")
        
        if response.status_code != 200:
            print("   [FAIL] Could not download image.")
            print(f"   Response content preview: {response.content[:200]}")
            return

        # 2. Test Image Loading
        print("2. Attempting to load image with face_recognition...")
        image_file = io.BytesIO(response.content)
        try:
            image = face_recognition.load_image_file(image_file)
            print("   [OK] Image loaded successfully.")
        except Exception as e:
            print(f"   [FAIL] Could not load image: {e}")
            return

        # 3. Test Face Encoding
        print("3. Attempting to find face encodings...")
        encodings = face_recognition.face_encodings(image)
        if len(encodings) > 0:
            print(f"   [OK] Found {len(encodings)} face(s).")
        else:
            print("   [FAIL] No faces found in the profile picture!")

    except Exception as e:
        print(f"   [CRITICAL ERROR] {e}")

if __name__ == "__main__":
    test_url()
