from django.db.models.signals import post_save, post_delete, pre_delete
from django.dispatch import receiver
from django.db import transaction
from .models import (
    User, Student, Teacher, Principal, Management, Admin, Parent, FormerMember
)


# ===============================================================
# DJANGO SIGNALS FOR ROLE-BASED TABLE MANAGEMENT
# ===============================================================
# This replaces database triggers for better maintainability and
# to avoid race conditions between database-level and application
# level logic.
#
# Handles:
#   1. Automatic role table creation when user is approved
#   2. Role table cleanup when role changes
#   3. Default data initialization for each role
#   4. Cascade deletion handling
# ===============================================================


@receiver(post_save, sender=User)
def manage_role_tables_on_user_save(sender, instance, created, **kwargs):
    """
    Automatically create or update role-specific records when a User is saved.
    Only creates role records when user is approved (is_approved=True).
    """
    # Only process if user is approved
    if not instance.is_approved:
        return
    
    # Use transaction to ensure atomicity
    with transaction.atomic():
        # Get the current role
        role = instance.role
        email = instance.email
        
        # Clean up existing role records for this user
        # (in case role was changed)
        _cleanup_role_records(email)
        
        # Create appropriate role record based on user's role
        if role == 'Student':
            _create_student_record(email)
        elif role == 'Teacher':
            _create_teacher_record(email)
        elif role == 'Principal':
            _create_principal_record(email)
        elif role == 'Management':
            _create_management_record(email)
        elif role == 'Admin':
            _create_admin_record(email)
        elif role == 'Parent':
            _create_parent_record(email)


@receiver(pre_delete, sender=User)
def cleanup_role_tables_on_user_delete(sender, instance, **kwargs):
    """
    Before deleting a User:
    1. Create a backup in FormerMember table (if doesn't exist)
    2. Clean up role-specific records
    
    FormerMember stores email as a string field, so it's completely independent
    from the User table and will NEVER be affected by User deletions.
    """
    with transaction.atomic():
        # 1) Ensure backup exists in FormerMember
        _backup_to_former_member(instance)
        
        # 2) Clean up role records
        _cleanup_role_records(instance.email)


# ===============================================================
# HELPER FUNCTIONS
# ===============================================================

def _cleanup_role_records(email):
    """
    Remove any existing role records for the given email.
    Used before creating new role records or when user is deleted.
    """
    # Delete from all role tables
    Student.objects.filter(email=email).delete()
    Teacher.objects.filter(email=email).delete()
    Principal.objects.filter(email=email).delete()
    Management.objects.filter(email=email).delete()
    Admin.objects.filter(email=email).delete()
    Parent.objects.filter(email=email).delete()


def _backup_to_former_member(user_instance):
    """
    Create a backup of user data in FormerMember table before deletion.
    Checks all role tables and copies relevant data.
    """
    email_str = user_instance.email
    
    # Skip if backup already exists
    if FormerMember.objects.filter(email=email_str).exists():
        return
    
    # Try to find user data in role tables
    role_tables = [
        (Student, 'Student'),
        (Teacher, 'Teacher'),
        (Principal, 'Principal'),
        (Management, 'Management'),
        (Admin, 'Admin'),
        (Parent, 'Parent'),
    ]
    
    for table, role_name in role_tables:
        try:
            obj = table.objects.get(email=user_instance)
            
            # Create FormerMember backup with all available data
            FormerMember.objects.create(
                email=email_str,
                fullname=getattr(obj, 'fullname', ''),
                role=role_name,
                phone=getattr(obj, 'phone', ''),
                date_of_birth=getattr(obj, 'date_of_birth', None),
                gender=getattr(obj, 'gender', ''),
                # Student/Teacher specific
                student_id=getattr(obj, 'student_id', None),
                teacher_id=getattr(obj, 'teacher_id', None),
                admission_date=getattr(obj, 'admission_date', None),
                date_joined=getattr(obj, 'date_joined', None),
                # Academic fields
                class_name=getattr(obj.class_enrolled, 'class_name', None) if hasattr(obj, 'class_enrolled') and obj.class_enrolled else None,
                department_name=getattr(obj.department, 'department_name', None) if hasattr(obj, 'department') and obj.department else None,
                designation=getattr(obj, 'designation', ''),
                qualification=getattr(obj, 'qualification', ''),
                experience_years=getattr(obj, 'experience_years', None),
                # Contact and address
                residential_address=getattr(obj, 'residential_address', ''),
                office_address=getattr(obj, 'office_address', ''),
                emergency_contact_name=getattr(obj, 'emergency_contact_name', ''),
                emergency_contact_relationship=getattr(obj, 'emergency_contact_relationship', ''),
                emergency_contact_no=getattr(obj, 'emergency_contact_no', ''),
                # Additional info
                nationality=getattr(obj, 'nationality', ''),
                blood_group=getattr(obj, 'blood_group', None),
                profile_picture=getattr(obj, 'profile_picture', ''),
                occupation=getattr(obj, 'occupation', ''),  # For parents
                bio=getattr(obj, 'bio', ''),  # For principals
                reason='User account deleted'
            )
            
            # Found and backed up, exit loop
            break
            
        except table.DoesNotExist:
            continue


