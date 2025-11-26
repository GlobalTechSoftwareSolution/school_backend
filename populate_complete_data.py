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

def populate_complete_data():
    print('Starting to populate database with complete data...')
    
    # Get existing departments
    departments = list(Department.objects.all())
    
    # Get existing classes
    classes = list(Class.objects.all())
    
    # Get existing subjects
    subjects = list(Subject.objects.all())
    
    # Create users for different roles
    user_data = [
        ('student1@school.com', 'Student'),
        ('student2@school.com', 'Student'),
        ('teacher1@school.com', 'Teacher'),
        ('teacher2@school.com', 'Teacher'),
        ('management@school.com', 'Management'),
        ('admin@school.com', 'Admin'),
        ('parent1@school.com', 'Parent'),
        ('parent2@school.com', 'Parent'),
    ]
    
    users = []
    for email, role in user_data:
        try:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'role': role,
                    'is_approved': True,
                    'is_active': True,
                    'is_staff': role in ['Admin', 'Principal', 'Management'],
                }
            )
            if created:
                user.set_password('password123')
                user.save()
            users.append(user)
            print(f"User {'created' if created else 'already exists'}: {email} ({role})")
        except Exception as e:
            print(f'Error creating user {email}: {e}')
            continue
    
    # Create students
    students = []
    student_names = ['John Doe', 'Jane Smith', 'Alice Johnson', 'Bob Wilson', 'Charlie Brown', 'Diana Prince']
    student_users = [u for u in users if u.role == 'Student']
    for i, name in enumerate(student_names):
        if i >= len(student_users):
            break
        user = student_users[i]
        try:
            student, created = Student.objects.get_or_create(
                email=user,
                defaults={
                    'fullname': name,
                    'student_id': f'STD{i+1:03d}',
                    'phone': f'+123456789{i:02d}',
                    'date_of_birth': timezone.now().astimezone(IST).date() - timedelta(days=365*15),
                    'gender': random.choice(['Male', 'Female']),
                    'admission_date': timezone.now().astimezone(IST).date() - timedelta(days=30),
                    'class_id': random.choice(classes) if classes else None,
                    'profile_picture': 'https://example.com/profile.jpg',
                    'residential_address': f'{i+1} Main Street, City',
                    'emergency_contact_name': f'Emergency Contact {i+1}',
                    'emergency_contact_relationship': 'Parent',
                    'emergency_contact_no': f'+987654321{i:02d}',
                    'nationality': 'Indian',
                    'father_name': f'Father of {name}',
                    'mother_name': f'Mother of {name}',
                    'blood_group': random.choice(['A+', 'B+', 'O+', 'AB+']),
                }
            )
            students.append(student)
            print(f"Student {'created' if created else 'already exists'}: {name}")
        except Exception as e:
            print(f'Error creating student {name}: {e}')
            continue
    
    # Create parents
    parents = []
    parent_names = ['John Doe Sr.', 'Jane Smith Sr.', 'Alice Johnson Sr.', 'Bob Wilson Sr.', 'Charlie Brown Sr.', 'Diana Prince Sr.']
    parent_users = [u for u in users if u.role == 'Parent']
    for i, name in enumerate(parent_names):
        if i >= len(parent_users):
            break
        user = parent_users[i]
        try:
            parent, created = Parent.objects.get_or_create(
                email=user,
                defaults={
                    'fullname': name,
                    'phone': f'+123456789{i:02d}',
                    'occupation': random.choice(['Engineer', 'Doctor', 'Teacher', 'Businessman', 'Lawyer']),
                    'residential_address': f'{i+1} Parent Street, City',
                    'profile_picture': 'https://example.com/profile.jpg',
                    'relationship_to_student': 'Father' if i % 2 == 0 else 'Mother',
                }
            )
            parents.append(parent)
            print(f"Parent {'created' if created else 'already exists'}: {name}")
        except Exception as e:
            print(f'Error creating parent {name}: {e}')
            continue
    
    # Link students to parents
    for i, student in enumerate(students):
        if parents:
            parent = parents[i % len(parents)]
            student.parent = parent
            student.save()
            print(f"Linked student {student.fullname} to parent {parent.fullname}")
    
    # Create teachers
    teachers = []
    teacher_names = ['Michael Brown', 'Sarah Davis', 'Robert Miller', 'Emily Wilson', 'David Johnson', 'Lisa Anderson']
    teacher_users = [u for u in users if u.role == 'Teacher']
    for i, name in enumerate(teacher_names):
        if i >= len(teacher_users):
            break
        user = teacher_users[i]
        try:
            teacher, created = Teacher.objects.get_or_create(
                email=user,
                defaults={
                    'fullname': name,
                    'teacher_id': f'TCHR{i+1:03d}',
                    'phone': f'+123456789{i:02d}',
                    'date_of_birth': timezone.now().astimezone(IST).date() - timedelta(days=365*30),
                    'gender': random.choice(['Male', 'Female']),
                    'date_joined': timezone.now().astimezone(IST).date() - timedelta(days=365),
                    'department': random.choice(departments) if departments else None,
                    'qualification': random.choice(['B.Ed', 'M.Ed', 'PhD']),
                    'experience_years': Decimal(random.randint(2, 15)),
                    'profile_picture': 'https://example.com/profile.jpg',
                    'residential_address': f'{i+1} Teacher Street, City',
                    'emergency_contact_name': f'Emergency Contact {i+1}',
                    'emergency_contact_relationship': 'Spouse',
                    'emergency_contact_no': f'+987654321{i:02d}',
                    'nationality': 'Indian',
                    'blood_group': random.choice(['A+', 'B+', 'O+', 'AB+']),
                    'is_classteacher': i < 2,
                    'class_id': random.choice(classes) if classes and i < 2 else None,
                }
            )
            # Set sec field based on class
            if teacher.class_id:
                teacher.sec = teacher.class_id.sec
            else:
                teacher.sec = 'A'  # Default section
            teacher.save()
            teachers.append(teacher)
            print(f"Teacher {'created' if created else 'already exists'}: {name}")
        except Exception as e:
            print(f'Error creating teacher {name}: {e}')
            continue
    
    # Create management
    management_user = next((u for u in users if u.role == 'Management'), None)
    if management_user:
        try:
            management, created = Management.objects.get_or_create(
                email=management_user,
                defaults={
                    'fullname': 'Management Staff',
                    'phone': '+1234567891',
                    'designation': 'Manager',
                    'date_of_birth': timezone.now().astimezone(IST).date() - timedelta(days=365*35),
                    'date_joined': timezone.now().astimezone(IST).date() - timedelta(days=365*3),
                    'department': random.choice(departments) if departments else None,
                    'profile_picture': 'https://example.com/profile.jpg',
                    'office_address': 'Management Office, School Building',
                }
            )
            print(f"Management {'created' if created else 'already exists'}: {management.fullname}")
        except Exception as e:
            print(f'Error creating management: {e}')
    
    # Create admin
    admin_user = next((u for u in users if u.role == 'Admin'), None)
    if admin_user:
        try:
            admin, created = Admin.objects.get_or_create(
                email=admin_user,
                defaults={
                    'fullname': 'Admin Name',
                    'phone': '+1234567892',
                    'office_address': 'Admin Office, School Building',
                    'profile_picture': 'https://example.com/profile.jpg',
                }
            )
            print(f"Admin {'created' if created else 'already exists'}: {admin.fullname}")
        except Exception as e:
            print(f'Error creating admin: {e}')
    
    # Create attendance records for students
    today = timezone.now().astimezone(IST).date()
    for student in students:
        try:
            attendance, created = Attendance.objects.get_or_create(
                user=student.email,
                date=today,
                defaults={
                    'check_in': timezone.now().astimezone(IST).time(),
                    'status': 'Present',
                    'role': 'Student',
                    'remarks': 'Regular attendance',
                }
            )
            print(f"Attendance {'created' if created else 'already exists'} for student: {student.fullname}")
        except Exception as e:
            print(f'Error creating attendance for {student.fullname}: {e}')
            continue
            
    # Create attendance records for teachers
    for teacher in teachers:
        try:
            attendance, created = Attendance.objects.get_or_create(
                user=teacher.email,
                date=today,
                defaults={
                    'check_in': timezone.now().astimezone(IST).time(),
                    'status': 'Present',
                    'role': 'Teacher',
                    'remarks': 'Regular attendance',
                }
            )
            print(f"Attendance {'created' if created else 'already exists'} for teacher: {teacher.fullname}")
        except Exception as e:
            print(f'Error creating attendance for teacher {teacher.fullname}: {e}')
            continue
    
    # Create grades
    for student in students[:3]:  # First 3 students
        for subject in subjects[:3]:  # First 3 subjects
            try:
                grade, created = Grade.objects.get_or_create(
                    student=student,
                    subject=subject,
                    exam_type='Midterm',
                    defaults={
                        'marks_obtained': Decimal(random.randint(60, 95)),
                        'total_marks': Decimal(100),
                        'exam_date': today - timedelta(days=10),
                        'remarks': 'Good performance',
                    }
                )
                print(f"Grade {'created' if created else 'already exists'} for {student.fullname} in {subject.subject_name}")
            except Exception as e:
                print(f'Error creating grade for {student.fullname} in {subject.subject_name}: {e}')
                continue
    
    # Create fee structure
    for cls in classes[:3]:  # First 3 classes
        try:
            fee_structure, created = FeeStructure.objects.get_or_create(
                class_id=cls,
                fee_type='Tuition',
                defaults={
                    'amount': Decimal('5000.00'),
                    'frequency': 'Monthly',
                    'description': f'Tuition fee for {cls.class_name} {cls.sec}',
                }
            )
            print(f"Fee structure {'created' if created else 'already exists'} for {cls.class_name} {cls.sec}")
        except Exception as e:
            print(f'Error creating fee structure for {cls.class_name} {cls.sec}: {e}')
            continue
    
    # Create assignments
    for subject in subjects[:3]:  # First 3 subjects
        try:
            assignment, created = Assignment.objects.get_or_create(
                title=f'Assignment for {subject.subject_name}',
                subject=subject,
                defaults={
                    'description': f'Assignment description for {subject.subject_name}',
                    'class_id': random.choice(classes) if classes else None,
                    'assigned_by': random.choice(users) if users else None,
                    'due_date': today + timedelta(days=7),
                    'attachment': 'https://example.com/assignment.pdf',
                    'status': 'Assigned',
                }
            )
            print(f"Assignment {'created' if created else 'already exists'} for {subject.subject_name}")
        except Exception as e:
            print(f'Error creating assignment for {subject.subject_name}: {e}')
            continue
    
    # Create timetable entries
    for cls in classes[:2]:  # First 2 classes
        for subject in subjects[:3]:  # First 3 subjects
            try:
                timetable, created = Timetable.objects.get_or_create(
                    class_id=cls,
                    subject=subject,
                    day_of_week=random.choice(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']),
                    defaults={
                        'teacher': random.choice(teachers) if teachers else None,
                        'start_time': timezone.now().astimezone(IST).time().replace(hour=9, minute=0),
                        'end_time': timezone.now().astimezone(IST).time().replace(hour=10, minute=0),
                        'room_number': f'Room {random.randint(101, 110)}',
                    }
                )
                print(f"Timetable {'created' if created else 'already exists'} for {cls.class_name} {cls.sec} - {subject.subject_name}")
            except Exception as e:
                print(f'Error creating timetable for {cls.class_name} {cls.sec} - {subject.subject_name}: {e}')
                continue
    
    # Create notices
    try:
        notice, created = Notice.objects.get_or_create(
            title='School Holiday Notice',
            defaults={
                'message': 'This is to inform all students and parents that the school will remain closed on account of the upcoming holiday.',
                'email': random.choice(users) if users else None,
                'posted_date': timezone.now().astimezone(IST),
                'valid_until': timezone.now().astimezone(IST) + timedelta(days=30),
                'important': True,
                'attachment': 'https://example.com/notice.pdf',
                'notice_by': random.choice(users) if users else None,
            }
        )
        print(f"Notice {'created' if created else 'already exists'}: {notice.title}")
    except Exception as e:
        print(f'Error creating notice: {e}')
    
    # Create documents for students
    for student in students:
        try:
            document, created = Document.objects.get_or_create(
                email=student.email,
                defaults={
                    'tenth': 'https://example.com/tenth.pdf',
                    'twelth': 'https://example.com/twelth.pdf',
                    'degree': 'https://example.com/degree.pdf',
                    'marks_card': 'https://example.com/marks_card.pdf',
                    'certificates': 'https://example.com/certificates.pdf',
                    'uploaded_at': timezone.now(),
                }
            )
            print(f"Document {'created' if created else 'already exists'} for {student.fullname}")
        except Exception as e:
            print(f'Error creating document for {student.fullname}: {e}')
            continue
    
    # Create awards
    for student in students[:2]:  # First 2 students
        try:
            award, created = Award.objects.get_or_create(
                email=student.email,
                title='Academic Excellence Award',
                defaults={
                    'description': 'Awarded for outstanding academic performance',
                    'photo': 'https://example.com/award.jpg',
                    'created_at': timezone.now(),
                }
            )
            print(f"Award {'created' if created else 'already exists'} for {student.fullname}")
        except Exception as e:
            print(f'Error creating award for {student.fullname}: {e}')
            continue
    
    print('Complete data population finished successfully!')

if __name__ == '__main__':
    populate_complete_data()