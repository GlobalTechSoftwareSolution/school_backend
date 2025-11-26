import os
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_backend.settings')
django.setup()

from school.models import (
    User, Department, Class, Subject, Student, Teacher, Principal, Management, Admin, Parent,
    Attendance, Grade, FeeStructure, FeePayment, Timetable, Assignment, FormerMember,
    Document, Award, Notice, Issue, Holiday, Leave, Task, Project, Program, Activity,
    Report, FinanceTransaction, TransportDetails
)

def verify_data():
    print("Verifying data in all models...")
    
    models_to_check = [
        ('Users', User),
        ('Departments', Department),
        ('Classes', Class),
        ('Subjects', Subject),
        ('Students', Student),
        ('Teachers', Teacher),
        ('Principals', Principal),
        ('Management', Management),
        ('Admins', Admin),
        ('Parents', Parent),
        ('Attendances', Attendance),
        ('Grades', Grade),
        ('FeeStructures', FeeStructure),
        ('FeePayments', FeePayment),
        ('Timetables', Timetable),
        ('Assignments', Assignment),
        ('FormerMembers', FormerMember),
        ('Documents', Document),
        ('Awards', Award),
        ('Notices', Notice),
        ('Issues', Issue),
        ('Holidays', Holiday),
        ('Leaves', Leave),
        ('Tasks', Task),
        ('Projects', Project),
        ('Programs', Program),
        ('Activities', Activity),
        ('Reports', Report),
        ('FinanceTransactions', FinanceTransaction),
        ('TransportDetails', TransportDetails),
    ]
    
    for name, model in models_to_check:
        count = model.objects.count()
        print(f"{name}: {count}")
        
        # Show first record details if any exist
        if count > 0:
            try:
                first_record = model.objects.first()
                if hasattr(first_record, '__str__'):
                    print(f"  First record: {first_record}")
                else:
                    print(f"  First record exists")
            except Exception as e:
                print(f"  Error getting first record: {e}")
        print()

if __name__ == '__main__':
    verify_data()