import os
import django
import sys

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_backend.settings')
django.setup()

from school.models import Teacher, Principal, Admin, Management

def inspect_urls():
    print("--- Inspecting Profile Picture URLs ---")
    
    roles = {
        'Teacher': Teacher,
        'Principal': Principal,
        'Admin': Admin,
        'Management': Management
    }
    
    for role_name, model in roles.items():
        users = model.objects.exclude(profile_picture__isnull=True).exclude(profile_picture='')
        if not users.exists():
            print(f"\nNo {role_name}s with profile pictures.")
            continue
            
        print(f"\n{role_name}s with profile pictures:")
        for user in users:
            email = user.email.email if hasattr(user.email, 'email') else str(user.email)
            url = user.profile_picture
            print(f"  User: {user.fullname} ({email})")
            print(f"  URL:  {url}")
            
            # Check for common issues
            if 'browser' in url:
                print("  [WARNING] URL contains 'browser'. This might be a MinIO UI link, not a direct image link!")
            if not url.lower().endswith(('.jpg', '.jpeg', '.png')):
                print("  [WARNING] URL does not end with a common image extension.")

if __name__ == "__main__":
    inspect_urls()
