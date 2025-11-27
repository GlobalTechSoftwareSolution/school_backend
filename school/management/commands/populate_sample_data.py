import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import pytz
from decouple import config
from school.models import (
    Department, Class, Subject, Student, Teacher, Principal, Management, Admin, Parent,
    Attendance, Grade, FeeStructure, FeePayment, Timetable, Assignment, FormerMember,
    Document, Award, Notice, Issue, Holiday, Leave, Task, Project, Program, Activity,
    Report, FinanceTransaction, TransportDetails
)

# Define IST timezone for Indian Standard Time
IST = pytz.timezone("Asia/Kolkata")

User = get_user_model()

class Command(BaseCommand):
    help = 'Populate database with sample data ensuring no null values where possible'

    def handle(self, *args, **options):
        self.stdout.write('Starting to populate database with sample data...')
        
        # Create departments
        departments = []
        dept_names = ['Mathematics', 'Science', 'English', 'History', 'Art', 'Physical Education']
        for name in dept_names:
            dept, created = Department.objects.get_or_create(
                department_name=name,
                defaults={'description': f'Department of {name}'}
            )
            departments.append(dept)
        
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
        
        # Create users
        users = []
        user_data = [
            ('student1@example.com', 'Student'),
            ('student2@example.com', 'Student'),
            ('teacher1@example.com', 'Teacher'),
            ('teacher2@example.com', 'Teacher'),
            ('principal1@example.com', 'Principal'),
            ('management1@example.com', 'Management'),
            ('admin1@example.com', 'Admin'),
            ('parent1@example.com', 'Parent'),
        ]
        
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
                    password = str(config('DEFAULT_USER_PASSWORD', default='password123'))
                    user.set_password(password)
                    user.save()
                users.append(user)
            except Exception as e:
                self.stdout.write(f'Error creating user {email}: {e}')
                continue
        
        # Create students
        students = []
        student_names = ['John Doe', 'Jane Smith', 'Alice Johnson', 'Bob Wilson']
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
            except Exception as e:
                self.stdout.write(f'Error creating student {name}: {e}')
                continue
        
        # Create parents
        parents = []
        parent_names = ['John Doe Sr.', 'Jane Smith Sr.', 'Alice Johnson Sr.', 'Bob Wilson Sr.']
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
                        'occupation': random.choice(['Engineer', 'Doctor', 'Teacher', 'Businessman']),
                        'residential_address': f'{i+1} Main Street, City',
                        'profile_picture': 'https://example.com/profile.jpg',
                        'relationship_to_student': 'Father' if i % 2 == 0 else 'Mother',
                    }
                )
                parents.append(parent)
            except Exception as e:
                self.stdout.write(f'Error creating parent {name}: {e}')
                continue
        
        # Link students to parents
        for student in students:
            if parents:
                student.parent = random.choice(parents)
                student.save()
        
        # Create teachers
        teachers = []
        teacher_names = ['Michael Brown', 'Sarah Davis', 'Robert Miller', 'Emily Wilson']
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
            except Exception as e:
                self.stdout.write(f'Error creating teacher {name}: {e}')
                continue
        
        # Assign class teachers
        for cls in classes[:2]:  # First 2 classes
            if teachers:
                cls.class_teacher = teachers[0]  # Assign first teacher as class teacher
                cls.save()
        
        # Create principal
        principal_user = next((u for u in users if u.role == 'Principal'), None)
        if principal_user:
            try:
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
            except Exception as e:
                self.stdout.write(f'Error creating principal: {e}')
        
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
            except Exception as e:
                self.stdout.write(f'Error creating management: {e}')
        
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
            except Exception as e:
                self.stdout.write(f'Error creating admin: {e}')
        
        # Create attendance records for students
        for student in students:
            try:
                attendance, created = Attendance.objects.get_or_create(
                    user=student.email,  # Use the user field instead of student
                    date=timezone.now().astimezone(IST).date(),
                    defaults={
                        'check_in': timezone.now().astimezone(IST).time(),
                        'status': 'Present',
                        'role': 'Student',  # Set the role explicitly
                        'remarks': 'Regular attendance',
                    }
                )
            except Exception as e:
                self.stdout.write(f'Error creating attendance for {student.fullname}: {e}')
                continue
                
        # Create attendance records for teachers
        for teacher in teachers:
            try:
                attendance, created = Attendance.objects.get_or_create(
                    user=teacher.email,  # Use the user field instead of student
                    date=timezone.now().astimezone(IST).date(),
                    defaults={
                        'check_in': timezone.now().astimezone(IST).time(),
                        'status': 'Present',
                        'role': 'Teacher',  # Set the role explicitly
                        'remarks': 'Regular attendance',
                    }
                )
            except Exception as e:
                self.stdout.write(f'Error creating attendance for teacher {teacher.fullname}: {e}')
                continue
                
        # Create attendance records for principal
        principal_user = next((u for u in users if u.role == 'Principal'), None)
        if principal_user:
            try:
                principal = Principal.objects.get(email=principal_user)
                attendance, created = Attendance.objects.get_or_create(
                    user=principal_user,
                    date=timezone.now().astimezone(IST).date(),
                    defaults={
                        'check_in': timezone.now().astimezone(IST).time(),
                        'status': 'Present',
                        'role': 'Principal',
                        'remarks': 'Regular attendance',
                    }
                )
            except Exception as e:
                self.stdout.write(f'Error creating attendance for principal: {e}')
                
        # Create attendance records for management
        management_user = next((u for u in users if u.role == 'Management'), None)
        if management_user:
            try:
                management = Management.objects.get(email=management_user)
                attendance, created = Attendance.objects.get_or_create(
                    user=management_user,
                    date=timezone.now().astimezone(IST).date(),
                    defaults={
                        'check_in': timezone.now().astimezone(IST).time(),
                        'status': 'Present',
                        'role': 'Management',
                        'remarks': 'Regular attendance',
                    }
                )
            except Exception as e:
                self.stdout.write(f'Error creating attendance for management: {e}')
                
        # Create attendance records for admin
        admin_user = next((u for u in users if u.role == 'Admin'), None)
        if admin_user:
            try:
                admin = Admin.objects.get(email=admin_user)
                attendance, created = Attendance.objects.get_or_create(
                    user=admin_user,
                    date=timezone.now().astimezone(IST).date(),
                    defaults={
                        'check_in': timezone.now().astimezone(IST).time(),
                        'status': 'Present',
                        'role': 'Admin',
                        'remarks': 'Regular attendance',
                    }
                )
            except Exception as e:
                self.stdout.write(f'Error creating attendance for admin: {e}')
        
        # Create grades
        for student in students:
            for subject in subjects[:3]:  # First 3 subjects
                try:
                    grade, created = Grade.objects.get_or_create(
                        student=student,
                        subject=subject,
                        exam_type='Midterm',
                        defaults={
                            'marks_obtained': Decimal(random.randint(60, 95)),
                            'total_marks': Decimal(100),
                            'exam_date': timezone.now().astimezone(IST).date() - timedelta(days=10),
                            'remarks': 'Good performance',
                        }
                    )
                except Exception as e:
                    self.stdout.write(f'Error creating grade for {student.fullname} in {subject.subject_name}: {e}')
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
            except Exception as e:
                self.stdout.write(f'Error creating fee structure for {cls.class_name} {cls.sec}: {e}')
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
                        'due_date': timezone.now().astimezone(IST).date() + timedelta(days=7),
                        'attachment': 'https://example.com/assignment.pdf',
                        'status': 'Assigned',
                    }
                )
            except Exception as e:
                self.stdout.write(f'Error creating assignment for {subject.subject_name}: {e}')
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
                except Exception as e:
                    self.stdout.write(f'Error creating timetable for {cls.class_name} {cls.sec} - {subject.subject_name}: {e}')
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
        except Exception as e:
            self.stdout.write(f'Error creating notice: {e}')
        
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
            except Exception as e:
                self.stdout.write(f'Error creating document for {student.fullname}: {e}')
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
            except Exception as e:
                self.stdout.write(f'Error creating award for {student.fullname}: {e}')
                continue
        
        self.stdout.write(
            self.style.SUCCESS('Successfully populated database with sample data')
        )