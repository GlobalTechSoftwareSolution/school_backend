-- =====================================================================
-- ⚠️ IMPORTANT: THIS DATABASE TRIGGER IS NOT CURRENTLY IN USE
-- =====================================================================
-- This PostgreSQL trigger has been REPLACED by Django signals for better
-- maintainability and to avoid race conditions between database-level
-- and application-level logic.
--
-- Current Implementation: Django signals in school/signals.py handle:
--   1. Role table management (Student, Teacher, Principal, Management, Admin, Parent)
--   2. Automatic role record creation when user is approved
--   3. Role record cleanup on user deletion
--   4. Role record updates when user role changes
--
-- DO NOT apply this trigger to the database unless you remove the Django
-- signals implementation to avoid conflicts and data inconsistencies.
-- =====================================================================

/*
CREATE OR REPLACE FUNCTION manage_role_tables_on_user_change()
RETURNS TRIGGER AS $$
BEGIN
  -- Handle INSERT or UPDATE
  IF (TG_OP = 'INSERT') OR
     (TG_OP = 'UPDATE' AND (NEW.is_approved <> OLD.is_approved OR NEW.role <> OLD.role)) THEN

    -- Delete any existing role records for this user
    DELETE FROM school_student WHERE email_id = NEW.email;
    DELETE FROM school_teacher WHERE email_id = NEW.email;
    DELETE FROM school_principal WHERE email_id = NEW.email;
    DELETE FROM school_management WHERE email_id = NEW.email;
    DELETE FROM school_admin WHERE email_id = NEW.email;
    DELETE FROM school_parent WHERE email_id = NEW.email;

    -- Only create new records if user is approved
    IF NEW.is_approved = TRUE THEN
      IF NEW.role = 'Student' THEN
        INSERT INTO school_student(
          email_id, fullname, student_id, phone, date_of_birth, gender,
          admission_date, class_enrolled_id, parent_id, profile_picture,
          residential_address, emergency_contact_name, emergency_contact_relationship,
          emergency_contact_no, nationality, blood_group
        ) VALUES (
          NEW.email, '', NULL, '', NULL, '', NULL, NULL, NULL, '',
          '', '', '', '', '', NULL
        );
      
      ELSIF NEW.role = 'Teacher' THEN
        INSERT INTO school_teacher(
          email_id, fullname, teacher_id, phone, date_of_birth, gender,
          date_joined, department_id, qualification, experience_years,
          profile_picture, residential_address, emergency_contact_name,
          emergency_contact_relationship, emergency_contact_no, nationality, blood_group
        ) VALUES (
          NEW.email, '', NULL, '', NULL, '', NULL, NULL, '', NULL,
          '', '', '', '', '', '', NULL
        );
      
      ELSIF NEW.role = 'Principal' THEN
        INSERT INTO school_principal(
          email_id, fullname, phone, date_of_birth, date_joined,
          qualification, total_experience, bio, profile_picture, office_address
        ) VALUES (
          NEW.email, '', '', NULL, NULL, '', NULL, '', '', ''
        );
      
      ELSIF NEW.role = 'Management' THEN
        INSERT INTO school_management(
          email_id, fullname, phone, designation, date_of_birth,
          date_joined, department_id, profile_picture, office_address
        ) VALUES (
          NEW.email, '', '', '', NULL, NULL, NULL, '', ''
        );
      
      ELSIF NEW.role = 'Admin' THEN
        INSERT INTO school_admin(
          email_id, fullname, phone, office_address, profile_picture
        ) VALUES (
          NEW.email, '', '', '', ''
        );
      
      ELSIF NEW.role = 'Parent' THEN
        INSERT INTO school_parent(
          email_id, fullname, phone, occupation, residential_address,
          profile_picture, relationship_to_student
        ) VALUES (
          NEW.email, '', '', '', '', '', ''
        );
      END IF;
    END IF;

  -- Handle DELETE (user deletion)
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
$$ LANGUAGE plpgsql;

-- Recreate the trigger
DROP TRIGGER IF EXISTS trg_manage_role_tables ON school_user;

CREATE TRIGGER trg_manage_role_tables
AFTER INSERT OR UPDATE OR DELETE ON school_user
FOR EACH ROW
EXECUTE FUNCTION manage_role_tables_on_user_change();
*/

-- =====================================================================
-- INSTEAD, USE THE DJANGO SIGNALS IMPLEMENTATION
-- =====================================================================
-- Location: school/signals.py
-- 
-- The Django signals approach provides:
-- ✅ Better code maintainability
-- ✅ Easier debugging and testing
-- ✅ Works across different databases
-- ✅ Follows Django best practices
-- ✅ No database-specific syntax
-- ✅ Application-level transaction control
-- =====================================================================
