"""
Script to populate all database tables with sample data.
Run this script using: python manage.py shell < populate_db.py
or: python populate_db.py (if Django setup is included)
"""

import os
import django
from datetime import date, time, timedelta
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_backend.settings')
django.setup()

from school.models import (
    User, Department, Subject, Student, Teacher, Principal,
    Management, Admin, Parent, Attendance, Grade, FeeStructure,
    FeePayment, Timetable, FormerMember, Document, Notice, Issue, Award,
    Assignment, Leave, Task, Project, Program, Activity, Report, FinanceTransaction, TransportDetails,
)

def populate_database():
    print("Starting database population...")
    
    # Clear existing data (optional - comment out if you want to keep existing data)
    print("\nClearing existing data...")
    Timetable.objects.all().delete()
    FeePayment.objects.all().delete()
    FeeStructure.objects.all().delete()
    Grade.objects.all().delete()
    Attendance.objects.all().delete()
    Student.objects.all().delete()
    Teacher.objects.all().delete()
    Principal.objects.all().delete()
    Management.objects.all().delete()
    Admin.objects.all().delete()
    Parent.objects.all().delete()
    Subject.objects.all().delete()
    Department.objects.all().delete()
    User.objects.filter(is_superuser=False).delete()
    
    # 1. Create Departments
    print("\n1. Creating Departments...")
    departments_data = [
        {"department_name": "Science", "description": "Science Department covering Physics, Chemistry, Biology"},
        {"department_name": "Mathematics", "description": "Mathematics and Statistics Department"},
        {"department_name": "Languages", "description": "English, Hindi and other language courses"},
        {"department_name": "Social Studies", "description": "History, Geography, Civics"},
        {"department_name": "Arts", "description": "Music, Drawing, Crafts"},
        {"department_name": "Physical Education", "description": "Sports and Physical Training"},
        {"department_name": "Administration", "description": "Administrative staff department"},
    ]
    departments = {}
    for dept_data in departments_data:
        dept, created = Department.objects.get_or_create(
            department_name=dept_data["department_name"],
            defaults=dept_data
        )
        departments[dept.department_name] = dept
        print(f"   {'Created' if created else 'Found existing'}: {dept}")
    
    # 2. Define Classes (in-memory only for assigning strings)
    print("\n2. Defining Classes (string fields)...")
    classes_data = [
        {"class_name": "Grade 1", "section": "A"},
        {"class_name": "Grade 1", "section": "B"},
        {"class_name": "Grade 5", "section": "A"},
        {"class_name": "Grade 8", "section": "A"},
        {"class_name": "Grade 10", "section": "A"},
        {"class_name": "Grade 12 Science", "section": None},
    ]
    classes = {f"{c['class_name']}": c for c in classes_data}
    for c in classes_data:
        print(f"   Defined: {c['class_name']} {c['section'] or ''}")
    
    # 3. Create Subjects
    print("\n3. Creating Subjects...")
    subjects_data = [
        {"subject_name": "Mathematics", "subject_code": "MATH101", "description": "Basic Mathematics"},
        {"subject_name": "Physics", "subject_code": "PHY101", "description": "Introduction to Physics"},
        {"subject_name": "Chemistry", "subject_code": "CHEM101", "description": "Basic Chemistry"},
        {"subject_name": "Biology", "subject_code": "BIO101", "description": "Life Sciences"},
        {"subject_name": "English", "subject_code": "ENG101", "description": "English Language and Literature"},
        {"subject_name": "Hindi", "subject_code": "HIN101", "description": "Hindi Language"},
        {"subject_name": "History", "subject_code": "HIST101", "description": "World History"},
        {"subject_name": "Geography", "subject_code": "GEO101", "description": "Physical and Human Geography"},
        {"subject_name": "Computer Science", "subject_code": "CS101", "description": "Introduction to Computing"},
        {"subject_name": "Physical Education", "subject_code": "PE101", "description": "Sports and Fitness"},
    ]
    subjects = {}
    for subj_data in subjects_data:
        subj, created = Subject.objects.get_or_create(
            subject_code=subj_data["subject_code"],
            defaults=subj_data
        )
        subjects[subj.subject_code] = subj
        print(f"   {'Created' if created else 'Found existing'}: {subj}")
    
    # 4. Create Admin User
    print("\n4. Creating Admin...")
    admin_user, created = User.objects.get_or_create(
        email="admin@school.com",
        defaults={
            "role": "Admin",
            "is_approved": True,
            "is_staff": True
        }
    )
    if created:
        admin_user.set_password("admin123")
        admin_user.save()
    
    admin_profile, created = Admin.objects.get_or_create(
        email=admin_user,
        defaults={
            "fullname": "System Administrator",
            "phone": "+1-555-0001",
            "office_address": "Admin Building, Room 101",
            "profile_picture": "https://i.pravatar.cc/150?img=1"
        }
    )
    print(f"   {'Created' if created else 'Found existing'}: {admin_profile}")
    
    # 5. Create Principal
    print("\n5. Creating Principal...")
    principal_user, created = User.objects.get_or_create(
        email="principal@school.com",
        defaults={
            "role": "Principal",
            "is_approved": True
        }
    )
    if created:
        principal_user.set_password("principal123")
        principal_user.save()
    
    principal_profile, created = Principal.objects.get_or_create(
        email=principal_user,
        defaults={
            "fullname": "Dr. Sarah Johnson",
            "phone": "+1-555-0002",
            "date_of_birth": date(1975, 5, 15),
            "date_joined": date(2015, 1, 1),
            "qualification": "Ph.D. in Education",
            "total_experience": Decimal("25.0"),
            "bio": "Experienced educator with a passion for student development",
            "profile_picture": "https://i.pravatar.cc/150?img=2",
            "office_address": "Principal's Office, Main Building"
        }
    )
    print(f"   {'Created' if created else 'Found existing'}: {principal_profile}")
    
    # 6. Create Management Staff
    print("\n6. Creating Management Staff...")
    management_data = [
        {
            "email": "hr@school.com",
            "fullname": "Michael Brown",
            "designation": "HR Manager",
            "department": departments["Administration"],
            "phone": "+1-555-0003",
            "date_of_birth": date(1980, 3, 20),
            "date_joined": date(2018, 6, 1),
        },
        {
            "email": "finance@school.com",
            "fullname": "Jennifer Davis",
            "designation": "Finance Manager",
            "department": departments["Administration"],
            "phone": "+1-555-0004",
            "date_of_birth": date(1982, 8, 10),
            "date_joined": date(2019, 1, 15),
        },
    ]
    for mgmt_data in management_data:
        dept = mgmt_data.pop("department")
        email = mgmt_data.pop("email")  # Remove email from dict
        
        mgmt_user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "role": "Management",
                "is_approved": True
            }
        )
        if created:
            mgmt_user.set_password("management123")
            mgmt_user.save()
        
        mgmt_profile, created = Management.objects.get_or_create(
            email=mgmt_user,
            defaults={
                "department": dept,
                "profile_picture": "https://i.pravatar.cc/150?img=3",
                "office_address": "Admin Building",
                **mgmt_data
            }
        )
        # Update existing management if needed
        if not created:
            mgmt_profile.department = dept
            for key, value in mgmt_data.items():
                setattr(mgmt_profile, key, value)
            mgmt_profile.save()
        
        print(f"   {'Created' if created else 'Updated'}: {mgmt_profile}")
    
    # 7. Create Teachers
    print("\n7. Creating Teachers...")
    teachers_data = [
        {
            "email": "john.smith@school.com",
            "fullname": "John Smith",
            "teacher_id": "T001",
            "department": departments["Mathematics"],
            "subjects": ["MATH101"],
            "phone": "+1-555-1001",
            "date_of_birth": date(1985, 4, 12),
            "gender": "Male",
            "date_joined": date(2020, 8, 1),
            "qualification": "M.Sc. Mathematics",
            "experience_years": Decimal("8.5"),
        },
        {
            "email": "emily.wilson@school.com",
            "fullname": "Emily Wilson",
            "teacher_id": "T002",
            "department": departments["Science"],
            "subjects": ["PHY101", "CHEM101"],
            "phone": "+1-555-1002",
            "date_of_birth": date(1987, 7, 22),
            "gender": "Female",
            "date_joined": date(2019, 7, 15),
            "qualification": "M.Sc. Physics",
            "experience_years": Decimal("10.0"),
        },
        {
            "email": "david.lee@school.com",
            "fullname": "David Lee",
            "teacher_id": "T003",
            "department": departments["Science"],
            "subjects": ["BIO101"],
            "phone": "+1-555-1003",
            "date_of_birth": date(1990, 1, 5),
            "gender": "Male",
            "date_joined": date(2021, 6, 1),
            "qualification": "M.Sc. Biology",
            "experience_years": Decimal("5.5"),
        },
        {
            "email": "lisa.anderson@school.com",
            "fullname": "Lisa Anderson",
            "teacher_id": "T004",
            "department": departments["Languages"],
            "subjects": ["ENG101", "HIN101"],
            "phone": "+1-555-1004",
            "date_of_birth": date(1988, 11, 30),
            "gender": "Female",
            "date_joined": date(2020, 1, 10),
            "qualification": "M.A. English Literature",
            "experience_years": Decimal("7.0"),
        },
        {
            "email": "robert.taylor@school.com",
            "fullname": "Robert Taylor",
            "teacher_id": "T005",
            "department": departments["Social Studies"],
            "subjects": ["HIST101", "GEO101"],
            "phone": "+1-555-1005",
            "date_of_birth": date(1986, 6, 18),
            "gender": "Male",
            "date_joined": date(2018, 9, 1),
            "qualification": "M.A. History",
            "experience_years": Decimal("12.0"),
        },
    ]
    teachers = {}
    for teacher_data in teachers_data:
        subject_codes = teacher_data.pop("subjects")
        dept = teacher_data.pop("department")
        email = teacher_data.pop("email")  # Remove email from dict
        teacher_id = teacher_data["teacher_id"]
        
        teacher_user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "role": "Teacher",
                "is_approved": True
            }
        )
        if created:
            teacher_user.set_password("teacher123")
            teacher_user.save()
        
        teacher_profile, created = Teacher.objects.get_or_create(
            email=teacher_user,
            defaults={
                "department": dept,
                "profile_picture": "https://i.pravatar.cc/150?img=10",
                "residential_address": "123 Teacher Lane, City",
                "emergency_contact_name": "Emergency Contact",
                "emergency_contact_relationship": "Spouse",
                "emergency_contact_no": "+1-555-9999",
                "nationality": "USA",
                "blood_group": "O+",
                **teacher_data
            }
        )
        # Update existing teacher if needed
        if not created:
            teacher_profile.department = dept
            for key, value in teacher_data.items():
                setattr(teacher_profile, key, value)
            teacher_profile.save()
        
        # Add subjects
        teacher_profile.subjects.clear()
        for code in subject_codes:
            teacher_profile.subjects.add(subjects[code])
        
        teachers[teacher_id] = teacher_profile
        print(f"   {'Created' if created else 'Updated'}: {teacher_profile}")
    
    # 8. Create Parents
    print("\n8. Creating Parents...")
    parents_data = [
        {
            "email": "parent1@example.com",
            "fullname": "Richard Miller",
            "phone": "+1-555-2001",
            "occupation": "Engineer",
            "relationship_to_student": "Father",
        },
        {
            "email": "parent2@example.com",
            "fullname": "Susan Miller",
            "phone": "+1-555-2002",
            "occupation": "Doctor",
            "relationship_to_student": "Mother",
        },
        {
            "email": "parent3@example.com",
            "fullname": "James Williams",
            "phone": "+1-555-2003",
            "occupation": "Business Owner",
            "relationship_to_student": "Father",
        },
        {
            "email": "parent4@example.com",
            "fullname": "Mary Garcia",
            "phone": "+1-555-2004",
            "occupation": "Teacher",
            "relationship_to_student": "Mother",
        },
    ]
    parents = {}
    for parent_data in parents_data:
        email = parent_data.pop("email")  # Remove email from dict
        
        parent_user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "role": "Parent",
                "is_approved": True
            }
        )
        if created:
            parent_user.set_password("parent123")
            parent_user.save()
        
        parent_profile, created = Parent.objects.get_or_create(
            email=parent_user,
            defaults={
                "profile_picture": "https://i.pravatar.cc/150?img=20",
                "residential_address": "456 Parent Street, City",
                **parent_data
            }
        )
        parents[email] = parent_profile
        print(f"   {'Created' if created else 'Found existing'}: {parent_profile}")
    
    # 9. Create Students
    print("\n9. Creating Students...")
    students_data = [
        {
            "email": "student1@school.com",
            "fullname": "Test Student One",
            "student_id": "S001",
            "parent": parents["parent1@example.com"],
            "class_name": "Grade 10",
            "section": "A",
            "phone": "+1-555-3001",
            "date_of_birth": date(2010, 3, 15),
            "gender": "Female",
            "admission_date": date(2022, 8, 1),
            "father_name": "Richard Miller",
            "mother_name": "Susan Miller",
        },
        {
            "email": "alice.miller@student.school.com",
            "fullname": "Alice Miller",
            "student_id": "S002",
            "parent": parents["parent1@example.com"],
            "class_name": "Grade 10",
            "section": "A",
            "phone": "+1-555-3001",
            "date_of_birth": date(2010, 3, 15),
            "gender": "Female",
            "admission_date": date(2022, 8, 1),
            "father_name": "Richard Miller",
            "mother_name": "Susan Miller",
        },
        {
            "email": "bob.miller@student.school.com",
            "fullname": "Bob Miller",
            "student_id": "S003",
            "parent": parents["parent2@example.com"],
            "class_name": "Grade 8",
            "section": "A",
            "phone": "+1-555-3002",
            "date_of_birth": date(2012, 6, 20),
            "gender": "Male",
            "admission_date": date(2023, 8, 1),
            "father_name": "Richard Miller",
            "mother_name": "Susan Miller",
        },
        {
            "email": "charlie.williams@student.school.com",
            "fullname": "Charlie Williams",
            "student_id": "S004",
            "parent": parents["parent3@example.com"],
            "class_name": "Grade 12 Science",
            "section": None,
            "phone": "+1-555-3003",
            "date_of_birth": date(2008, 9, 10),
            "gender": "Male",
            "admission_date": date(2020, 8, 1),
            "father_name": "James Williams",
            "mother_name": "Mary Garcia",
        },
        {
            "email": "diana.garcia@student.school.com",
            "fullname": "Diana Garcia",
            "student_id": "S005",
            "parent": parents["parent4@example.com"],
            "class_name": classes["Grade 5"]["class_name"],
            "section": "A",
            "phone": "+1-555-3004",
            "date_of_birth": date(2015, 12, 5),
            "gender": "Female",
            "admission_date": date(2021, 8, 1),
            "father_name": "Richard Garcia",
            "mother_name": "Mary Garcia",
        },
        {
            "email": "edward.brown@student.school.com",
            "fullname": "Edward Brown",
            "student_id": "S006",
            "parent": parents["parent1@example.com"],
            "class_name": "Grade 1",
            "section": "A",
            "phone": "+1-555-3005",
            "date_of_birth": date(2019, 2, 28),
            "gender": "Male",
            "admission_date": date(2024, 8, 1),
            "father_name": "Richard Miller",
            "mother_name": "Susan Miller",
        },
    ]
    students = {}
    for student_data in students_data:
        parent = student_data.pop("parent")
        class_name_val = student_data.pop("class_name")
        section_val = student_data.pop("section")
        email = student_data.pop("email")  # Remove email from dict
        student_id = student_data["student_id"]
        
        # Set password same as email for student1@school.com
        password = email if email == "student1@school.com" else "student123"
        
        student_user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "role": "Student",
                "is_approved": True
            }
        )
        if created:
            student_user.set_password(password)
            student_user.save()
        else:
            # Update password for existing student1@school.com
            if email == "student1@school.com":
                student_user.set_password(password)
                student_user.save()
        
        student_profile, created = Student.objects.get_or_create(
            email=student_user,
            defaults={
                "parent": parent,
                "class_name": class_name_val,
                "section": section_val,
                "profile_picture": "https://i.pravatar.cc/150?img=30",
                "residential_address": "789 Student Avenue, City",
                "emergency_contact_name": "Emergency Contact",
                "emergency_contact_relationship": "Parent",
                "emergency_contact_no": "+1-555-9999",
                "nationality": "USA",
                "blood_group": "A+",
                **student_data
            }
        )
        # Update existing student if needed
        if not created:
            student_profile.class_name = class_name_val
            student_profile.section = section_val
            student_profile.parent = parent
            for key, value in student_data.items():
                setattr(student_profile, key, value)
            student_profile.save()
        
        students[student_id] = student_profile
        print(f"   {'Created' if created else 'Updated'}: {student_profile}")
    
    # 10. Create Attendance Records
    print("\n10. Creating Attendance Records...")
    attendance_count = 0
    for student in students.values():
        if not student.class_name:
            print(f"   Skipping attendance for {student.fullname} - no class assigned")
            continue
        for i in range(10):  # Last 10 days
            attendance_date = date.today() - timedelta(days=i)
            status = "Present" if i % 4 != 0 else "Absent"  # Mostly present
            Attendance.objects.get_or_create(
                student=student,
                date=attendance_date,
                defaults={
                    "class_name": student.class_name,
                    "status": status,
                    "remarks": "Regular attendance" if status == "Present" else "Absent without notice"
                }
            )
            attendance_count += 1
    print(f"   Created/verified {attendance_count} attendance records")
    
    # 11. Create Grades
    print("\n11. Creating Grades...")
    exam_types = ['Quiz', 'Midterm', 'Final', 'Assignment']
    grade_count = 0
    for student in students.values():
        # Each student gets grades in 5 subjects
        for subject in list(subjects.values())[:5]:
            for exam_type in exam_types:
                _, created = Grade.objects.get_or_create(
                    student=student,
                    subject=subject,
                    exam_type=exam_type,
                    exam_date=date.today() - timedelta(days=30),
                    defaults={
                        "teacher": teachers["T001"],  # Assign to first teacher
                        "marks_obtained": Decimal(str(70 + (hash(str(student.email) + subject.subject_code + exam_type) % 25))),
                        "total_marks": Decimal("100.00"),
                        "remarks": "Good performance"
                    }
                )
                if created:
                    grade_count += 1
    print(f"   Created {grade_count} new grade records")
    
    # 12. Create Fee Structures
    print("\n12. Creating Fee Structures...")
    fee_count = 0
    for cls in classes.values():
        fee_types = [
            ("Tuition", Decimal("5000.00"), "Monthly"),
            ("Transport", Decimal("1000.00"), "Monthly"),
            ("Library", Decimal("500.00"), "Annually"),
            ("Sports", Decimal("300.00"), "Quarterly"),
            ("Lab", Decimal("800.00"), "Quarterly"),
        ]
        for fee_type, amount, frequency in fee_types:
            _, created = FeeStructure.objects.get_or_create(
                class_name=cls["class_name"],
                fee_type=fee_type,
                defaults={
                    "amount": amount,
                    "frequency": frequency,
                    "description": f"{fee_type} fee for {cls['class_name']}"
                }
            )
            if created:
                fee_count += 1
    print(f"   Created {fee_count} new fee structures")
    
    # 13. Create Fee Payments
    print("\n13. Creating Fee Payments...")
    payment_count = 0
    for student in students.values():
        if not student.class_name:
            continue
        fee_structures = FeeStructure.objects.filter(class_name=student.class_name)
        for idx, fee_struct in enumerate(fee_structures[:3]):  # First 3 fees
            _, created = FeePayment.objects.get_or_create(
                student=student,
                fee_structure=fee_struct,
                transaction_id=f"TXN{student.student_id}{idx:03d}",
                defaults={
                    "amount_paid": fee_struct.amount,
                    "payment_date": date.today() - timedelta(days=15),
                    "payment_method": "Online",
                    "status": "Paid",
                    "remarks": "Payment received successfully"
                }
            )
            if created:
                payment_count += 1
    print(f"   Created {payment_count} new fee payment records")
    
    # 14. Create Timetable
    print("\n14. Creating Timetable...")
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    time_slots = [
        (time(9, 0), time(10, 0)),
        (time(10, 0), time(11, 0)),
        (time(11, 0), time(12, 0)),
        (time(13, 0), time(14, 0)),
        (time(14, 0), time(15, 0)),
    ]
    
    timetable_count = 0
    for cls in list(classes.values())[:3]:  # First 3 classes
        subject_list = list(subjects.values())[:5]
        teacher_list = list(teachers.values())
        
        for day_idx, day in enumerate(days):
            for slot_idx, (start, end) in enumerate(time_slots):
                _, created = Timetable.objects.get_or_create(
                    class_name=cls["class_name"],
                    day_of_week=day,
                    start_time=start,
                    defaults={
                        "subject": subject_list[slot_idx % len(subject_list)],
                        "teacher": teacher_list[slot_idx % len(teacher_list)],
                        "end_time": end,
                        "room_number": f"Room {100 + slot_idx}"
                    }
                )
                if created:
                    timetable_count += 1
    print(f"   Created {timetable_count} new timetable entries")
    
    # 15. Create Former Members
    print("\n15. Creating Former Members...")
    former_members_data = [
        {
            "email": "former.student@school.com",
            "fullname": "Tom Harrison",
            "role": "Student",
            "student_id": "S999",
            "phone": "+1-555-9001",
            "date_of_birth": date(2009, 5, 10),
            "gender": "Male",
            "admission_date": date(2019, 8, 1),
            "class_name": "Grade 10",
            "reason": "Transferred to another school",
        },
        {
            "email": "former.teacher@school.com",
            "fullname": "Patricia Johnson",
            "role": "Teacher",
            "teacher_id": "T999",
            "phone": "+1-555-9002",
            "date_of_birth": date(1983, 8, 15),
            "gender": "Female",
            "date_joined": date(2015, 9, 1),
            "department_name": "Mathematics",
            "qualification": "M.Sc. Mathematics",
            "experience_years": Decimal("15.0"),
            "reason": "Retired",
        },
    ]
    for fm_data in former_members_data:
        _, created = FormerMember.objects.get_or_create(
            email=fm_data["email"],
            defaults=fm_data
        )
        print(f"   {'Created' if created else 'Found existing'} former member: {fm_data['fullname']}")
    
    # 16. Create Documents (for some users)
    print("\n16. Creating Documents...")
    doc_targets = [
        ("student1@school.com", {
            "tenth": "https://example.com/docs/student1/tenth.pdf",
            "twelth": "https://example.com/docs/student1/twelth.pdf",
            "id_proof": "https://example.com/docs/student1/id.pdf",
        }),
        ("john.smith@school.com", {
            "degree": "https://example.com/docs/teacher1/degree.pdf",
            "resume": "https://example.com/docs/teacher1/resume.pdf",
        }),
        ("principal@school.com", {
            "masters": "https://example.com/docs/principal/masters.pdf",
            "achievement_crt": "https://example.com/docs/principal/award.pdf",
        }),
    ]
    for email, fields in doc_targets:
        try:
            usr = User.objects.get(email=email)
            Document.objects.update_or_create(
                email=usr,
                defaults=fields
            )
            print(f"   Upserted documents for {email}")
        except User.DoesNotExist:
            print(f"   Skipped documents for missing user: {email}")

    # 17. Create Notices
    print("\n17. Creating Notices...")
    notice_defs = [
        {
            "title": "PTM Scheduled",
            "message": "Parent-Teacher meeting on 10th Nov at 10 AM.",
            "email": admin_user,
            "important": True,
            "notice_by": principal_user,
            "notice_to": None,
        },
        {
            "title": "Science Fair",
            "message": "Annual Science Fair next week.",
            "email": None,
            "important": False,
            "notice_by": teachers["T001"].email if "teachers" in locals() and "T001" in teachers else None,
            "notice_to": None,
        },
    ]
    for nd in notice_defs:
        Notice.objects.get_or_create(
            title=nd["title"],
            defaults=nd
        )
        print(f"   Ensured notice: {nd['title']}")

    # 18. Create Issues
    print("\n18. Creating Issues...")
    mgmt_first = Management.objects.first()
    mgmt_user = mgmt_first.email if mgmt_first else admin_user
    issue_defs = [
        {
            "subject": "Classroom Projector Not Working",
            "status": "Open",
            "description": "Projector in Room 101 fails to start.",
            "priority": "High",
            "raised_by": teachers["T001"].email if "teachers" in locals() and "T001" in teachers else admin_user,
            "raised_to": mgmt_user,
        },
        {
            "subject": "Library Books Request",
            "status": "In Progress",
            "description": "Need new science journals.",
            "priority": "Medium",
            "raised_by": principal_user,
            "raised_to": admin_user,
        },
    ]
    for idef in issue_defs:
        Issue.objects.get_or_create(
            subject=idef["subject"],
            defaults=idef
        )
        print(f"   Ensured issue: {idef['subject']}")

    # 19. Create Awards
    print("\n19. Creating Awards...")
    award_defs = [
        {"email": teachers["T001"].email if "teachers" in locals() and "T001" in teachers else admin_user, "title": "Best Teacher", "description": "Excellence in Mathematics", "photo": "https://example.com/awards/best-teacher.jpg"},
        {"email": principal_user, "title": "Leadership Excellence", "description": "Outstanding leadership", "photo": "https://example.com/awards/leadership.jpg"},
        {"email": admin_user, "title": "Service Award", "description": "Dedicated service to school", "photo": "https://example.com/awards/service.jpg"},
    ]
    for adef in award_defs:
        Award.objects.get_or_create(
            email=adef["email"],
            title=adef["title"],
            defaults={k: v for k, v in adef.items() if k not in ("email", "title")}
        )
        print(f"   Ensured award: {adef['title']}")

    # 20. Create Assignments
    print("\n20. Creating Assignments...")
    # Safely resolve teacher Users for assigned_by
    t001 = teachers.get("T001") if "teachers" in locals() else None
    t002 = teachers.get("T002") if "teachers" in locals() else None
    t001_user = t001.email if t001 is not None else None
    t002_user = t002.email if t002 is not None else None

    assignment_defs = [
        {
            "title": "Algebra Homework",
            "description": "Solve problems 1-10 from chapter 3",
            "subject": subjects.get("MATH101"),
            "class_name": "Grade 10",
            "assigned_by": t001_user,
            "due_date": date.today() + timedelta(days=5),
            "attachment": "https://example.com/assignments/algebra.pdf",
        },
        {
            "title": "Physics Lab Report",
            "description": "Write a report on motion experiment",
            "subject": subjects.get("PHY101"),
            "class_name": "Grade 10",
            "assigned_by": t002_user,
            "due_date": date.today() + timedelta(days=7),
        },
    ]
    for a in assignment_defs:
        if a["subject"] is None or a["assigned_by"] is None:
            continue
        Assignment.objects.get_or_create(
            title=a["title"],
            subject=a["subject"],
            due_date=a["due_date"],
            defaults={k: v for k, v in a.items() if k not in ("title", "subject", "due_date")}
        )

    # 21. Create Leaves
    print("\n21. Creating Leaves...")
    leave_defs = [
        {
            "applicant": User.objects.filter(email="student1@school.com").first(),
            "leave_type": "Sick",
            "start_date": date.today() + timedelta(days=1),
            "end_date": date.today() + timedelta(days=2),
            "reason": "Fever",
            "status": "Pending",
            "approved_by": principal_user,
        },
        {
            "applicant": User.objects.filter(email="john.smith@school.com").first(),
            "leave_type": "Casual",
            "start_date": date.today() + timedelta(days=3),
            "end_date": date.today() + timedelta(days=3),
            "reason": "Personal work",
            "status": "Approved",
            "approved_by": principal_user,
        },
    ]
    for l in leave_defs:
        if l["applicant"] is None:
            continue
        Leave.objects.get_or_create(
            applicant=l["applicant"],
            start_date=l["start_date"],
            end_date=l["end_date"],
            defaults={k: v for k, v in l.items() if k not in ("applicant", "start_date", "end_date")}
        )

    # 22. Create Tasks
    print("\n22. Creating Tasks...")
    task_defs = [
        {
            "title": "Prepare Lab Equipment",
            "description": "Set up physics lab for Monday",
            "assigned_to": User.objects.filter(email="john.smith@school.com").first(),
            "created_by": admin_user,
            "status": "Todo",
            "priority": "High",
            "due_date": date.today() + timedelta(days=2),
        },
        {
            "title": "Update Math Syllabus",
            "assigned_to": User.objects.filter(email="john.smith@school.com").first(),
            "created_by": principal_user,
            "status": "In Progress",
            "priority": "Medium",
            "due_date": date.today() + timedelta(days=10),
        },
        {
            "title": "Organize PTA Meeting",
            "assigned_to": principal_user,
            "created_by": admin_user,
            "status": "Todo",
            "priority": "Urgent",
            "due_date": date.today() + timedelta(days=7),
        },
    ]
    for t in task_defs:
        if t["assigned_to"] is None or t["created_by"] is None:
            continue
        Task.objects.get_or_create(
            title=t["title"],
            assigned_to=t["assigned_to"],
            defaults={k: v for k, v in t.items() if k not in ("title", "assigned_to")}
        )

    # 23. Create Projects
    print("\n23. Creating Projects...")
    project_defs = [
        {
            "title": "Science Fair",
            "description": "Annual school science fair",
            "start_date": date.today() + timedelta(days=3),
            "end_date": date.today() + timedelta(days=10),
            "status": "Planned",
            "owner": admin_user,
            "class_name": "Grade 10",
            "section": "A",
        },
        {
            "title": "Math Olympiad Prep",
            "description": "Preparation sessions for math olympiad",
            "start_date": date.today(),
            "status": "In Progress",
            "owner": principal_user,
        },
    ]
    for p in project_defs:
        proj, created = Project.objects.get_or_create(
            title=p["title"],
            defaults=p,
        )
        if not created:
            for k, v in p.items():
                setattr(proj, k, v)
            proj.save()

    # 24. Create Programs
    print("\n24. Creating Programs...")
    program_defs = [
        {
            "name": "After School Tutoring",
            "description": "Extra help for students",
            "start_date": date.today() + timedelta(days=1),
            "status": "Active",
            "coordinator": principal_user,
        },
        {
            "name": "Sports Camp",
            "description": "Weekend sports activities",
            "start_date": date.today() + timedelta(days=14),
            "status": "Planned",
            "coordinator": admin_user,
        },
    ]
    for pr in program_defs:
        program, created = Program.objects.get_or_create(
            name=pr["name"],
            defaults=pr,
        )
        if not created:
            for k, v in pr.items():
                setattr(program, k, v)
            program.save()

    # 25. Create Activities
    print("\n25. Creating Activities...")
    activity_defs = [
        {
            "name": "Football Match",
            "description": "Inter-house football match",
            "type": "Sports",
            "date": date.today() + timedelta(days=5),
            "conducted_by": User.objects.filter(email="john.smith@school.com").first(),
            "class_name": "Grade 10",
            "section": "A",
        },
        {
            "name": "Debate Competition",
            "type": "Cultural",
            "date": date.today() + timedelta(days=8),
            "conducted_by": admin_user,
        },
    ]
    for ac in activity_defs:
        if ac["conducted_by"] is None:
            continue
        act, created = Activity.objects.get_or_create(
            name=ac["name"],
            date=ac.get("date"),
            defaults={k: v for k, v in ac.items() if k not in ("name", "date")},
        )
        if not created:
            for k, v in ac.items():
                if k not in ("name",):
                    setattr(act, k, v)
            act.save()

    # 26. Create Reports
    print("\n26. Creating Reports...")
    some_student = Student.objects.first()
    some_teacher = Teacher.objects.first()
    report_defs = [
        {
            "title": "Monthly Performance",
            "description": "Overall academic progress",
            "report_type": "Academic",
            "student": some_student,
            "teacher": some_teacher,
            "created_by": principal_user,
        },
        {
            "title": "Incident Report",
            "description": "Minor classroom incident",
            "report_type": "Behavior",
            "student": some_student,
            "teacher": some_teacher,
            "created_by": admin_user,
        },
    ]
    for rp in report_defs:
        report, created = Report.objects.get_or_create(
            title=rp["title"],
            created_by=rp["created_by"],
            defaults={k: v for k, v in rp.items() if k not in ("title", "created_by")},
        )
        if not created:
            for k, v in rp.items():
                if k not in ("title", "created_by"):
                    setattr(report, k, v)
            report.save()

    # 27. Create Finance Transactions
    print("\n27. Creating Finance Transactions...")
    finance_defs = [
        {
            "date": date.today(),
            "amount": Decimal("10000.00"),
            "type": "Income",
            "category": "Tuition",
            "description": "Tuition fee collection",
            "reference_id": "FIN-TUITION-001",
            "recorded_by": User.objects.filter(email="finance@school.com").first() or admin_user,
        },
        {
            "date": date.today(),
            "amount": Decimal("2500.00"),
            "type": "Expense",
            "category": "Supplies",
            "description": "Lab equipment purchase",
            "reference_id": "FIN-EXP-001",
            "recorded_by": User.objects.filter(email="finance@school.com").first() or admin_user,
        },
    ]
    for f in finance_defs:
        if f["recorded_by"] is None:
            continue
        ft, created = FinanceTransaction.objects.get_or_create(
            reference_id=f.get("reference_id"),
            defaults=f,
        )
        if not created:
            for k, v in f.items():
                setattr(ft, k, v)
            ft.save()

    # 28. Create Transport Details
    print("\n28. Creating Transport Details...")
    for st in Student.objects.all()[:2]:
        td, created = TransportDetails.objects.get_or_create(
            student=st,
            defaults={
                "route_name": "Route 1",
                "bus_number": "KA-01-1234",
                "pickup_point": "Main Gate",
                "drop_point": "City Park",
                "driver_name": "Ravi",
                "driver_phone": "+91-9999999999",
                "transport_fee": Decimal("1000.00"),
                "is_active": True,
            }
        )
        if not created:
            td.route_name = "Route 1"
            td.bus_number = "KA-01-1234"
            td.pickup_point = "Main Gate"
            td.drop_point = "City Park"
            td.driver_name = "Ravi"
            td.driver_phone = "+91-9999999999"
            td.transport_fee = Decimal("1000.00")
            td.is_active = True
            td.save()

    # Ensure any remaining null/empty fields get placeholder data
    try:
        backfill_null_fields()
    except Exception:
        pass

    print("\n" + "="*50)
    print("DATABASE POPULATION COMPLETED SUCCESSFULLY!")
    print("="*50)
    print("\nSummary:")
    print(f"  Users: {User.objects.count()}")
    print(f"  Departments: {Department.objects.count()}")
    print(f"  Subjects: {Subject.objects.count()}")
    print(f"  Students: {Student.objects.count()}")
    print(f"  Teachers: {Teacher.objects.count()}")
    print(f"  Parents: {Parent.objects.count()}")
    print(f"  Principal: {Principal.objects.count()}")
    print(f"  Management: {Management.objects.count()}")
    print(f"  Admin: {Admin.objects.count()}")
    print(f"  Attendance: {Attendance.objects.count()}")
    print(f"  Grades: {Grade.objects.count()}")
    print(f"  Fee Structures: {FeeStructure.objects.count()}")
    print(f"  Fee Payments: {FeePayment.objects.count()}")
    print(f"  Timetable: {Timetable.objects.count()}")
    print(f"  Former Members: {FormerMember.objects.count()}")
    print(f"  Documents: {Document.objects.count()}")
    print(f"  Notices: {Notice.objects.count()}")
    print(f"  Issues: {Issue.objects.count()}")
    print(f"  Awards: {Award.objects.count()}")
    print(f"  Assignments: {Assignment.objects.count()}")
    print(f"  Leaves: {Leave.objects.count()}")
    print(f"  Tasks: {Task.objects.count()}")
    print(f"  Projects: {Project.objects.count()}")
    print(f"  Programs: {Program.objects.count()}")
    print(f"  Activities: {Activity.objects.count()}")
    print(f"  Reports: {Report.objects.count()}")
    print(f"  Finance Transactions: {FinanceTransaction.objects.count()}")
    print(f"  Transport Details: {TransportDetails.objects.count()}")
    print("\nLogin Credentials:")
    print("  Admin: admin@school.com / admin123")
    print("  Principal: principal@school.com / principal123")
    print("  Teacher: john.smith@school.com / teacher123")
    print("  Student: student1@school.com / student1@school.com")
    print("  Parent: parent1@example.com / parent123")


