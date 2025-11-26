import os
import django
from decimal import Decimal
import random

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta
from school.models import (
    Department, Class, Subject, Student, Teacher, Principal, Management, Admin, Parent,
    Attendance, Grade, FeeStructure, FeePayment, Timetable, Assignment, FormerMember,
    Document, Award, Notice, Issue, Holiday, Leave, Task, Project, Program, Activity,
    Report, FinanceTransaction, TransportDetails
)

# Define IST timezone for Indian Standard Time
import pytz
IST = pytz.timezone("Asia/Kolkata")

User = get_user_model()

def populate_basic_data():
    print('Starting to populate database with basic data...')
    
    # Create departments
    departments = []
    dept_names = ['Mathematics', 'Science', 'English', 'History', 'Art', 'Physical Education']
    for name in dept_names:
        dept, created = Department.objects.get_or_create(
            department_name=name,
            defaults={'description': f'Department of {name}'}
        )
        departments.append(dept)
        print(f"Department {'created' if created else 'already exists'}: {name}")
    
    # Create classes
    classes = []
    class_data = [
        ('1st Grade', 'A'), ('1st Grade', 'B'), ('2nd Grade', 'A'), ('2nd Grade', 'B'),
        ('3rd Grade', 'A'), ('3rd Grade', 'B'), ('4th Grade', 'A'), ('4th Grade', 'B'),
        ('5th Grade', 'A'), ('5th Grade', 'B'), ('6th Grade', 'A'), ('6th Grade', 'B'),
        ('7th Grade', 'A'), ('7th Grade', 'B'), ('8th Grade', 'A'), ('8th Grade', 'B'),
        ('9th Grade', 'A'), ('9th Grade', 'B'), ('10th Grade', 'A'), ('10th Grade', 'B'),
    ]
    for class_name, sec in class_data:
        cls, created = Class.objects.get_or_create(
            class_name=class_name,
            sec=sec,
            defaults={'created_at': timezone.now().astimezone(IST), 'updated_at': timezone.now().astimezone(IST)}
        )
        classes.append(cls)
        print(f"Class {'created' if created else 'already exists'}: {class_name} {sec}")
    
    # Create subjects
    subjects = []
    subject_data = [
        ('Mathematics', 'MATH101'), ('Science', 'SCI101'), ('English', 'ENG101'),
        ('History', 'HIST101'), ('Art', 'ART101'), ('Physical Education', 'PE101'),
        ('Physics', 'PHY101'), ('Chemistry', 'CHEM101'), ('Biology', 'BIO101'),
    ]
    for name, code in subject_data:
        subj, created = Subject.objects.get_or_create(
            subject_name=name,
            subject_code=code,
            defaults={'description': f'Subject of {name}'}
        )
        subjects.append(subj)
        print(f"Subject {'created' if created else 'already exists'}: {name} ({code})")
    
    # Create a principal user
    principal_user, created = User.objects.get_or_create(
        email='principal@school.com',
        defaults={
            'role': 'Principal',
            'is_approved': True,
            'is_active': True,
            'is_staff': True,
        }
    )
    if created:
        principal_user.set_password('principal123')
        principal_user.save()
    print(f"Principal user {'created' if created else 'already exists'}: {principal_user.email}")
    
    # Create principal profile
    principal, created = Principal.objects.get_or_create(
        email=principal_user,
        defaults={
            'fullname': 'Dr. Principal Name',
            'phone': '+1234567890',
            'date_of_birth': timezone.now().astimezone(IST).date() - timedelta(days=365*45),
            'date_joined': timezone.now().astimezone(IST).date() - timedelta(days=365*5),
            'qualification': 'PhD in Education',
            'total_experience': Decimal('20.0'),
            'bio': 'Experienced educational leader',
            'profile_picture': 'https://example.com/profile.jpg',
            'office_address': 'Principal Office, School Building',
        }
    )
    print(f"Principal profile {'created' if created else 'already exists'}: {principal.fullname}")
    
    print('Basic data population completed successfully!')

if __name__ == '__main__':
    populate_basic_data()