import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_backend.settings')

# Setup Django
django.setup()

from school.models import User, Teacher
from school.views import _generate_barcode_for_user

# Check if the user exists
user_exists = User.objects.filter(email='teacher1@example.com').exists()
print(f"User exists: {user_exists}")

if user_exists:
    user = User.objects.get(email='teacher1@example.com')
    print(f"User role: {user.role}")
    
    # Check if the teacher profile exists
    if user.role == 'Teacher':
        teacher_exists = hasattr(user, 'teacher')
        print(f"Teacher profile exists: {teacher_exists}")
        
        if teacher_exists:
            try:
                # Try to generate the barcode
                barcode_url = _generate_barcode_for_user(user)
                print(f"Barcode generated successfully: {barcode_url}")
            except Exception as e:
                print(f"Error generating barcode: {e}")
        else:
            print("Teacher profile not found")
    else:
        print(f"User is not a teacher, but a {user.role}")
else:
    print("User does not exist")