if __name__ == "__main__":
    populate_database()


# Backfill helper to replace NULL/empty values safely
def backfill_null_fields():
    """
    Iterate over key tables and fill NULL/empty fields with raw placeholder data.
    Never overwrite non-empty values.
    Run with: python manage.py shell -c "from populate_db import backfill_null_fields; backfill_null_fields()"
    """
    from django.db.models import Q

    def set_if_missing(obj, field, value):
        current = getattr(obj, field, None)
        if current in (None, ""):
            setattr(obj, field, value)

    # Students: ensure contacts and parent names
    for s in Student.objects.all():
        if s.parent:
            # try to infer father/mother from parent's relationship if available
            rel = getattr(s.parent, 'relationship_to_student', None)
            if (rel or '').lower() == 'father':
                set_if_missing(s, 'father_name', s.parent.fullname)
            elif (rel or '').lower() == 'mother':
                set_if_missing(s, 'mother_name', s.parent.fullname)
            # emergency contacts from parent
            set_if_missing(s, 'emergency_contact_name', s.parent.fullname)
            set_if_missing(s, 'emergency_contact_relationship', rel or 'Parent')
            set_if_missing(s, 'emergency_contact_no', getattr(s.parent, 'phone', None) or '+1-555-0000')
        # generic fallbacks
        set_if_missing(s, 'father_name', 'Unknown Father')
        set_if_missing(s, 'mother_name', 'Unknown Mother')
        set_if_missing(s, 'phone', '+1-555-0100')
        set_if_missing(s, 'nationality', 'India')
        set_if_missing(s, 'blood_group', 'O+')
        set_if_missing(s, 'profile_picture', 'https://i.pravatar.cc/150?img=30')
        s.save()

    # Parents
    for p in Parent.objects.all():
        set_if_missing(p, 'phone', '+1-555-0200')
        set_if_missing(p, 'occupation', 'Self Employed')
        set_if_missing(p, 'residential_address', '123 Parent Street, City')
        set_if_missing(p, 'profile_picture', 'https://i.pravatar.cc/150?img=20')
        p.save()

    # Teachers
    for t in Teacher.objects.all():
        set_if_missing(t, 'phone', '+1-555-0300')
        set_if_missing(t, 'qualification', 'Graduate')
        set_if_missing(t, 'residential_address', '123 Teacher Lane, City')
        set_if_missing(t, 'emergency_contact_name', 'Emergency Contact')
        set_if_missing(t, 'emergency_contact_relationship', 'Spouse')
        set_if_missing(t, 'emergency_contact_no', '+1-555-9999')
        set_if_missing(t, 'nationality', 'India')
        set_if_missing(t, 'blood_group', 'O+')
        set_if_missing(t, 'profile_picture', 'https://i.pravatar.cc/150?img=10')
        t.save()

    # Principal
    for pr in Principal.objects.all():
        set_if_missing(pr, 'phone', '+1-555-0400')
        set_if_missing(pr, 'qualification', 'Masters')
        set_if_missing(pr, 'profile_picture', 'https://i.pravatar.cc/150?img=2')
        set_if_missing(pr, 'office_address', "Principal's Office, Main Building")
        pr.save()

    # Management
    for m in Management.objects.all():
        set_if_missing(m, 'phone', '+1-555-0500')
        set_if_missing(m, 'designation', 'Manager')
        set_if_missing(m, 'profile_picture', 'https://i.pravatar.cc/150?img=3')
        set_if_missing(m, 'office_address', 'Admin Building')
        m.save()

    # Admin
    for a in Admin.objects.all():
        set_if_missing(a, 'phone', '+1-555-0600')
        set_if_missing(a, 'office_address', 'Admin Building, Room 101')
        set_if_missing(a, 'profile_picture', 'https://i.pravatar.cc/150?img=1')
        a.save()

    # Transport Details
    for td in TransportDetails.objects.all():
        set_if_missing(td, 'route_name', 'Route 1')
        set_if_missing(td, 'bus_number', 'KA-01-1234')
        set_if_missing(td, 'pickup_point', 'Main Gate')
        set_if_missing(td, 'drop_point', 'City Park')
        set_if_missing(td, 'driver_name', 'Ravi')
        set_if_missing(td, 'driver_phone', '+91-9999999999')
        td.save()

    print('Backfill complete.')