def _create_student_record(email):
    """Create a Student record with default values."""
    if not Student.objects.filter(email=email).exists():
        Student.objects.create(
            email=email,
            fullname='',
            student_id=None,
            phone='',
            date_of_birth=None,
            gender='',
            admission_date=None,
            class_enrolled=None,
            parent=None,
            profile_picture='',
            residential_address='',
            emergency_contact_name='',
            emergency_contact_relationship='',
            emergency_contact_no='',
            nationality='',
            blood_group=None
        )


def _create_teacher_record(email):
    """Create a Teacher record with default values."""
    if not Teacher.objects.filter(email=email).exists():
        Teacher.objects.create(
            email=email,
            fullname='',
            teacher_id=None,
            phone='',
            date_of_birth=None,
            gender='',
            date_joined=None,
            department=None,
            qualification='',
            experience_years=None,
            profile_picture='',
            residential_address='',
            emergency_contact_name='',
            emergency_contact_relationship='',
            emergency_contact_no='',
            nationality='',
            blood_group=None,
            is_classteacher=False
        )


def _create_principal_record(email):
    """Create a Principal record with default values."""
    if not Principal.objects.filter(email=email).exists():
        Principal.objects.create(
            email=email,
            fullname='',
            phone='',
            date_of_birth=None,
            date_joined=None,
            qualification='',
            total_experience=None,
            bio='',
            profile_picture='',
            office_address=''
        )


def _create_management_record(email):
    """Create a Management record with default values."""
    if not Management.objects.filter(email=email).exists():
        Management.objects.create(
            email=email,
            fullname='',
            phone='',
            designation='',
            date_of_birth=None,
            date_joined=None,
            department=None,
            profile_picture='',
            office_address=''
        )


def _create_admin_record(email):
    """Create an Admin record with default values."""
    if not Admin.objects.filter(email=email).exists():
        Admin.objects.create(
            email=email,
            fullname='',
            phone='',
            office_address='',
            profile_picture=''
        )


def _create_parent_record(email):
    """Create a Parent record with default values."""
    if not Parent.objects.filter(email=email).exists():
        Parent.objects.create(
            email=email,
            fullname='',
            phone='',
            occupation='',
            residential_address='',
            profile_picture='',
            relationship_to_student=''
        )


# ===============================================================
# OPTIONAL: HANDLE ROLE CHANGES WITH APPROVAL
# ===============================================================

@receiver(post_save, sender=User)
def handle_user_approval_change(sender, instance, created, update_fields, **kwargs):
    """
    Handle when a user's approval status changes from False to True.
    This ensures role records are created when user gets approved.
    """
    # Skip if this is a new user creation (handled by main signal)
    if created:
        return
    
    # Check if is_approved was updated
    if update_fields and 'is_approved' in update_fields:
        if instance.is_approved:
            # User was just approved, ensure role record exists
            manage_role_tables_on_user_save(sender, instance, created=False)
        else:
            # User approval was revoked, clean up role records
            with transaction.atomic():
                _cleanup_role_records(instance.email)
