from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from datetime import datetime


# ------------------- USER MANAGER -------------------
class UserManager(BaseUserManager):

    def create_user(self, email, role, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, role=role, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, role='Admin', password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_approved', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, role, password, **extra_fields)


# ------------------- USER MODEL -------------------
class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('Student', 'Student'),
        ('Teacher', 'Teacher'),
        ('Principal', 'Principal'),
        ('Management', 'Management'),
        ('Admin', 'Admin'),
        ('Parent', 'Parent'),
    ]
    
    email = models.EmailField(primary_key=True, max_length=254)
    role = models.CharField(max_length=30, choices=ROLE_CHOICES)
    is_active = models.BooleanField(default=True)  # type: ignore[call-arg]
    is_staff = models.BooleanField(default=False)  # type: ignore[call-arg]
    is_approved = models.BooleanField(default=False)  # type: ignore[call-arg]
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['role']

    objects: UserManager = UserManager()  # type: ignore[assignment]

    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return f"{self.email} ({self.role}) - {'Approved' if self.is_approved else 'Pending'}"


# ------------------- DEPARTMENT -------------------
class Department(models.Model):
    department_name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.department_name)


# ------------------- CLASS/GRADE -------------------
# Removed discrete Class model; using string fields on Student/FeeStructure/Timetable


# ------------------- SUBJECT -------------------
class Subject(models.Model):
    subject_name = models.CharField(max_length=100)
    subject_code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.subject_name} ({self.subject_code})"


# ------------------- STUDENT -------------------
class Student(models.Model):
    email = models.OneToOneField(User, on_delete=models.CASCADE, to_field='email', primary_key=True)
    fullname = models.CharField(max_length=255)
    student_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, null=True, blank=True)
    admission_date = models.DateField(null=True, blank=True)
    class_name = models.CharField(max_length=50, null=True, blank=True)
    section = models.CharField(max_length=10, null=True, blank=True)
    parent = models.ForeignKey('Parent', on_delete=models.SET_NULL, null=True, blank=True, related_name='children', to_field='email')
    profile_picture = models.URLField(null=True, blank=True)
    residential_address = models.TextField(null=True, blank=True)
    emergency_contact_name = models.CharField(max_length=100, null=True, blank=True)
    emergency_contact_relationship = models.CharField(max_length=50, null=True, blank=True)
    emergency_contact_no = models.CharField(max_length=20, null=True, blank=True)
    nationality = models.CharField(max_length=50, null=True, blank=True)
    
    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    ]
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES, null=True, blank=True)

    def __str__(self):
        return f"{self.fullname} ({self.student_id})"


# ------------------- TEACHER -------------------
class Teacher(models.Model):
    email = models.OneToOneField(User, on_delete=models.CASCADE, to_field='email', primary_key=True)
    fullname = models.CharField(max_length=255)
    teacher_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, null=True, blank=True)
    date_joined = models.DateField(null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='teachers')
    subjects = models.ManyToManyField(Subject, related_name='teachers', blank=True)
    qualification = models.CharField(max_length=255, null=True, blank=True)
    experience_years = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    profile_picture = models.URLField(null=True, blank=True)
    residential_address = models.TextField(null=True, blank=True)
    emergency_contact_name = models.CharField(max_length=100, null=True, blank=True)
    emergency_contact_relationship = models.CharField(max_length=50, null=True, blank=True)
    emergency_contact_no = models.CharField(max_length=20, null=True, blank=True)
    nationality = models.CharField(max_length=50, null=True, blank=True)
    
    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    ]
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES, null=True, blank=True)

    def __str__(self):
        return f"{self.fullname} ({self.teacher_id})"


# ------------------- PRINCIPAL -------------------
class Principal(models.Model):
    email = models.OneToOneField(User, on_delete=models.CASCADE, to_field='email', primary_key=True)
    fullname = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    date_joined = models.DateField(null=True, blank=True)
    qualification = models.CharField(max_length=255, null=True, blank=True)
    total_experience = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    profile_picture = models.URLField(null=True, blank=True)
    office_address = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.fullname} (Principal)"


# ------------------- MANAGEMENT -------------------
class Management(models.Model):
    email = models.OneToOneField(User, on_delete=models.CASCADE, to_field='email', primary_key=True)
    fullname = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, null=True, blank=True)
    designation = models.CharField(max_length=100, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    date_joined = models.DateField(null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='management_staff')
    profile_picture = models.URLField(null=True, blank=True)
    office_address = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "Management Staff"

    def __str__(self):
        return f"{self.fullname} (Management - {self.designation})"


# ------------------- ADMIN -------------------
class Admin(models.Model):
    email = models.OneToOneField(User, on_delete=models.CASCADE, to_field='email', primary_key=True)
    fullname = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, null=True, blank=True)
    office_address = models.TextField(null=True, blank=True)
    profile_picture = models.URLField(null=True, blank=True)

    def __str__(self):
        return f"{self.fullname} (Admin)"


