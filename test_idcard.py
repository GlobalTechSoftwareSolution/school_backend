import os
import sys
import django
import requests

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_backend.settings')

# Setup Django
django.setup()

from school.models import User, IDCard

# Check if we have users
print("Checking database...")
user_count = User.objects.count()
print(f"Total users: {user_count}")

if user_count > 0:
    # Get the first user
    user = User.objects.first()
    if user is not None:
        print(f"Testing with user: {user.email} ({user.role})")
        
        # Check if ID card already exists
        id_card_exists = IDCard.objects.filter(user=user).exists()
        print(f"ID card exists: {id_card_exists}")
        
        # Try to generate ID card
        try:
            response = requests.post('http://127.0.0.1:8000/api/id_cards/generate/', 
                                   json={'email': user.email})
            print(f"ID card generation response: {response.status_code}")
            print(f"Response data: {response.json()}")
        except Exception as e:
            print(f"Error generating ID card: {e}")
    else:
        print("No user found.")
else:
    print("No users found in database. Please create some users first.")