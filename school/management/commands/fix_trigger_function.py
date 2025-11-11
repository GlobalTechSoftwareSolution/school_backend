from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Fix the manage_role_tables_on_user_change trigger function'

    def handle(self, *args, **options):
        self.stdout.write('Fixing the manage_role_tables_on_user_change trigger function...')
        
        sql = """
        CREATE OR REPLACE FUNCTION public.manage_role_tables_on_user_change()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $function$
        BEGIN
          IF (TG_OP = 'INSERT') OR
             (TG_OP = 'UPDATE' AND (NEW.is_approved <> OLD.is_approved OR NEW.role <> OLD.role)) THEN

            DELETE FROM school_student WHERE email_id = NEW.email;
            DELETE FROM school_teacher WHERE email_id = NEW.email;
            DELETE FROM school_principal WHERE email_id = NEW.email;
            DELETE FROM school_management WHERE email_id = NEW.email;
            DELETE FROM school_admin WHERE email_id = NEW.email;
            DELETE FROM school_parent WHERE email_id = NEW.email;

            IF NEW.is_approved = TRUE THEN
              IF NEW.role = 'Student' THEN
                INSERT INTO school_student(email_id, fullname) VALUES (NEW.email, '');
              ELSIF NEW.role = 'Teacher' THEN
                INSERT INTO school_teacher(email_id, fullname, is_classteacher) VALUES (NEW.email, '', FALSE);
              ELSIF NEW.role = 'Principal' THEN
                INSERT INTO school_principal(email_id, fullname) VALUES (NEW.email, '');
              ELSIF NEW.role = 'Management' THEN
                INSERT INTO school_management(email_id, fullname) VALUES (NEW.email, '');
              ELSIF NEW.role = 'Admin' THEN
                INSERT INTO school_admin(email_id, fullname) VALUES (NEW.email, '');
              ELSIF NEW.role = 'Parent' THEN
                INSERT INTO school_parent(email_id, fullname) VALUES (NEW.email, '');
              END IF;
            END IF;

          ELSIF TG_OP = 'DELETE' THEN
            DELETE FROM school_student WHERE email_id = OLD.email;
            DELETE FROM school_teacher WHERE email_id = OLD.email;
            DELETE FROM school_principal WHERE email_id = OLD.email;
            DELETE FROM school_management WHERE email_id = OLD.email;
            DELETE FROM school_admin WHERE email_id = OLD.email;
            DELETE FROM school_parent WHERE email_id = OLD.email;
          END IF;

          RETURN NEW;
        END;
        $function$
        """
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql)
            self.stdout.write(self.style.SUCCESS('Successfully fixed the trigger function'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error fixing the trigger function: {e}'))