import os
import django
import sys
import requests
import time

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_backend.settings')
django.setup()

from school.models import Teacher, Principal, Admin, Management

def check_system():
    print("--- Checking System Prerequisites ---")
    try:
        import face_recognition
        print("[OK] face_recognition library is installed.")
    except ImportError:
        print("[CRITICAL] face_recognition library is NOT installed!")

    print("\n--- Checking User Data & Connectivity ---")
    
    roles = {
        'Teacher': Teacher,
        'Principal': Principal,
        'Admin': Admin,
        'Management': Management
    }
    
    found_valid_user = False
    
    for role_name, model in roles.items():
        users = model.objects.exclude(profile_picture__isnull=True).exclude(profile_picture='')
        if not users.exists():
            continue
            
        print(f"\nChecking {role_name}s with profile pictures ({users.count()} found):")
        
        for user in users:
            email = user.email.email if hasattr(user.email, 'email') else str(user.email)
            url = user.profile_picture
            print(f"  User: {user.fullname} ({email})")
            print(f"  URL: {url}")
            
            try:
                # Test connectivity
                start = time.time()
                response = requests.get(url, timeout=5)
                duration = time.time() - start
                
                if response.status_code == 200:
                    print(f"    [OK] Image accessible ({len(response.content)} bytes) in {duration:.2f}s")
                    found_valid_user = True
                else:
                    print(f"    [FAIL] Image not accessible. Status: {response.status_code}")
            except Exception as e:
                print(f"    [FAIL] Error accessing image: {e}")
                
            # Only check first 3 per role to save time
            if users.count() > 3:
                print("    ... (skipping remaining users for this role)")
                break

    if not found_valid_user:
        print("\n[WARNING] No accessible profile pictures found! Face recognition will fail for everyone.")
    else:
        print("\n[OK] Found at least one user with an accessible profile picture.")

if __name__ == "__main__":
    check_system()
