import logging
from django.core.management.base import BaseCommand
from django.db import connection

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Fix database schema inconsistencies'

    def handle(self, *args, **options):
        self.stdout.write('Checking database schema inconsistencies...')
        
        with connection.cursor() as cursor:
            # Check if class_id_id exists in school_teacher table
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'school_teacher' 
                AND column_name = 'class_id_id'
            """)
            result = cursor.fetchone()
            
            if result:
                self.stdout.write('Found class_id_id column in school_teacher table, renaming to class_id...')
                try:
                    cursor.execute("""
                        ALTER TABLE school_teacher 
                        RENAME COLUMN class_id_id TO class_id
                    """)
                    self.stdout.write(self.style.SUCCESS('Successfully renamed class_id_id to class_id in school_teacher table'))
                except Exception as e:
                    self.stdout.write(f'Error renaming column in school_teacher: {e}')
            
            # Check if class_id_id exists in school_student table
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'school_student' 
                AND column_name = 'class_id_id'
            """)
            result = cursor.fetchone()
            
            # Check if class_fk_id exists in school_student table
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'school_student' 
                AND column_name = 'class_fk_id'
            """)
            result = cursor.fetchone()
            
            if result:
                self.stdout.write('Found class_fk_id column in school_student table, renaming to class_id...')
                try:
                    cursor.execute("""
                        ALTER TABLE school_student 
                        RENAME COLUMN class_fk_id TO class_id
                    """)
                    self.stdout.write(self.style.SUCCESS('Successfully renamed class_fk_id to class_id in school_student table'))
                except Exception as e:
                    self.stdout.write(f'Error renaming column in school_student: {e}')
            
            # Check if class_fk_id exists in school_feestructure table
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'school_feestructure' 
                AND column_name = 'class_fk_id'
            """)
            result = cursor.fetchone()
            
            if result:
                self.stdout.write('Found class_fk_id column in school_feestructure table, renaming to class_id...')
                try:
                    cursor.execute("""
                        ALTER TABLE school_feestructure 
                        RENAME COLUMN class_fk_id TO class_id
                    """)
                    self.stdout.write(self.style.SUCCESS('Successfully renamed class_fk_id to class_id in school_feestructure table'))
                except Exception as e:
                    self.stdout.write(f'Error renaming column in school_feestructure: {e}')
            
            # Check if class_fk_id exists in school_assignment table
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'school_assignment' 
                AND column_name = 'class_fk_id'
            """)
            result = cursor.fetchone()
            
            if result:
                self.stdout.write('Found class_fk_id column in school_assignment table, renaming to class_id...')
                try:
                    cursor.execute("""
                        ALTER TABLE school_assignment 
                        RENAME COLUMN class_fk_id TO class_id
                    """)
                    self.stdout.write(self.style.SUCCESS('Successfully renamed class_fk_id to class_id in school_assignment table'))
                except Exception as e:
                    self.stdout.write(f'Error renaming column in school_assignment: {e}')
            
            # Check if class_fk_id exists in school_timetable table
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'school_timetable' 
                AND column_name = 'class_fk_id'
            """)
            result = cursor.fetchone()
            
            if result:
                self.stdout.write('Found class_fk_id column in school_timetable table, renaming to class_id...')
                try:
                    cursor.execute("""
                        ALTER TABLE school_timetable 
                        RENAME COLUMN class_fk_id TO class_id
                    """)
                    self.stdout.write(self.style.SUCCESS('Successfully renamed class_fk_id to class_id in school_timetable table'))
                except Exception as e:
                    self.stdout.write(f'Error renaming column in school_timetable: {e}')
            
            # Check if class_fk_id exists in school_attendance table
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'school_attendance' 
                AND column_name = 'class_fk_id'
            """)
            result = cursor.fetchone()
            
            if result:
                self.stdout.write('Found class_fk_id column in school_attendance table, renaming to class_id...')
                try:
                    cursor.execute("""
                        ALTER TABLE school_attendance 
                        RENAME COLUMN class_fk_id TO class_id
                    """)
                    self.stdout.write(self.style.SUCCESS('Successfully renamed class_fk_id to class_id in school_attendance table'))
                except Exception as e:
                    self.stdout.write(f'Error renaming column in school_attendance: {e}')
            
            # Check if class_fk_id exists in school_project table
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'school_project' 
                AND column_name = 'class_fk_id'
            """)
            result = cursor.fetchone()
            
            if result:
                self.stdout.write('Found class_fk_id column in school_project table, renaming to class_id...')
                try:
                    cursor.execute("""
                        ALTER TABLE school_project 
                        RENAME COLUMN class_fk_id TO class_id
                    """)
                    self.stdout.write(self.style.SUCCESS('Successfully renamed class_fk_id to class_id in school_project table'))
                except Exception as e:
                    self.stdout.write(f'Error renaming column in school_project: {e}')
            
            # Check if class_fk_id exists in school_activity table
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'school_activity' 
                AND column_name = 'class_fk_id'
            """)
            result = cursor.fetchone()
            
            if result:
                self.stdout.write('Found class_fk_id column in school_activity table, renaming to class_id...')
                try:
                    cursor.execute("""
                        ALTER TABLE school_activity 
                        RENAME COLUMN class_fk_id TO class_id
                    """)
                    self.stdout.write(self.style.SUCCESS('Successfully renamed class_fk_id to class_id in school_activity table'))
                except Exception as e:
                    self.stdout.write(f'Error renaming column in school_activity: {e}')
        
        self.stdout.write(self.style.SUCCESS('Finished checking and fixing database schema inconsistencies'))
