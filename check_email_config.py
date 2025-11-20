import os
import sys
import django
from decouple import config

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_backend.settings')
django.setup()

from django.conf import settings

def check_email_settings():
    print("--- Email Configuration Check ---")
    print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    
    # Check if password is set (don't print it)
    password = settings.EMAIL_HOST_PASSWORD
    if password == 'your-email-password':
        print("EMAIL_HOST_PASSWORD: [WARNING] Using default placeholder!")
    elif not password:
        print("EMAIL_HOST_PASSWORD: [ERROR] Not set!")
    else:
        print(f"EMAIL_HOST_PASSWORD: [OK] Set (Length: {len(password)})")

    # Check .env file existence
    if os.path.exists('.env'):
        print("\n[OK] .env file found.")
    else:
        print("\n[WARNING] .env file NOT found!")

if __name__ == "__main__":
    check_email_settings()
