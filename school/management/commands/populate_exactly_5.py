import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from school.models import *
from datetime import date, timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Populate database with exactly 5 records for each model'

    def handle(self, *args, **options):
        self.stdout.write('Starting to populate database with exactly 5 records for each model...')
        
        # Get existing data
        departments = list(Department.objects.all())[:5]
        classes = list(Class.objects.all())[:5]
        subjects = list(Subject.objects.all())[:5]
        students = list(Student.objects.all())[:5]
        teachers = list(Teacher.objects.all())[:5]
        users = list(User.objects.all())[:25]  # Get first 25 users (5 of each role)
        parents = list(Parent.objects.all())[:5]
        assignments = list(Assignment.objects.all())[:5]
        
        # Ensure we have exactly 5 FormerMember records
        former_members = list(FormerMember.objects.all())
        if len(former_members) > 5:
            # Delete extra FormerMember records
            for member in former_members[5:]:
                member.delete()
            former_members = former_members[:5]
        elif len(former_members) < 5:
            # Create additional FormerMember records
            for i in range(len(former_members), 5):
                member = FormerMember.objects.create(
                    email=f'former{i+1}@test.com',
                    fullname=f'Former Member {i+1}',
                    role=random.choice(['Student', 'Teacher']),
                    phone=f'+123456789{i:02d}',
                    date_of_birth='1990-01-01',
                    gender=random.choice(['Male', 'Female']),
                    left_date=timezone.now(),
                    reason=f'Reason {i+1}',
                )
                former_members.append(member)
                self.stdout.write(f"Created FormerMember: Former Member {i+1}")
        
        # Ensure we have exactly 5 StudentAttendance records
        student_attendances = list(StudentAttendance.objects.all())
        if len(student_attendances) > 5:
            # Delete extra StudentAttendance records
            for att in student_attendances[5:]:
                att.delete()
            student_attendances = student_attendances[:5]
        elif len(student_attendances) < 5:
            # Create additional StudentAttendance records
            for i in range(len(student_attendances), 5):
                if students and subjects and teachers and classes:
                    att = StudentAttendance.objects.create(
                        student=students[i % len(students)],
                        subject=subjects[i % len(subjects)],
                        teacher=teachers[i % len(teachers)],
                        class_id=classes[i % len(classes)],
                        date=date.today() - timedelta(days=i),
                        status=random.choice(['Present', 'Absent', 'Late', 'Excused']),
                    )
                    student_attendances.append(att)
                    self.stdout.write(f"Created StudentAttendance: {students[i % len(students)].fullname}")
        
        # Ensure we have exactly 5 Grade records
        grades = list(Grade.objects.all())
        if len(grades) > 5:
            # Delete extra Grade records
            for grade in grades[5:]:
                grade.delete()
            grades = grades[:5]
        elif len(grades) < 5:
            # Create additional Grade records
            for i in range(len(grades), 5):
                if students and subjects and teachers:
                    grade = Grade.objects.create(
                        student=students[i % len(students)],
                        subject=subjects[i % len(subjects)],
                        teacher=teachers[i % len(teachers)],
                        exam_type=random.choice(['Quiz', 'Midterm', 'Final', 'Assignment', 'Project']),
                        marks_obtained=random.randint(60, 100),
                        total_marks=100,
                        exam_date=date.today() - timedelta(days=i*5),
                        remarks=f'Grade remarks {i+1}',
                    )
                    grades.append(grade)
                    self.stdout.write(f"Created Grade: {students[i % len(students)].fullname}")
        
        # Ensure we have exactly 5 FeeStructure records
        fee_structures = list(FeeStructure.objects.all())
        if len(fee_structures) > 5:
            # Delete extra FeeStructure records
            for fs in fee_structures[5:]:
                fs.delete()
            fee_structures = fee_structures[:5]
        elif len(fee_structures) < 5:
            # Create additional FeeStructure records
            fee_types = ['Tuition', 'Transport', 'Library', 'Sports', 'Lab']
            for i in range(len(fee_structures), 5):
                if classes:
                    fs = FeeStructure.objects.create(
                        class_id=classes[i % len(classes)],
                        fee_type=fee_types[i % len(fee_types)],
                        amount=random.randint(500, 5000),
                        frequency=random.choice(['Monthly', 'Quarterly', 'Annually', 'One-time']),
                        description=f'{fee_types[i % len(fee_types)]} fee for {classes[i % len(classes)].class_name}',
                    )
                    fee_structures.append(fs)
                    self.stdout.write(f"Created FeeStructure: {fee_types[i % len(fee_types)]}")
        
        # Ensure we have exactly 5 FeePayment records
        fee_payments = list(FeePayment.objects.all())
        if len(fee_payments) > 5:
            # Delete extra FeePayment records
            for fp in fee_payments[5:]:
                fp.delete()
            fee_payments = fee_payments[:5]
        elif len(fee_payments) < 5:
            # Create additional FeePayment records
            for i in range(len(fee_payments), 5):
                if students and fee_structures:
                    fp = FeePayment.objects.create(
                        student=students[i % len(students)],
                        fee_structure=fee_structures[i % len(fee_structures)],
                        total_amount=random.randint(1000, 10000),
                        amount_paid=random.randint(500, 5000),
                        remaining_amount=random.randint(0, 5000),
                        payment_date=date.today() - timedelta(days=i*10),
                        payment_method=random.choice(['Cash', 'Card', 'Bank Transfer', 'Online', 'Cheque']),
                        transaction_id=f'TRANS{i+1:05d}',
                        status=random.choice(['Paid', 'Pending', 'Failed']),
                        remarks=f'Fee payment remarks {i+1}',
                    )
                    fee_payments.append(fp)
                    self.stdout.write(f"Created FeePayment: {students[i % len(students)].fullname}")
        
        # Ensure we have exactly 5 Timetable records
        timetables = list(Timetable.objects.all())
        if len(timetables) > 5:
            # Delete extra Timetable records
            for tt in timetables[5:]:
                tt.delete()
            timetables = timetables[:5]
        elif len(timetables) < 5:
            # Create additional Timetable records
            for i in range(len(timetables), 5):
                if classes and subjects and teachers:
                    tt = Timetable.objects.create(
                        class_id=classes[i % len(classes)],
                        subject=subjects[i % len(subjects)],
                        teacher=teachers[i % len(teachers)],
                        day_of_week=random.choice(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']),
                        start_time=f'{9 + i}:00:00',
                        end_time=f'{10 + i}:00:00',
                        room_number=f'Room {i+1:03d}',
                    )
                    timetables.append(tt)
                    self.stdout.write(f"Created Timetable: {classes[i % len(classes)].class_name}")
        
        # Ensure we have exactly 5 SubmittedAssignment records
        submitted_assignments = list(SubmittedAssignment.objects.all())
        if len(submitted_assignments) > 5:
            # Delete extra SubmittedAssignment records
            for sa in submitted_assignments[5:]:
                sa.delete()
            submitted_assignments = submitted_assignments[:5]
        elif len(submitted_assignments) < 5:
            # Create additional SubmittedAssignment records
            for i in range(len(submitted_assignments), 5):
                if students and assignments:
                    sa = SubmittedAssignment.objects.create(
                        assignment=assignments[i % len(assignments)],
                        student=students[i % len(students)],
                        submission_file='https://example.com/submission.pdf',
                        submission_date=timezone.now() - timedelta(days=i),
                        grade=random.randint(60, 100),
                        feedback=f'Good work on assignment {i+1}',
                        is_late=i % 3 == 0,
                    )
                    submitted_assignments.append(sa)
                    self.stdout.write(f"Created SubmittedAssignment: {assignments[i % len(assignments)].title}")
        
        # Ensure we have exactly 5 Document records
        documents = list(Document.objects.all())
        if len(documents) > 5:
            # Delete extra Document records
            for doc in documents[5:]:
                doc.delete()
            documents = documents[:5]
        elif len(documents) < 5:
            # Create additional Document records
            for i in range(len(documents), 5):
                if users:
                    doc = Document.objects.create(
                        email=users[i % len(users)],
                        tenth='https://example.com/10th_marks_card.pdf',
                        twelth='https://example.com/12th_marks_card.pdf',
                        degree='https://example.com/degree_certificate.pdf',
                        marks_card='https://example.com/marks_card.pdf',
                        certificates='https://example.com/certificates.pdf',
                    )
                    documents.append(doc)
                    self.stdout.write(f"Created Document: {users[i % len(users)].email}")
        
        # Ensure we have exactly 5 Award records
        awards = list(Award.objects.all())
        if len(awards) > 5:
            # Delete extra Award records
            for award in awards[5:]:
                award.delete()
            awards = awards[:5]
        elif len(awards) < 5:
            # Create additional Award records
            for i in range(len(awards), 5):
                if users:
                    award = Award.objects.create(
                        email=users[i % len(users)],
                        title=f'Award {i+1}',
                        description=f'Description for award {i+1}',
                        photo='https://example.com/award_photo.jpg',
                    )
                    awards.append(award)
                    self.stdout.write(f"Created Award: Award {i+1}")
        
        # Ensure we have exactly 5 Notice records
        notices = list(Notice.objects.all())
        if len(notices) > 5:
            # Delete extra Notice records
            for notice in notices[5:]:
                notice.delete()
            notices = notices[:5]
        elif len(notices) < 5:
            # Create additional Notice records
            for i in range(len(notices), 5):
                if users:
                    notice = Notice.objects.create(
                        title=f'Notice {i+1}',
                        message=f'Message for notice {i+1}',
                        email=users[i % len(users)],
                        posted_date=date.today() - timedelta(days=i),
                        valid_until=date.today() + timedelta(days=30),
                        important=i % 2 == 0,
                        attachment='https://example.com/notice_attachment.pdf',
                    )
                    notices.append(notice)
                    self.stdout.write(f"Created Notice: Notice {i+1}")
        
        # Ensure we have exactly 5 Issue records
        issues = list(Issue.objects.all())
        if len(issues) > 5:
            # Delete extra Issue records
            for issue in issues[5:]:
                issue.delete()
            issues = issues[:5]
        elif len(issues) < 5:
            # Create additional Issue records
            for i in range(len(issues), 5):
                if users:
                    issue = Issue.objects.create(
                        subject=f'Issue {i+1}',
                        status=random.choice(['Open', 'In Progress', 'Closed']),
                        description=f'Description for issue {i+1}',
                        priority=random.choice(['Low', 'Medium', 'High', 'Urgent']),
                        created_at=timezone.now() - timedelta(days=i),
                        updated_at=timezone.now() - timedelta(days=i//2),
                        closed_description=f'Closed description for issue {i+1}' if i % 3 == 0 else None,
                        raised_by=users[i % len(users)],
                    )
                    issues.append(issue)
                    self.stdout.write(f"Created Issue: Issue {i+1}")
        
        # Ensure we have exactly 5 Holiday records
        holidays = list(Holiday.objects.all())
        if len(holidays) > 5:
            # Delete extra Holiday records
            for holiday in holidays[5:]:
                holiday.delete()
            holidays = holidays[:5]
        elif len(holidays) < 5:
            # Create additional Holiday records
            for i in range(len(holidays), 5):
                holiday_date = date.today() + timedelta(days=30+i*5)
                holiday = Holiday.objects.create(
                    date=holiday_date,
                    name=f'Holiday {i+1}',
                    type=random.choice(['National', 'Regional', 'School', 'Religious']),
                    year=holiday_date.year,
                    month=holiday_date.month,
                    country='India',
                )
                holidays.append(holiday)
                self.stdout.write(f"Created Holiday: Holiday {i+1}")
        
        # Ensure we have exactly 5 Leave records
        leaves = list(Leave.objects.all())
        if len(leaves) > 5:
            # Delete extra Leave records
            for leave in leaves[5:]:
                leave.delete()
            leaves = leaves[:5]
        elif len(leaves) < 5:
            # Create additional Leave records
            for i in range(len(leaves), 5):
                if users:
                    leave = Leave.objects.create(
                        applicant=users[i % len(users)],
                        leave_type=random.choice(['Sick', 'Casual', 'Vacation', 'Other']),
                        start_date=date.today() + timedelta(days=10+i),
                        end_date=date.today() + timedelta(days=12+i),
                        reason=f'Reason for leave {i+1}',
                        status=random.choice(['Pending', 'Approved', 'Rejected']),
                    )
                    leaves.append(leave)
                    self.stdout.write(f"Created Leave: {users[i % len(users)].email}")
        
        # Ensure we have exactly 5 Task records
        tasks = list(Task.objects.all())
        if len(tasks) > 5:
            # Delete extra Task records
            for task in tasks[5:]:
                task.delete()
            tasks = tasks[:5]
        elif len(tasks) < 5:
            # Create additional Task records
            for i in range(len(tasks), 5):
                if users:
                    task = Task.objects.create(
                        title=f'Task {i+1}',
                        description=f'Description for task {i+1}',
                        assigned_to=users[i % len(users)],
                        status=random.choice(['Todo', 'In Progress', 'Done']),
                        priority=random.choice(['Low', 'Medium', 'High', 'Urgent']),
                        due_date=date.today() + timedelta(days=7+i),
                    )
                    tasks.append(task)
                    self.stdout.write(f"Created Task: Task {i+1}")
        
        # Ensure we have exactly 5 Project records
        projects = list(Project.objects.all())
        if len(projects) > 5:
            # Delete extra Project records
            for project in projects[5:]:
                project.delete()
            projects = projects[:5]
        elif len(projects) < 5:
            # Create additional Project records
            for i in range(len(projects), 5):
                if users:
                    project = Project.objects.create(
                        title=f'Project {i+1}',
                        description=f'Description for project {i+1}',
                        start_date=date.today() - timedelta(days=30),
                        end_date=date.today() + timedelta(days=30),
                        status=random.choice(['Planned', 'In Progress', 'Completed', 'On Hold', 'Cancelled']),
                        owner=users[i % len(users)],
                    )
                    projects.append(project)
                    self.stdout.write(f"Created Project: Project {i+1}")
        
        # Ensure we have exactly 5 Program records
        programs = list(Program.objects.all())
        if len(programs) > 5:
            # Delete extra Program records
            for program in programs[5:]:
                program.delete()
            programs = programs[:5]
        elif len(programs) < 5:
            # Create additional Program records
            for i in range(len(programs), 5):
                if users:
                    program = Program.objects.create(
                        name=f'Program {i+1}',
                        description=f'Description for program {i+1}',
                        start_date=date.today() - timedelta(days=60),
                        end_date=date.today() + timedelta(days=60),
                        coordinator=users[i % len(users)],
                        status=random.choice(['Planned', 'Active', 'Completed', 'Cancelled']),
                    )
                    programs.append(program)
                    self.stdout.write(f"Created Program: Program {i+1}")
        
        # Ensure we have exactly 5 Activity records
        activities = list(Activity.objects.all())
        if len(activities) > 5:
            # Delete extra Activity records
            for activity in activities[5:]:
                activity.delete()
            activities = activities[:5]
        elif len(activities) < 5:
            # Create additional Activity records
            for i in range(len(activities), 5):
                if users:
                    activity = Activity.objects.create(
                        name=f'Activity {i+1}',
                        description=f'Description for activity {i+1}',
                        type=random.choice(['Sports', 'Cultural', 'Academic', 'Other']),
                        date=date.today() + timedelta(days=i*3),
                        conducted_by=users[i % len(users)],
                        attachment='https://example.com/activity_attachment.pdf',
                    )
                    activities.append(activity)
                    self.stdout.write(f"Created Activity: Activity {i+1}")
        
        # Ensure we have exactly 5 Report records
        reports = list(Report.objects.all())
        if len(reports) > 5:
            # Delete extra Report records
            for report in reports[5:]:
                report.delete()
            reports = reports[:5]
        elif len(reports) < 5:
            # Create additional Report records
            for i in range(len(reports), 5):
                if students and users:
                    report = Report.objects.create(
                        title=f'Report {i+1}',
                        description=f'Description for report {i+1}',
                        report_type=random.choice(['General', 'Academic', 'Behavior', 'Finance', 'Other']),
                        student=students[i % len(students)],
                        created_by=users[0] if users else None,
                        file_url='https://example.com/report_file.pdf',
                    )
                    reports.append(report)
                    self.stdout.write(f"Created Report: Report {i+1}")
        
        # Ensure we have exactly 5 FinanceTransaction records
        finance_transactions = list(FinanceTransaction.objects.all())
        if len(finance_transactions) > 5:
            # Delete extra FinanceTransaction records
            for ft in finance_transactions[5:]:
                ft.delete()
            finance_transactions = finance_transactions[:5]
        elif len(finance_transactions) < 5:
            # Create additional FinanceTransaction records
            for i in range(len(finance_transactions), 5):
                if users:
                    ft = FinanceTransaction.objects.create(
                        date=date.today() - timedelta(days=i*2),
                        amount=random.randint(1000, 10000),
                        type=random.choice(['Income', 'Expense']),
                        category=random.choice(['Tuition', 'Transport', 'Salaries', 'Supplies', 'Maintenance', 'Other']),
                        description=f'Description for finance transaction {i+1}',
                        reference_id=f'REF{i+1:05d}',
                        recorded_by=users[i % len(users)],
                    )
                    finance_transactions.append(ft)
                    self.stdout.write(f"Created FinanceTransaction: {ft.type}")
        
        # Ensure we have exactly 5 TransportDetails records
        transport_details = list(TransportDetails.objects.all())
        if len(transport_details) > 5:
            # Delete extra TransportDetails records
            for td in transport_details[5:]:
                td.delete()
            transport_details = transport_details[:5]
        elif len(transport_details) < 5:
            # Create additional TransportDetails records
            for i in range(len(transport_details), 5):
                if users:
                    td = TransportDetails.objects.create(
                        user=users[i % len(users)],
                        route_name=f'Route {i+1}',
                        bus_number=f'BUS{i+1:03d}',
                        pickup_point=f'Pickup Point {i+1}',
                        drop_point=f'Drop Point {i+1}',
                        driver_name=f'Driver {i+1}',
                        driver_phone=f'+123456789{i:02d}',
                        transport_fee=random.randint(500, 2000),
                    )
                    transport_details.append(td)
                    self.stdout.write(f"Created TransportDetails: {users[i % len(users)].email}")
        
        # Ensure we have exactly 5 IDCard records
        id_cards = list(IDCard.objects.all())
        if len(id_cards) > 5:
            # Delete extra IDCard records
            for id_card in id_cards[5:]:
                id_card.delete()
            id_cards = id_cards[:5]
        elif len(id_cards) < 5:
            # Create additional IDCard records
            for i in range(len(id_cards), 5):
                if users:
                    id_card = IDCard.objects.create(
                        user=users[i % len(users)],
                        id_card_url='https://example.com/id_card.pdf',
                    )
                    id_cards.append(id_card)
                    self.stdout.write(f"Created IDCard: {users[i % len(users)].email}")
        
        self.stdout.write(
            self.style.SUCCESS('Successfully populated database with exactly 5 records for each model!')
        )