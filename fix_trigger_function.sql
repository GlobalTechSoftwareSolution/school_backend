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