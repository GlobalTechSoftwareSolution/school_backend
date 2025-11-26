import logging
from django.core.management.base import BaseCommand
from django.db import connection

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Remove old database trigger that conflicts with current schema'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            try:
                # Drop the trigger
                cursor.execute("DROP TRIGGER IF EXISTS trg_manage_role_tables ON school_user")
                self.stdout.write(
                    self.style.SUCCESS('Successfully dropped trigger trg_manage_role_tables')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error dropping trigger: {e}')
                )
            
            try:
                # Drop the function
                cursor.execute("DROP FUNCTION IF EXISTS manage_role_tables_on_user_change()")
                self.stdout.write(
                    self.style.SUCCESS('Successfully dropped function manage_role_tables_on_user_change')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error dropping function: {e}')
                )
        
        self.stdout.write(
            self.style.SUCCESS('Database cleanup completed. You can now approve users normally.')
        )
