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
    Assignment, Leave, Task, Project, Program, Activity, Report, FinanceTransaction, TransportDetails, Class,
)

def insert_raw_data():
    print("Inserting raw data for empty tables...")

    # Get existing data
    students = Student.objects.all()
    teachers = Teacher.objects.all()
    subjects = Subject.objects.all()
    users = User.objects.all()
    principal = Principal.objects.first()
    admin = Admin.objects.first()

    # Attendance
    if Attendance.objects.count() == 0 and students.exists():
        print("Inserting Attendance records...")
        for student in students:
            # Get or create the Class object
            class_name = student.class_fk.class_name if student.class_fk else "Grade 1"
            class_obj, _ = Class.objects.get_or_create(
                class_name=class_name,
                defaults={'sec': 'A'}
            )
            Attendance.objects.create(
                student=student,
                date=date.today(),
                class_fk=class_obj,
                status="Present",
                remarks="Auto-generated"
            )
        print(f"Inserted {students.count()} Attendance records")

    # Grade
    if Grade.objects.count() == 0 and students.exists() and subjects.exists() and teachers.exists():
        print("Inserting Grade records...")
        teacher = teachers.first()
        for student in students[:3]:  # First 3 students
            for subject in subjects[:3]:  # First 3 subjects
                Grade.objects.create(
                    student=student,
                    subject=subject,
                    exam_type="Quiz",
                    exam_date=date.today() - timedelta(days=30),
                    teacher=teacher,
                    marks_obtained=Decimal("80.00"),
                    total_marks=Decimal("100.00"),
                    remarks="Good"
                )
        print("Inserted Grade records")

    # FeeStructure
    if FeeStructure.objects.count() == 0:
        print("Inserting FeeStructure records...")
        classes = ["Grade 1", "Grade 5", "Grade 10"]
        for cls in classes:
            FeeStructure.objects.create(
                class_name=cls,
                fee_type="Tuition",
                amount=Decimal("5000.00"),
                frequency="Monthly",
                description=f"Tuition for {cls}"
            )
        print(f"Inserted {len(classes)} FeeStructure records")

    # FeePayment
    if FeePayment.objects.count() == 0 and students.exists():
        print("Inserting FeePayment records...")
        fee_structures = FeeStructure.objects.all()
        if fee_structures.exists():
            for student in students[:2]:  # First 2 students
                fee_struct = fee_structures.first()
                if fee_struct:
                    FeePayment.objects.create(
                        student=student,
                        fee_structure=fee_struct,
                        transaction_id=f"TXN{student.student_id}001",
                        amount_paid=fee_struct.amount,
                        payment_date=date.today(),
                        payment_method="Cash",
                        status="Paid",
                        remarks="Auto payment"
                    )
        print("Inserted FeePayment records")

    # Timetable
    if Timetable.objects.count() == 0 and subjects.exists() and teachers.exists():
        print("Inserting Timetable records...")
        subject = subjects.first()
        teacher = teachers.first()
        Timetable.objects.create(
            class_name="Grade 10",
            day_of_week="Monday",
            start_time=time(9, 0),
            end_time=time(10, 0),
            subject=subject,
            teacher=teacher,
            room_number="Room 101"
        )
        print("Inserted Timetable record")

    # Document
    if Document.objects.count() == 0 and users.exists():
        print("Inserting Document records...")
        user = users.filter(email="student1@school.com").first()
        if user:
            Document.objects.create(
                email=user,
                tenth="https://example.com/docs/tenth.pdf",
                id_proof="https://example.com/docs/id.pdf"
            )
        print("Inserted Document record")

    # Award
    if Award.objects.count() == 0 and users.exists():
        print("Inserting Award records...")
        user = users.filter(email="john.smith@school.com").first()
        if user:
            Award.objects.create(
                email=user,
                title="Best Teacher",
                description="Excellence in teaching",
                photo="https://example.com/awards/best-teacher.jpg"
            )
        print("Inserted Award record")

    # Assignment
    if Assignment.objects.count() == 0 and subjects.exists() and teachers.exists():
        print("Inserting Assignment records...")
        subject = subjects.first()
        teacher = teachers.first()
        if teacher:
            Assignment.objects.create(
                title="Math Homework",
                description="Solve problems 1-10",
                subject=subject,
                class_name="Grade 10",
                assigned_by=teacher.email,
                due_date=date.today() + timedelta(days=7),
                attachment="https://example.com/assignments/math.pdf"
            )
        print("Inserted Assignment record")

    # Leave
    if Leave.objects.count() == 0 and users.exists():
        print("Inserting Leave records...")
        user = users.filter(email="student1@school.com").first()
        if user:
            Leave.objects.create(
                applicant=user,
                leave_type="Sick",
                start_date=date.today() + timedelta(days=1),
                end_date=date.today() + timedelta(days=1),
                reason="Fever",
                status="Approved",
                approved_by=principal.email if principal else None
            )
        teacher_user = users.filter(email="john.smith@school.com").first()
        if teacher_user:
            Leave.objects.create(
                applicant=teacher_user,
                leave_type="Casual",
                start_date=date.today() + timedelta(days=3),
                end_date=date.today() + timedelta(days=3),
                reason="Family event",
                status="Pending",
                approved_by=principal.email if principal else None
            )
        print("Inserted Leave records")

    # Add one more leave as requested
    if Leave.objects.count() == 1 and users.exists():
        print("Adding one more Leave record...")
        admin_user = users.filter(email="admin@school.com").first()
        if admin_user:
            Leave.objects.create(
                applicant=admin_user,
                leave_type="Vacation",
                start_date=date.today() + timedelta(days=5),
                end_date=date.today() + timedelta(days=7),
                reason="Annual vacation",
                status="Pending",
                approved_by=principal.email if principal else None
            )
        print("Added one more Leave record")

    # TransportDetails
    if TransportDetails.objects.count() == 0 and students.exists():
        print("Inserting TransportDetails records...")
        student = students.first()
        if student:
            TransportDetails.objects.create(
                user=student.email,
                route_name="Route A",
                bus_number="BUS001",
                pickup_point="Main Gate",
                drop_point="City Center",
                driver_name="John Driver",
                driver_phone="+1234567890",
                transport_fee=Decimal("1000.00"),
                is_active=True
            )
        print("Inserted TransportDetails record")

    print("Raw data insertion completed!")

if __name__ == "__main__":
    insert_raw_data()