# ------------------- PARENT -------------------
class Parent(models.Model):
    email = models.OneToOneField(User, on_delete=models.CASCADE, to_field='email', primary_key=True)
    fullname = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, null=True, blank=True)
    occupation = models.CharField(max_length=100, null=True, blank=True)
    residential_address = models.TextField(null=True, blank=True)
    profile_picture = models.URLField(null=True, blank=True)
    relationship_to_student = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"{self.fullname} (Parent)"


# ------------------- ATTENDANCE -------------------
class Attendance(models.Model):
    student: Student = models.ForeignKey(Student, on_delete=models.CASCADE, to_field='email', related_name='attendance_records')  # type: ignore[assignment]
    class_name = models.CharField(max_length=50, null=True, blank=True)
    date = models.DateField()
    status = models.CharField(max_length=20, choices=[
        ('Present', 'Present'),
        ('Absent', 'Absent'),
    ])
    marked_by_role = models.CharField(max_length=20, choices=[
        ('Student', 'Student'),
        ('Teacher', 'Teacher'),
        ('Principal', 'Principal'),
        ('Management', 'Management'),
        ('Admin', 'Admin'),
    ], default='Admin')
    remarks = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['student', 'date']
        ordering = ['-date']

    def __str__(self):
        return f"{self.student.fullname} - {self.date} - {self.status}"


# ------------------- GRADE/MARKS -------------------
class Grade(models.Model):
    student: Student = models.ForeignKey(Student, on_delete=models.CASCADE, to_field='email', related_name='grades')  # type: ignore[assignment]
    subject: Subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='grades')  # type: ignore[assignment]
    teacher: Teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, to_field='email', related_name='grades_given')  # type: ignore[assignment]
    exam_type = models.CharField(max_length=50, choices=[
        ('Quiz', 'Quiz'),
        ('Midterm', 'Midterm'),
        ('Final', 'Final'),
        ('Assignment', 'Assignment'),
        ('Project', 'Project'),
    ])
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2)
    total_marks = models.DecimalField(max_digits=5, decimal_places=2)
    exam_date = models.DateField(null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student.fullname} - {self.subject.subject_name} - {self.exam_type}"

    @property
    def percentage(self):
        if self.total_marks > 0:  # type: ignore[operator]
            return (self.marks_obtained / self.total_marks) * 100  # type: ignore[operator]
        return 0


# ------------------- FEE STRUCTURE -------------------
class FeeStructure(models.Model):
    class_name = models.CharField(max_length=50)
    fee_type = models.CharField(max_length=100, choices=[
        ('Tuition', 'Tuition Fee'),
        ('Transport', 'Transport Fee'),
        ('Library', 'Library Fee'),
        ('Sports', 'Sports Fee'),
        ('Lab', 'Lab Fee'),
        ('Other', 'Other Fee'),
    ])
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    frequency = models.CharField(max_length=50, choices=[
        ('Monthly', 'Monthly'),
        ('Quarterly', 'Quarterly'),
        ('Annually', 'Annually'),
        ('One-time', 'One-time'),
    ])
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.class_name} - {self.fee_type} - {self.amount}"


# ------------------- FEE PAYMENT -------------------
class FeePayment(models.Model):
    student: Student = models.ForeignKey(Student, on_delete=models.CASCADE, to_field='email', related_name='fee_payments')  # type: ignore[assignment]
    fee_structure: FeeStructure = models.ForeignKey(FeeStructure, on_delete=models.CASCADE, related_name='payments')  # type: ignore[assignment]
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=50, choices=[
        ('Cash', 'Cash'),
        ('Card', 'Card'),
        ('Bank Transfer', 'Bank Transfer'),
        ('Online', 'Online Payment'),
        ('Cheque', 'Cheque'),
    ])
    transaction_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('Paid', 'Paid'),
        ('Pending', 'Pending'),
        ('Failed', 'Failed'),
    ], default='Paid')
    remarks = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student.fullname} - {self.fee_structure.fee_type} - {self.amount_paid}"


# ------------------- TIMETABLE -------------------
class Timetable(models.Model):
    class_name = models.CharField(max_length=50)
    subject: Subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='timetable_entries')  # type: ignore[assignment]
    teacher: Teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, to_field='email', related_name='timetable_entries')  # type: ignore[assignment]
    day_of_week = models.CharField(max_length=20, choices=[
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
    ])
    start_time = models.TimeField()
    end_time = models.TimeField()
    room_number = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['day_of_week', 'start_time']

    def __str__(self):
        return f"{self.class_name} - {self.subject.subject_name} - {self.day_of_week} {self.start_time}-{self.end_time}"


