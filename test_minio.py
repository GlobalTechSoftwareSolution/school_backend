import os
import sys
from django.conf import settings

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_backend.settings')

import django
django.setup()

from minio import Minio
from django.conf import settings

def test_minio_connection():
    try:
        print(f"MinIO Configuration:")
        print(f"  Endpoint: {settings.MINIO_STORAGE['ENDPOINT']}")
        print(f"  Access Key: {settings.MINIO_STORAGE['ACCESS_KEY']}")
        print(f"  Secure: {settings.MINIO_STORAGE['USE_SSL']}")
        print(f"  Bucket: {settings.MINIO_STORAGE['BUCKET_NAME']}")
        
        # Create MinIO client
        client = Minio(
            settings.MINIO_STORAGE['ENDPOINT'],
            access_key=settings.MINIO_STORAGE['ACCESS_KEY'],
            secret_key=settings.MINIO_STORAGE['SECRET_KEY'],
            secure=settings.MINIO_STORAGE['USE_SSL']
        )
        
        # List objects in the bucket
        print(f"\nConnecting to bucket: {settings.MINIO_STORAGE['BUCKET_NAME']}")
        objects = client.list_objects(settings.MINIO_STORAGE['BUCKET_NAME'], recursive=True)
        
        print("Objects in bucket:")
        found_objects = False
        for obj in objects:
            print(f"  - {obj.object_name}")
            found_objects = True
            
        if not found_objects:
            print("  No objects found in bucket")
            
        # Try to access the specific profile picture
        try:
            response = client.stat_object(settings.MINIO_STORAGE['BUCKET_NAME'], 'images/student1/profile.jpg')
            print(f"\nProfile picture found:")
            print(f"  Size: {response.size} bytes")
            print(f"  Last modified: {response.last_modified}")
        except Exception as e:
            print(f"\nCould not access profile picture: {e}")
            
    except Exception as e:
        print(f"Error connecting to MinIO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_minio_connection()