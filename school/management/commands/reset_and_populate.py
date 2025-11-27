import random
from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import transaction, connection
from django.contrib.auth import get_user_model
from school.models import *

User = get_user_model()

class Command(BaseCommand):
    help = 'Reset database and populate with exactly 5 records for each model'

    def handle(self, *args, **options):
        self.stdout.write('Starting to reset database...')
        
        # Truncate all tables using raw SQL
        with connection.cursor() as cursor:
            # Get all table names from the school app
            school_models = apps.get_app_config('school').get_models()
            table_names = [model._meta.db_table for model in school_models]
            
            # Also add the user table
            table_names.append(User._meta.db_table)
            
            # Truncate all tables
            for table_name in table_names:
                try:
                    cursor.execute(f'TRUNCATE TABLE "{table_name}" RESTART IDENTITY CASCADE')
                    self.stdout.write(f'Truncated table: {table_name}')
                except Exception as e:
                    self.stdout.write(f'Error truncating table {table_name}: {e}')
                    continue
        
        self.stdout.write(self.style.SUCCESS('Successfully reset database.'))
        
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
        
        # Create 5 users for students (different emails)
        student_users = []
        for i in range(5):
            try:
                user = User.objects.create(
                    email=f'student{i+1}@test.com',
                    role='Student',
                    is_approved=True,
                    is_active=True,
                )
                user.set_password('password123')
                user.save()
                student_users.append(user)
                self.stdout.write(f"Created student user: student{i+1}@test.com")
            except Exception as e:
                self.stdout.write(f'Error creating student user {i+1}: {e}')
                continue
        
        # Create 5 users for teachers (different emails)
        teacher_users = []
        for i in range(5):
            try:
                user = User.objects.create(
                    email=f'teacher{i+1}@test.com',
                    role='Teacher',
                    is_approved=True,
                    is_active=True,
                    is_staff=True,
                )
                user.set_password('password123')
                user.save()
                teacher_users.append(user)
                self.stdout.write(f"Created teacher user: teacher{i+1}@test.com")
            except Exception as e:
                self.stdout.write(f'Error creating teacher user {i+1}: {e}')
                continue
        
        # Create users for other roles
        other_roles = ['Principal', 'Management', 'Admin']
        other_users = {}
        for i, role in enumerate(other_roles):
            try:
                user = User.objects.create(
                    email=f'{role.lower()}@test.com',
                    role=role,
                    is_approved=True,
                    is_active=True,
                    is_staff=True,
                )
                user.set_password('password123')
                user.save()
                other_users[role] = user
                self.stdout.write(f"Created {role.lower()} user: {role.lower()}@test.com")
            except Exception as e:
                self.stdout.write(f'Error creating {role.lower()} user: {e}')
                continue
        
        # Create a parent user
        try:
            parent_user = User.objects.create(
                email='parent@test.com',
                role='Parent',
                is_approved=True,
                is_active=True,
            )
            parent_user.set_password('password123')
            parent_user.save()
            self.stdout.write(f"Created parent user: parent@test.com")
        except Exception as e:
            self.stdout.write(f'Error creating parent user: {e}')
        
        # Create 5 students
        students = []
        student_names = ['John Doe', 'Jane Smith', 'Alice Johnson', 'Bob Wilson', 'Charlie Brown']
        for i, name in enumerate(student_names):
            if i < len(student_users):
                user = student_users[i]
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
        for i, name in enumerate(parent_names):
            try:
                parent = Parent.objects.create(
                    email=parent_user,  # Using the same parent user for all parents
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
        for i, name in enumerate(teacher_names):
            if i < len(teacher_users):
                user = teacher_users[i]
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
                        experience_years=random.randint(2, 15),
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
            self.style.SUCCESS('Successfully reset database and populated with exactly 5 records for each model!')
        )