import random
from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import transaction

class Command(BaseCommand):
    help = 'Remove all records from all models in the school app'

    def handle(self, *args, **options):
        self.stdout.write('Starting to remove all records from all models...')
        
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
        
        deleted_counts = {}
        
        # Delete records in the specified order
        with transaction.atomic():
            for model_name in ordered_models:
                try:
                    model = next((m for m in school_models if m.__name__ == model_name), None)
                    if model:
                        count = model.objects.all().delete()
                        deleted_counts[model_name] = count[0] if count else 0
                        self.stdout.write(f'Deleted {count[0] if count else 0} records from {model_name}')
                except Exception as e:
                    self.stdout.write(f'Error deleting records from {model_name}: {e}')
                    continue
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully removed all records from all models. Deleted counts: {deleted_counts}')
        )