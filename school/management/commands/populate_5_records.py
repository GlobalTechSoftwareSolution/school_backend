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
    Attendance, StudentAttendance, Grade, FeeStructure, FeePayment, Timetable, Assignment, SubmittedAssignment, FormerMember,
    Document, Award, Notice, Issue, Holiday, Leave, Task, Project, Program, Activity,
    Report, FinanceTransaction, TransportDetails, IDCard
)

# Define IST timezone for Indian Standard Time
IST = pytz.timezone("Asia/Kolkata")

User = get_user_model()

class Command(BaseCommand):
    help = 'Populate database with exactly 5 records for each model'

    def handle(self, *args, **options):
        self.stdout.write('Starting to populate database with exactly 5 records for each model...')
        
        # Create 5 departments
        departments = []
        dept_names = ['Mathematics', 'Science', 'English', 'History', 'Art']
        for i, name in enumerate(dept_names):
            dept, created = Department.objects.get_or_create(
                department_name=name,
                defaults={'description': f'Department of {name}'}
            )
            departments.append(dept)
            self.stdout.write(f"Department {'created' if created else 'already exists'}: {name}")
        
        # Create 5 classes
        classes = []
        class_data = [('1st Grade', 'A'), ('2nd Grade', 'B'), ('3rd Grade', 'A'), ('4th Grade', 'B'), ('5th Grade', 'A')]
        for i, (class_name, sec) in enumerate(class_data):
            cls, created = Class.objects.get_or_create(
                class_name=class_name,
                sec=sec,
                defaults={'created_at': timezone.now().astimezone(IST), 'updated_at': timezone.now().astimezone(IST)}
            )
            classes.append(cls)
            self.stdout.write(f"Class {'created' if created else 'already exists'}: {class_name} {sec}")
        
        # Create 5 subjects
        subjects = []
        subject_data = [('Mathematics', 'MATH101'), ('Science', 'SCI101'), ('English', 'ENG101'), ('History', 'HIST101'), ('Art', 'ART101')]
        for i, (name, code) in enumerate(subject_data):
            subj, created = Subject.objects.get_or_create(
                subject_name=name,
                subject_code=code,
                defaults={'description': f'Subject of {name}'}
            )
            subjects.append(subj)
            self.stdout.write(f"Subject {'created' if created else 'already exists'}: {name} ({code})")
        
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
                self.stdout.write(f"User {'created' if created else 'already exists'}: {email} ({role})")
            except Exception as e:
                self.stdout.write(f'Error creating user {email}: {e}')
                continue
        
        # Create 5 students
        students = []
        student_names = ['John Doe', 'Jane Smith', 'Alice Johnson', 'Bob Wilson', 'Charlie Brown']
        student_users = [u for u in users if u.role == 'Student']
        for i, name in enumerate(student_names):
            if i >= len(student_users):
                break
            user = student_users[i] if i < len(student_users) else student_users[0]  # Reuse first student user if needed
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
                        'class_id': classes[i % len(classes)] if classes else None,
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
                self.stdout.write(f"Student {'created' if created else 'already exists'}: {name}")
            except Exception as e:
                self.stdout.write(f'Error creating student {name}: {e}')
                continue
        
        # Create 5 parents
        parents = []
        parent_names = ['John Doe Sr.', 'Jane Smith Sr.', 'Alice Johnson Sr.', 'Bob Wilson Sr.', 'Charlie Brown Sr.']
        parent_users = [u for u in users if u.role == 'Parent']
        # Create a parent user if we don't have one
        if not parent_users:
            parent_user, created = User.objects.get_or_create(
                email='parent@example.com',
                defaults={
                    'role': 'Parent',
                    'is_approved': True,
                    'is_active': True,
                }
            )
            if created:
                password = str(config('DEFAULT_USER_PASSWORD', default='password123'))
                parent_user.set_password(password)
                parent_user.save()
            parent_users.append(parent_user)
            users.append(parent_user)
            
        for i, name in enumerate(parent_names):
            user = parent_users[0]  # Use the same parent user for all
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
                self.stdout.write(f"Parent {'created' if created else 'already exists'}: {name}")
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
        if not teacher_users and users:
            teacher_user, created = User.objects.get_or_create(
                email='teacher2@example.com',
                defaults={
                    'role': 'Teacher',
                    'is_approved': True,
                    'is_active': True,
                }
            )
            if created:
                password = str(config('DEFAULT_USER_PASSWORD', default='password123'))
                teacher_user.set_password(password)
                teacher_user.save()
            teacher_users.append(teacher_user)
            users.append(teacher_user)
            
        for i, name in enumerate(teacher_names):
            user = teacher_users[0] if teacher_users else users[0]  # Use available user
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
                        'department': departments[i % len(departments)] if departments else None,
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
                        'class_id': classes[i % len(classes)] if classes and i < 2 else None,
                    }
                )
                # Set sec field based on class
                if teacher.class_id:
                    teacher.sec = teacher.class_id.sec
                else:
                    teacher.sec = 'A'  # Default section
                teacher.save()
                teachers.append(teacher)
                self.stdout.write(f"Teacher {'created' if created else 'already exists'}: {name}")
            except Exception as e:
                self.stdout.write(f'Error creating teacher {name}: {e}')
                continue
        
        # Create 5 principals
        principal_users = [u for u in users if u.role == 'Principal']
        if principal_users:
            for i in range(5):
                try:
                    principal, created = Principal.objects.get_or_create(
                        email=principal_users[0],
                        defaults={
                            'fullname': f'Dr. Principal Name {i+1}',
                            'phone': f'+123456789{i:02d}',
                            'date_of_birth': timezone.now().astimezone(IST).date() - timedelta(days=365*45),
                            'date_joined': timezone.now().astimezone(IST).date() - timedelta(days=365*5),
                            'qualification': 'PhD in Education',
                            'total_experience': Decimal('20.0'),
                            'bio': f'Experienced educational leader {i+1}',
                            'profile_picture': 'https://example.com/profile.jpg',
                            'office_address': f'Principal Office {i+1}, School Building',
                        }
                    )
                    self.stdout.write(f"Principal {'created' if created else 'already exists'}: {principal.fullname}")
                    break  # Only create one principal
                except Exception as e:
                    self.stdout.write(f'Error creating principal: {e}')
                    break
        
        # Create 5 management staff
        management_users = [u for u in users if u.role == 'Management']
        if management_users:
            for i in range(5):
                try:
                    management, created = Management.objects.get_or_create(
                        email=management_users[0],
                        defaults={
                            'fullname': f'Management Staff {i+1}',
                            'phone': f'+123456789{i:02d}',
                            'designation': f'Manager {i+1}',
                            'date_of_birth': timezone.now().astimezone(IST).date() - timedelta(days=365*35),
                            'date_joined': timezone.now().astimezone(IST).date() - timedelta(days=365*3),
                            'department': departments[i % len(departments)] if departments else None,
                            'profile_picture': 'https://example.com/profile.jpg',
                            'office_address': f'Management Office {i+1}, School Building',
                        }
                    )
                    self.stdout.write(f"Management {'created' if created else 'already exists'}: {management.fullname}")
                except Exception as e:
                    self.stdout.write(f'Error creating management: {e}')
        
        # Create 5 admins
        admin_users = [u for u in users if u.role == 'Admin']
        if admin_users:
            for i in range(5):
                try:
                    admin, created = Admin.objects.get_or_create(
                        email=admin_users[0],
                        defaults={
                            'fullname': f'Admin Name {i+1}',
                            'phone': f'+123456789{i:02d}',
                            'office_address': f'Admin Office {i+1}, School Building',
                            'profile_picture': 'https://example.com/profile.jpg',
                        }
                    )
                    self.stdout.write(f"Admin {'created' if created else 'already exists'}: {admin.fullname}")
                except Exception as e:
                    self.stdout.write(f'Error creating admin: {e}')
        
        # Create 5 attendance records
        for i in range(5):
            if students:
                try:
                    attendance, created = Attendance.objects.get_or_create(
                        user=students[i % len(students)].email,
                        date=timezone.now().astimezone(IST).date() - timedelta(days=i),
                        defaults={
                            'check_in': (timezone.now() - timedelta(hours=i)).astimezone(IST).time(),
                            'status': random.choice(['Present', 'Absent', 'Late']),
                            'role': 'Student',
                            'remarks': f'Attendance record {i+1}',
                        }
                    )
                    self.stdout.write(f"Attendance {'created' if created else 'already exists'}: {attendance.user.email} on {attendance.date}")
                except Exception as e:
                    self.stdout.write(f'Error creating attendance: {e}')
                    continue
        
        # Create 5 student attendance records
        for i in range(5):
            if students and subjects and teachers and classes:
                try:
                    student_attendance, created = StudentAttendance.objects.get_or_create(
                        student=students[i % len(students)],
                        subject=subjects[i % len(subjects)],
                        teacher=teachers[i % len(teachers)],
                        class_id=classes[i % len(classes)],
                        date=timezone.now().astimezone(IST).date() - timedelta(days=i),
                        defaults={
                            'status': random.choice(['Present', 'Absent', 'Late', 'Excused']),
                        }
                    )
                    self.stdout.write(f"StudentAttendance {'created' if created else 'already exists'}: {student_attendance.student.fullname}")
                except Exception as e:
                    self.stdout.write(f'Error creating student attendance: {e}')
                    continue
        
        # Create 5 grades
        for i in range(5):
            if students and subjects and teachers:
                try:
                    grade, created = Grade.objects.get_or_create(
                        student=students[i % len(students)],
                        subject=subjects[i % len(subjects)],
                        teacher=teachers[i % len(teachers)],
                        exam_type=random.choice(['Quiz', 'Midterm', 'Final', 'Assignment', 'Project']),
                        defaults={
                            'marks_obtained': Decimal(random.randint(60, 100)),
                            'total_marks': Decimal(100),
                            'exam_date': timezone.now().astimezone(IST).date() - timedelta(days=i*5),
                            'remarks': f'Grade record {i+1}',
                        }
                    )
                    self.stdout.write(f"Grade {'created' if created else 'already exists'}: {grade.student.fullname}")
                except Exception as e:
                    self.stdout.write(f'Error creating grade: {e}')
                    continue
        
        # Create 5 fee structures
        for i in range(5):
            try:
                fee_structure, created = FeeStructure.objects.get_or_create(
                    class_id=classes[i % len(classes)] if classes else None,
                    fee_type=random.choice(['Tuition', 'Transport', 'Library', 'Sports', 'Lab', 'Other']),
                    defaults={
                        'amount': Decimal(random.randint(500, 5000)),
                        'frequency': random.choice(['Monthly', 'Quarterly', 'Annually', 'One-time']),
                        'description': f'Fee structure {i+1}',
                    }
                )
                self.stdout.write(f"FeeStructure {'created' if created else 'already exists'}: {fee_structure.fee_type}")
            except Exception as e:
                self.stdout.write(f'Error creating fee structure: {e}')
                continue
        
        # Create 5 fee payments
        for i in range(5):
            if students:
                try:
                    fee_payment, created = FeePayment.objects.get_or_create(
                        student=students[i % len(students)],
                        amount_paid=Decimal(random.randint(500, 5000)),
                        payment_date=timezone.now().astimezone(IST).date() - timedelta(days=i*10),
                        defaults={
                            'total_amount': Decimal(random.randint(500, 5000)),
                            'remaining_amount': Decimal(0),
                            'payment_method': random.choice(['Cash', 'Card', 'Bank Transfer', 'Online Payment', 'Cheque']),
                            'transaction_id': f'TRANS{i+1:05d}',
                            'status': 'Paid',
                            'remarks': f'Fee payment {i+1}',
                        }
                    )
                    self.stdout.write(f"FeePayment {'created' if created else 'already exists'}: {fee_payment.student.fullname}")
                except Exception as e:
                    self.stdout.write(f'Error creating fee payment: {e}')
                    continue
        
        # Create 5 timetable entries
        for i in range(5):
            if classes and subjects and teachers:
                try:
                    timetable, created = Timetable.objects.get_or_create(
                        class_id=classes[i % len(classes)],
                        subject=subjects[i % len(subjects)],
                        teacher=teachers[i % len(teachers)],
                        day_of_week=random.choice(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']),
                        defaults={
                            'start_time': (timezone.now() + timedelta(hours=i)).time(),
                            'end_time': (timezone.now() + timedelta(hours=i+1)).time(),
                            'room_number': f'Room {i+1:03d}',
                        }
                    )
                    self.stdout.write(f"Timetable {'created' if created else 'already exists'}: {timetable.class_id.class_name}")
                except Exception as e:
                    self.stdout.write(f'Error creating timetable: {e}')
                    continue
        
        # Create 5 assignments
        assignments = []
        for i in range(5):
            if subjects and teachers:
                try:
                    assignment, created = Assignment.objects.get_or_create(
                        title=f'Assignment {i+1}',
                        subject=subjects[i % len(subjects)],
                        defaults={
                            'description': f'Description for assignment {i+1}',
                            'assigned_by': teachers[i % len(teachers)].email if teachers else None,
                            'due_date': timezone.now().astimezone(IST).date() + timedelta(days=7+i),
                            'attachment': 'https://example.com/assignment.pdf',
                            'status': random.choice(['Assigned', 'In Progress', 'Submitted', 'Graded', 'Late']),
                        }
                    )
                    assignments.append(assignment)
                    self.stdout.write(f"Assignment {'created' if created else 'already exists'}: {assignment.title}")
                except Exception as e:
                    self.stdout.write(f'Error creating assignment: {e}')
                    continue
        
        # Create 5 submitted assignments
        for i in range(5):
            if students and assignments:
                try:
                    submitted_assignment, created = SubmittedAssignment.objects.get_or_create(
                        assignment=assignments[i % len(assignments)],
                        student=students[i % len(students)],
                        defaults={
                            'submission_file': 'https://example.com/submission.pdf',
                            'submission_date': timezone.now().astimezone(IST) - timedelta(days=i),
                            'grade': Decimal(random.randint(60, 100)),
                            'feedback': f'Good work on assignment {i+1}',
                            'is_late': i % 3 == 0,
                        }
                    )
                    self.stdout.write(f"SubmittedAssignment {'created' if created else 'already exists'}: {submitted_assignment.assignment.title}")
                except Exception as e:
                    self.stdout.write(f'Error creating submitted assignment: {e}')
                    continue
        
        # Create 5 documents
        for i in range(5):
            if users:
                try:
                    document, created = Document.objects.get_or_create(
                        email=users[i % len(users)],
                        defaults={
                            'tenth': 'https://example.com/10th_marks_card.pdf',
                            'twelth': 'https://example.com/12th_marks_card.pdf',
                            'degree': 'https://example.com/degree_certificate.pdf',
                            'marks_card': 'https://example.com/marks_card.pdf',
                            'certificates': 'https://example.com/certificates.pdf',
                        }
                    )
                    self.stdout.write(f"Document {'created' if created else 'already exists'}: {document.email.email}")
                except Exception as e:
                    self.stdout.write(f'Error creating document: {e}')
                    continue
        
        # Create 5 awards
        for i in range(5):
            if users:
                try:
                    award, created = Award.objects.get_or_create(
                        email=users[i % len(users)],
                        title=f'Award {i+1}',
                        defaults={
                            'description': f'Description for award {i+1}',
                            'photo': 'https://example.com/award_photo.jpg',
                        }
                    )
                    self.stdout.write(f"Award {'created' if created else 'already exists'}: {award.title}")
                except Exception as e:
                    self.stdout.write(f'Error creating award: {e}')
                    continue
        
        # Create 5 notices
        for i in range(5):
            if users:
                try:
                    notice, created = Notice.objects.get_or_create(
                        title=f'Notice {i+1}',
                        defaults={
                            'message': f'Message for notice {i+1}',
                            'email': users[i % len(users)],
                            'posted_date': timezone.now().astimezone(IST) - timedelta(days=i),
                            'valid_until': timezone.now().astimezone(IST) + timedelta(days=30),
                            'important': i % 2 == 0,
                            'attachment': 'https://example.com/notice_attachment.pdf',
                        }
                    )
                    self.stdout.write(f"Notice {'created' if created else 'already exists'}: {notice.title}")
                except Exception as e:
                    self.stdout.write(f'Error creating notice: {e}')
                    continue
        
        # Create 5 issues
        for i in range(5):
            if users:
                try:
                    issue, created = Issue.objects.get_or_create(
                        subject=f'Issue {i+1}',
                        defaults={
                            'status': random.choice(['Open', 'In Progress', 'Closed']),
                            'description': f'Description for issue {i+1}',
                            'priority': random.choice(['Low', 'Medium', 'High', 'Urgent']),
                            'created_at': timezone.now().astimezone(IST) - timedelta(days=i),
                            'updated_at': timezone.now().astimezone(IST) - timedelta(days=i//2),
                            'closed_description': f'Closed description for issue {i+1}' if i % 3 == 0 else None,
                            'raised_by': users[i % len(users)],
                        }
                    )
                    self.stdout.write(f"Issue {'created' if created else 'already exists'}: {issue.subject}")
                except Exception as e:
                    self.stdout.write(f'Error creating issue: {e}')
                    continue
        
        # Create 5 holidays
        for i in range(5):
            try:
                holiday_date = timezone.now().astimezone(IST).date() + timedelta(days=30+i*5)
                holiday, created = Holiday.objects.get_or_create(
                    date=holiday_date,
                    country='India',
                    defaults={
                        'name': f'Holiday {i+1}',
                        'type': random.choice(['National', 'Regional', 'School', 'Religious']),
                        'year': holiday_date.year,
                        'month': holiday_date.month,
                    }
                )
                self.stdout.write(f"Holiday {'created' if created else 'already exists'}: {holiday.name}")
            except Exception as e:
                self.stdout.write(f'Error creating holiday: {e}')
                continue
        
        # Create 5 leaves
        for i in range(5):
            if users:
                try:
                    leave, created = Leave.objects.get_or_create(
                        applicant=users[i % len(users)],
                        leave_type=random.choice(['Sick', 'Casual', 'Vacation', 'Other']),
                        start_date=timezone.now().astimezone(IST).date() + timedelta(days=10+i),
                        end_date=timezone.now().astimezone(IST).date() + timedelta(days=12+i),
                        defaults={
                            'reason': f'Reason for leave {i+1}',
                            'status': random.choice(['Pending', 'Approved', 'Rejected']),
                        }
                    )
                    self.stdout.write(f"Leave {'created' if created else 'already exists'}: {leave.applicant.email}")
                except Exception as e:
                    self.stdout.write(f'Error creating leave: {e}')
                    continue
        
        # Create 5 tasks
        for i in range(5):
            if users:
                try:
                    task, created = Task.objects.get_or_create(
                        title=f'Task {i+1}',
                        defaults={
                            'description': f'Description for task {i+1}',
                            'assigned_to': users[i % len(users)],
                            'status': random.choice(['Todo', 'In Progress', 'Done']),
                            'priority': random.choice(['Low', 'Medium', 'High', 'Urgent']),
                            'due_date': timezone.now().astimezone(IST).date() + timedelta(days=7+i),
                        }
                    )
                    self.stdout.write(f"Task {'created' if created else 'already exists'}: {task.title}")
                except Exception as e:
                    self.stdout.write(f'Error creating task: {e}')
                    continue
        
        # Create 5 projects
        for i in range(5):
            if users:
                try:
                    project, created = Project.objects.get_or_create(
                        title=f'Project {i+1}',
                        defaults={
                            'description': f'Description for project {i+1}',
                            'start_date': timezone.now().astimezone(IST).date() - timedelta(days=30),
                            'end_date': timezone.now().astimezone(IST).date() + timedelta(days=30),
                            'status': random.choice(['Planned', 'In Progress', 'Completed', 'On Hold', 'Cancelled']),
                            'owner': users[i % len(users)],
                        }
                    )
                    self.stdout.write(f"Project {'created' if created else 'already exists'}: {project.title}")
                except Exception as e:
                    self.stdout.write(f'Error creating project: {e}')
                    continue
        
        # Create 5 programs
        for i in range(5):
            if users:
                try:
                    program, created = Program.objects.get_or_create(
                        name=f'Program {i+1}',
                        defaults={
                            'description': f'Description for program {i+1}',
                            'start_date': timezone.now().astimezone(IST).date() - timedelta(days=60),
                            'end_date': timezone.now().astimezone(IST).date() + timedelta(days=60),
                            'coordinator': users[i % len(users)],
                            'status': random.choice(['Planned', 'Active', 'Completed', 'Cancelled']),
                        }
                    )
                    self.stdout.write(f"Program {'created' if created else 'already exists'}: {program.name}")
                except Exception as e:
                    self.stdout.write(f'Error creating program: {e}')
                    continue
        
        # Create 5 activities
        for i in range(5):
            if users:
                try:
                    activity, created = Activity.objects.get_or_create(
                        name=f'Activity {i+1}',
                        defaults={
                            'description': f'Description for activity {i+1}',
                            'type': random.choice(['Sports', 'Cultural', 'Academic', 'Other']),
                            'date': timezone.now().astimezone(IST).date() + timedelta(days=i*3),
                            'conducted_by': users[i % len(users)],
                            'attachment': 'https://example.com/activity_attachment.pdf',
                        }
                    )
                    self.stdout.write(f"Activity {'created' if created else 'already exists'}: {activity.name}")
                except Exception as e:
                    self.stdout.write(f'Error creating activity: {e}')
                    continue
        
        # Create 5 reports
        for i in range(5):
            if students:
                try:
                    report, created = Report.objects.get_or_create(
                        title=f'Report {i+1}',
                        defaults={
                            'description': f'Description for report {i+1}',
                            'report_type': random.choice(['General', 'Academic', 'Behavior', 'Finance', 'Other']),
                            'student': students[i % len(students)],
                            'created_by': users[0] if users else None,
                            'file_url': 'https://example.com/report_file.pdf',
                        }
                    )
                    self.stdout.write(f"Report {'created' if created else 'already exists'}: {report.title}")
                except Exception as e:
                    self.stdout.write(f'Error creating report: {e}')
                    continue
        
        # Create 5 finance transactions
        for i in range(5):
            if users:
                try:
                    finance_transaction, created = FinanceTransaction.objects.get_or_create(
                        date=timezone.now().astimezone(IST).date() - timedelta(days=i*2),
                        amount=Decimal(random.randint(1000, 10000)),
                        type=random.choice(['Income', 'Expense']),
                        category=random.choice(['Tuition', 'Transport', 'Salaries', 'Supplies', 'Maintenance', 'Other']),
                        defaults={
                            'description': f'Description for finance transaction {i+1}',
                            'reference_id': f'REF{i+1:05d}',
                            'recorded_by': users[i % len(users)],
                        }
                    )
                    self.stdout.write(f"FinanceTransaction {'created' if created else 'already exists'}: {finance_transaction.type}")
                except Exception as e:
                    self.stdout.write(f'Error creating finance transaction: {e}')
                    continue
        
        # Create 5 transport details
        for i in range(5):
            if users:
                try:
                    transport_details, created = TransportDetails.objects.get_or_create(
                        user=users[i % len(users)],
                        defaults={
                            'route_name': f'Route {i+1}',
                            'bus_number': f'BUS{i+1:03d}',
                            'pickup_point': f'Pickup Point {i+1}',
                            'drop_point': f'Drop Point {i+1}',
                            'driver_name': f'Driver {i+1}',
                            'driver_phone': f'+123456789{i:02d}',
                            'transport_fee': Decimal(random.randint(500, 2000)),
                        }
                    )
                    self.stdout.write(f"TransportDetails {'created' if created else 'already exists'}: {transport_details.user.email}")
                except Exception as e:
                    self.stdout.write(f'Error creating transport details: {e}')
                    continue
        
        # Create 5 ID cards
        for i in range(5):
            if users:
                try:
                    id_card, created = IDCard.objects.get_or_create(
                        user=users[i % len(users)],
                        defaults={
                            'id_card_url': 'https://example.com/id_card.pdf',
                        }
                    )
                    self.stdout.write(f"IDCard {'created' if created else 'already exists'}: {id_card.user.email}")
                except Exception as e:
                    self.stdout.write(f'Error creating ID card: {e}')
                    continue
        
        self.stdout.write(
            self.style.SUCCESS('Successfully populated database with exactly 5 records for each model!')
        )