# ------------------- FORMER MEMBER (BACKUP) -------------------
class FormerMember(models.Model):
    """
    Backup table for storing information about users who left the school.
    This table is completely independent and stores email as a string field,
    so it's never affected by User deletions.
    """
    email = models.EmailField(primary_key=True, max_length=254)
    fullname = models.CharField(max_length=255, null=True, blank=True)
    role = models.CharField(max_length=30, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, null=True, blank=True)
    
    # Student/Teacher specific fields
    student_id = models.CharField(max_length=50, null=True, blank=True)
    teacher_id = models.CharField(max_length=50, null=True, blank=True)
    admission_date = models.DateField(null=True, blank=True)
    date_joined = models.DateField(null=True, blank=True)
    
    # Academic fields
    class_name = models.CharField(max_length=50, null=True, blank=True)
    department_name = models.CharField(max_length=100, null=True, blank=True)
    designation = models.CharField(max_length=100, null=True, blank=True)
    qualification = models.CharField(max_length=255, null=True, blank=True)
    experience_years = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    
    # Contact and address
    residential_address = models.TextField(null=True, blank=True)
    office_address = models.TextField(null=True, blank=True)
    emergency_contact_name = models.CharField(max_length=100, null=True, blank=True)
    emergency_contact_relationship = models.CharField(max_length=50, null=True, blank=True)
    emergency_contact_no = models.CharField(max_length=20, null=True, blank=True)
    
    # Additional info
    nationality = models.CharField(max_length=50, null=True, blank=True)
    blood_group = models.CharField(max_length=3, null=True, blank=True)
    profile_picture = models.URLField(null=True, blank=True)
    occupation = models.CharField(max_length=100, null=True, blank=True)  # For parents
    bio = models.TextField(null=True, blank=True)  # For principals
    
    # Metadata
    left_date = models.DateTimeField(auto_now_add=True)
    reason = models.TextField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Former Member"
        verbose_name_plural = "Former Members"
        ordering = ['-left_date']
    
    def __str__(self):
        return f"{self.email} - {self.role} (Left: {self.left_date.strftime('%Y-%m-%d')})"


# ------------------- DOCUMENT -------------------
class Document(models.Model):
    email = models.OneToOneField(User, on_delete=models.CASCADE, to_field='email', related_name='document')
    tenth = models.URLField(null=True, blank=True)
    twelth = models.URLField(null=True, blank=True)
    degree = models.URLField(null=True, blank=True)
    masters = models.URLField(null=True, blank=True)
    marks_card = models.URLField(null=True, blank=True)
    certificates = models.URLField(null=True, blank=True)
    award = models.URLField(null=True, blank=True)
    resume = models.URLField(null=True, blank=True)
    id_proof = models.URLField(null=True, blank=True)
    appointment_letter = models.URLField(null=True, blank=True)
    offer_letter = models.URLField(null=True, blank=True)
    releaving_letter = models.URLField(null=True, blank=True)
    resignation_letter = models.URLField(null=True, blank=True)
    achievement_crt = models.URLField(null=True, blank=True)
    bonafide_crt = models.URLField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Documents for {self.email.email}"


# ------------------- AWARD -------------------
class Award(models.Model):
    email = models.ForeignKey(User, on_delete=models.CASCADE, to_field='email', related_name='awards')
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    photo = models.URLField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.email}"


# ------------------- NOTICE -------------------
class Notice(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    message = models.TextField()
    email = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, to_field='email', related_name='notices')
    posted_date = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField(null=True, blank=True)
    important = models.BooleanField(default=False)
    attachment = models.FileField(upload_to='notices/', null=True, blank=True)
    notice_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, to_field='email', related_name='notices_by')
    notice_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, to_field='email', related_name='notices_to')

    class Meta:
        ordering = ['-posted_date']

    def __str__(self) -> str:
        return str(self.title)


# ------------------- TICKET (Issues DB) -------------------
class Issue(models.Model):
    STATUS_CHOICES = [('Open','Open'),('In Progress','In Progress'),('Closed','Closed')]
    PRIORITY_CHOICES = [('Low','Low'),('Medium','Medium'),('High','High'),('Urgent','Urgent')]

    subject = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Open')
    description = models.TextField(blank=True, null=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='Medium')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_description = models.TextField(blank=True, null=True)
    raised_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, to_field='email', related_name='tickets_assigned_by')
    raised_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, to_field='email', related_name='tickets_assigned_to')
    closed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, to_field='email', related_name='tickets_closed_by')
    closed_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, to_field='email', related_name='tickets_closed_to')

    class Meta:
        ordering = ['-created_at']
        db_table = 'school_issues'

    def __str__(self):
        return f"{self.subject} - {self.status}"


# ------------------- HOLIDAY -------------------
class Holiday(models.Model):
    name = models.CharField(max_length=255)
    date = models.DateField()
    type = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default="India")
    year = models.PositiveIntegerField()
    month = models.PositiveIntegerField()
    weekday = models.CharField(max_length=10, blank=True)

    class Meta:
        unique_together = ('date', 'country')
        ordering = ['date']

    def save(self, *args, **kwargs):
        if isinstance(self.date, str):
            self.date = datetime.strptime(self.date, '%Y-%m-%d').date()
        self.weekday = self.date.strftime('%A')
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.date} - {self.weekday})"
