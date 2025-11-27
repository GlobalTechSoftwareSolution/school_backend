import random
from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import transaction
from django.contrib.auth import get_user_model
from school.models import *

User = get_user_model()

class Command(BaseCommand):
    help = 'Clear all data and populate database with exactly 5 records for each model'

    def handle(self, *args, **options):
        self.stdout.write('Starting to clear all data...')
        
        # Get all models from the school app
        school_models = apps.get_app_config('school').get_models()
        
        # Order models to avoid foreign key constraint issues
        # We'll delete in reverse order of dependencies
        ordered_models = [
            'SubmittedAssignment',
            'StudentAttendance',
            'Attendance',
            'Grade',
            'FeePayment',
            'Timetable',
            'Assignment',
            'FeeStructure',
            'Report',
            'Activity',
            'Program',
            'Project',
            'Task',
            'Leave',
            'Holiday',
            'Issue',
            'Notice',
            'Award',
            'Document',
            'TransportDetails',
            'IDCard',
            'FinanceTransaction',
            'FormerMember',
            'Student',
            'Teacher',
            'Principal',
            'Management',
            'Admin',
            'Parent',
            'Class',
            'Subject',
            'Department',
            'User',
        ]
        
        # Delete records in the specified order
        with transaction.atomic():
            for model_name in ordered_models:
                try:
                    model = next((m for m in school_models if m.__name__ == model_name), None)
                    if model:
                        count = model.objects.all().count()
                        model.objects.all().delete()
                        self.stdout.write(f'Deleted {count} records from {model_name}')
                except Exception as e:
                    self.stdout.write(f'Error deleting records from {model_name}: {e}')
                    continue
        
        self.stdout.write(self.style.SUCCESS('Successfully cleared all data.'))
        
        # Add a small delay to ensure deletion is complete
        import time
        time.sleep(2)
        
        # Verify that all data is cleared
        self.stdout.write('Verifying data is cleared...')
        for model_name in ordered_models:
            try:
                model = next((m for m in school_models if m.__name__ == model_name), None)
                if model:
                    count = model.objects.all().count()
                    self.stdout.write(f'{model_name}: {count} records remaining')
            except Exception as e:
                self.stdout.write(f'Error checking {model_name}: {e}')
                continue
        
        # Now populate with exactly 5 records for each model
        self.stdout.write('Starting to populate database with exactly 5 records for each model...')
        
        # Create 5 departments
        departments = []
        dept_names = ['Mathematics', 'Science', 'English', 'History', 'Art']
        for i, name in enumerate(dept_names):
            dept = Department.objects.create(
                department_name=name,
                description=f'Department of {name}'
            )
            departments.append(dept)
            self.stdout.write(f"Created department: {name}")
        
        # Create 5 classes
        classes = []
        class_data = [('1st Grade', 'A'), ('2nd Grade', 'B'), ('3rd Grade', 'A'), ('4th Grade', 'B'), ('5th Grade', 'A')]
        for i, (class_name, sec) in enumerate(class_data):
            cls = Class.objects.create(
                class_name=class_name,
                sec=sec
            )
            classes.append(cls)
            self.stdout.write(f"Created class: {class_name} {sec}")
        
        # Create 5 subjects
        subjects = []
        subject_data = [('Mathematics', 'MATH101'), ('Science', 'SCI101'), ('English', 'ENG101'), ('History', 'HIST101'), ('Art', 'ART101')]
        for i, (name, code) in enumerate(subject_data):
            subj = Subject.objects.create(
                subject_name=name,
                subject_code=code,
                description=f'Subject of {name}'
            )
            subjects.append(subj)
            self.stdout.write(f"Created subject: {name} ({code})")
        
        # Create 5 users (one of each role)
        users = []
        user_data = [
            ('student@example.com', 'Student'),
            ('teacher@example.com', 'Teacher'),
            ('principal@example.com', 'Principal'),
            ('management@example.com', 'Management'),
            ('admin@example.com', 'Admin'),
        ]
        
        for i, (email, role) in enumerate(user_data):
            try:
                user = User.objects.create(
                    email=email,
                    role=role,
                    is_approved=True,
                    is_active=True,
                    is_staff=role in ['Admin', 'Principal', 'Management'],
                )
                user.set_password('password123')
                user.save()
                users.append(user)
                self.stdout.write(f"Created user: {email} ({role})")
            except Exception as e:
                self.stdout.write(f'Error creating user {email}: {e}')
                continue
        
        # Create 5 students
        students = []
        student_names = ['John Doe', 'Jane Smith', 'Alice Johnson', 'Bob Wilson', 'Charlie Brown']
        student_users = [u for u in users if u.role == 'Student']
        for i, name in enumerate(student_names):
            if student_users:
                user = student_users[0]  # Reuse the student user
                try:
                    student = Student.objects.create(
                        email=user,
                        fullname=name,
                        student_id=f'STD{i+1:03d}',
                        phone=f'+123456789{i:02d}',
                        date_of_birth='2010-01-01',
                        gender=random.choice(['Male', 'Female']),
                        admission_date='2020-01-01',
                        class_id=classes[i % len(classes)],
                        profile_picture='https://example.com/profile.jpg',
                        residential_address=f'{i+1} Main Street, City',
                        emergency_contact_name=f'Emergency Contact {i+1}',
                        emergency_contact_relationship='Parent',
                        emergency_contact_no=f'+987654321{i:02d}',
                        nationality='Indian',
                        father_name=f'Father of {name}',
                        mother_name=f'Mother of {name}',
                        blood_group=random.choice(['A+', 'B+', 'O+', 'AB+']),
                    )
                    students.append(student)
                    self.stdout.write(f"Created student: {name}")
                except Exception as e:
                    self.stdout.write(f'Error creating student {name}: {e}')
                    continue
        
        # Create 5 parents
        parents = []
        parent_names = ['John Doe Sr.', 'Jane Smith Sr.', 'Alice Johnson Sr.', 'Bob Wilson Sr.', 'Charlie Brown Sr.']
        parent_users = [u for u in users if u.role == 'Parent']
        # Create a parent user if we don't have one
        if not parent_users:
            parent_user = User.objects.create(
                email='parent@example.com',
                role='Parent',
                is_approved=True,
                is_active=True,
            )
            parent_user.set_password('password123')
            parent_user.save()
            parent_users.append(parent_user)
            users.append(parent_user)
            
        for i, name in enumerate(parent_names):
            user = parent_users[0]  # Use the same parent user for all
            try:
                parent = Parent.objects.create(
                    email=user,
                    fullname=name,
                    phone=f'+123456789{i:02d}',
                    occupation=random.choice(['Engineer', 'Doctor', 'Teacher', 'Businessman']),
                    residential_address=f'{i+1} Main Street, City',
                    profile_picture='https://example.com/profile.jpg',
                    relationship_to_student='Father' if i % 2 == 0 else 'Mother',
                )
                parents.append(parent)
                self.stdout.write(f"Created parent: {name}")
            except Exception as e:
                self.stdout.write(f'Error creating parent {name}: {e}')
                continue
        
        # Link students to parents
        for i, student in enumerate(students):
            if parents:
                student.parent = parents[i % len(parents)]
                student.save()
                self.stdout.write(f"Linked student {student.fullname} to parent {parents[i % len(parents)].fullname}")
        
        # Create 5 teachers
        teachers = []
        teacher_names = ['Michael Brown', 'Sarah Davis', 'Robert Miller', 'Emily Wilson', 'David Johnson']
        teacher_users = [u for u in users if u.role == 'Teacher']
        # Create a teacher user if we don't have one
        if not teacher_users:
            teacher_user = User.objects.create(
                email='teacher2@example.com',
                role='Teacher',
                is_approved=True,
                is_active=True,
            )
            teacher_user.set_password('password123')
            teacher_user.save()
            teacher_users.append(teacher_user)
            users.append(teacher_user)
            
        for i, name in enumerate(teacher_names):
            user = teacher_users[0] if teacher_users else users[0]  # Use available user
            try:
                teacher = Teacher.objects.create(
                    email=user,
                    fullname=name,
                    teacher_id=f'TCHR{i+1:03d}',
                    phone=f'+123456789{i:02d}',
                    date_of_birth='1980-01-01',
                    gender=random.choice(['Male', 'Female']),
                    date_joined='2010-01-01',
                    department=departments[i % len(departments)],
                    qualification=random.choice(['B.Ed', 'M.Ed', 'PhD']),
                    experience_years=5,
                    profile_picture='https://example.com/profile.jpg',
                    residential_address=f'{i+1} Teacher Street, City',
                    emergency_contact_name=f'Emergency Contact {i+1}',
                    emergency_contact_relationship='Spouse',
                    emergency_contact_no=f'+987654321{i:02d}',
                    nationality='Indian',
                    blood_group=random.choice(['A+', 'B+', 'O+', 'AB+']),
                    is_classteacher=i < 2,
                    class_id=classes[i % len(classes)] if i < 2 else None,
                    sec=classes[i % len(classes)].sec if i < 2 and classes else 'A',
                )
                teachers.append(teacher)
                self.stdout.write(f"Created teacher: {name}")
            except Exception as e:
                self.stdout.write(f'Error creating teacher {name}: {e}')
                continue
        
        # Create 5 assignments
        assignments = []
        for i in range(5):
            if subjects and teachers:
                try:
                    assignment = Assignment.objects.create(
                        title=f'Assignment {i+1}',
                        subject=subjects[i % len(subjects)],
                        description=f'Description for assignment {i+1}',
                        assigned_by=teachers[i % len(teachers)].email if teachers else None,
                        due_date='2025-12-31',
                        attachment='https://example.com/assignment.pdf',
                        status=random.choice(['Assigned', 'In Progress', 'Submitted', 'Graded', 'Late']),
                    )
                    assignments.append(assignment)
                    self.stdout.write(f"Created assignment: {assignment.title}")
                except Exception as e:
                    self.stdout.write(f'Error creating assignment: {e}')
                    continue
        
        self.stdout.write(
            self.style.SUCCESS('Successfully cleared all data and populated database with exactly 5 records for each model!')
        )