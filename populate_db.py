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
    User, Department, Class, Subject, Student, Teacher, Principal,
    Management, Admin, Parent, Attendance, Grade, FeeStructure,
    FeePayment, Timetable, FormerMember
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
    Class.objects.all().delete()
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
    
    # 2. Create Classes
    print("\n2. Creating Classes...")
    classes_data = [
        {"class_name": "Grade 1 A", "section": "A", "description": "First grade section A"},
        {"class_name": "Grade 1 B", "section": "B", "description": "First grade section B"},
        {"class_name": "Grade 5 A", "section": "A", "description": "Fifth grade section A"},
        {"class_name": "Grade 8 A", "section": "A", "description": "Eighth grade section A"},
        {"class_name": "Grade 10 A", "section": "A", "description": "Tenth grade section A"},
        {"class_name": "Grade 12 Science", "section": "Science", "description": "Twelfth grade Science stream"},
    ]
    classes = {}
    for cls_data in classes_data:
        cls, created = Class.objects.get_or_create(
            class_name=cls_data["class_name"],
            defaults=cls_data
        )
        classes[f"{cls_data['class_name']}"] = cls
        print(f"   {'Created' if created else 'Found existing'}: {cls}")
    
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
            "class_enrolled": classes["Grade 10 A"],
            "phone": "+1-555-3001",
            "date_of_birth": date(2010, 3, 15),
            "gender": "Female",
            "admission_date": date(2022, 8, 1),
        },
        {
            "email": "alice.miller@student.school.com",
            "fullname": "Alice Miller",
            "student_id": "S002",
            "parent": parents["parent1@example.com"],
            "class_enrolled": classes["Grade 10 A"],
            "phone": "+1-555-3001",
            "date_of_birth": date(2010, 3, 15),
            "gender": "Female",
            "admission_date": date(2022, 8, 1),
        },
        {
            "email": "bob.miller@student.school.com",
            "fullname": "Bob Miller",
            "student_id": "S003",
            "parent": parents["parent2@example.com"],
            "class_enrolled": classes["Grade 8 A"],
            "phone": "+1-555-3002",
            "date_of_birth": date(2012, 6, 20),
            "gender": "Male",
            "admission_date": date(2023, 8, 1),
        },
        {
            "email": "charlie.williams@student.school.com",
            "fullname": "Charlie Williams",
            "student_id": "S004",
            "parent": parents["parent3@example.com"],
            "class_enrolled": classes["Grade 12 Science"],
            "phone": "+1-555-3003",
            "date_of_birth": date(2008, 9, 10),
            "gender": "Male",
            "admission_date": date(2020, 8, 1),
        },
        {
            "email": "diana.garcia@student.school.com",
            "fullname": "Diana Garcia",
            "student_id": "S005",
            "parent": parents["parent4@example.com"],
            "class_enrolled": classes["Grade 5 A"],
            "phone": "+1-555-3004",
            "date_of_birth": date(2015, 12, 5),
            "gender": "Female",
            "admission_date": date(2021, 8, 1),
        },
        {
            "email": "edward.brown@student.school.com",
            "fullname": "Edward Brown",
            "student_id": "S006",
            "parent": parents["parent1@example.com"],
            "class_enrolled": classes["Grade 1 A"],
            "phone": "+1-555-3005",
            "date_of_birth": date(2019, 2, 28),
            "gender": "Male",
            "admission_date": date(2024, 8, 1),
        },
    ]
    students = {}
    for student_data in students_data:
        parent = student_data.pop("parent")
        class_enrolled = student_data.pop("class_enrolled")
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
                "class_enrolled": class_enrolled,
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
            student_profile.class_enrolled = class_enrolled
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
        if not student.class_enrolled:
            print(f"   Skipping attendance for {student.fullname} - no class assigned")
            continue
        for i in range(10):  # Last 10 days
            attendance_date = date.today() - timedelta(days=i)
            status = "Present" if i % 4 != 0 else "Absent"  # Mostly present
            Attendance.objects.get_or_create(
                student=student,
                date=attendance_date,
                defaults={
                    "class_enrolled": student.class_enrolled,
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
                class_level=cls,
                fee_type=fee_type,
                defaults={
                    "amount": amount,
                    "frequency": frequency,
                    "description": f"{fee_type} fee for {cls}"
                }
            )
            if created:
                fee_count += 1
    print(f"   Created {fee_count} new fee structures")
    
    # 13. Create Fee Payments
    print("\n13. Creating Fee Payments...")
    payment_count = 0
    for student in students.values():
        if not student.class_enrolled:
            continue
        fee_structures = FeeStructure.objects.filter(class_level=student.class_enrolled)
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
                    class_enrolled=cls,
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
    
    print("\n" + "="*50)
    print("DATABASE POPULATION COMPLETED SUCCESSFULLY!")
    print("="*50)
    print("\nSummary:")
    print(f"  Users: {User.objects.count()}")
    print(f"  Departments: {Department.objects.count()}")
    print(f"  Classes: {Class.objects.count()}")
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
    print("\nLogin Credentials:")
    print("  Admin: admin@school.com / admin123")
    print("  Principal: principal@school.com / principal123")
    print("  Teacher: john.smith@school.com / teacher123")
    print("  Student: student1@school.com / student1@school.com")
    print("  Parent: parent1@example.com / parent123")


if __name__ == "__main__":
    populate_database()
