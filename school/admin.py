from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, Department, Class, Subject, Student, Teacher, Principal,
    Management, Admin as SchoolAdmin, Parent, Attendance, Grade,
    FeeStructure, FeePayment, Timetable, FormerMember
)


# ------------------- CUSTOM USER ADMIN -------------------
class CustomUserAdmin(BaseUserAdmin):
    list_display = ('email', 'role', 'is_approved', 'is_active', 'is_staff', 'created_at')
    list_filter = ('role', 'is_approved', 'is_active', 'is_staff', 'is_superuser')
    search_fields = ('email',)
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('role',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'is_approved', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'role', 'password1', 'password2', 'is_approved'),
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'last_login')
    
    actions = ['approve_users', 'reject_users']
    
    @admin.action(description="Approve selected users")
    def approve_users(self, request, queryset):
        queryset.update(is_approved=True)
        self.message_user(request, f"{queryset.count()} users approved successfully.")
    
    @admin.action(description="Reject selected users")
    def reject_users(self, request, queryset):
        queryset.update(is_approved=False)
        self.message_user(request, f"{queryset.count()} users rejected.")


# ------------------- DEPARTMENT ADMIN -------------------
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('department_name', 'created_at', 'updated_at')
    search_fields = ('department_name',)
    readonly_fields = ('created_at', 'updated_at')


# ------------------- SUBJECT ADMIN -------------------
@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('subject_name', 'subject_code', 'created_at')
    search_fields = ('subject_name', 'subject_code')
    readonly_fields = ('created_at', 'updated_at')


# ------------------- CLASS ADMIN -------------------
@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ('class_name', 'sec', 'class_teacher', 'created_at')
    search_fields = ('class_name', 'sec', 'class_teacher__fullname')
    list_filter = ('class_name', 'sec')
    readonly_fields = ('created_at', 'updated_at')


# ------------------- STUDENT ADMIN -------------------
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'fullname', 'email', 'class_fk', 'admission_date')
    search_fields = ('fullname', 'student_id', 'email__email')
    list_filter = ('class_fk', 'gender', 'admission_date')
    readonly_fields = ('email',)


# ------------------- TEACHER ADMIN -------------------
@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('teacher_id', 'fullname', 'email', 'department', 'date_joined')
    search_fields = ('fullname', 'teacher_id', 'email__email')
    list_filter = ('department', 'date_joined')
    filter_horizontal = ('subjects',)
    readonly_fields = ('email',)


# ------------------- PRINCIPAL ADMIN -------------------
@admin.register(Principal)
class PrincipalAdmin(admin.ModelAdmin):
    list_display = ('fullname', 'email', 'phone', 'date_joined')
    search_fields = ('fullname', 'email__email')
    readonly_fields = ('email',)


# ------------------- MANAGEMENT ADMIN -------------------
@admin.register(Management)
class ManagementAdmin(admin.ModelAdmin):
    list_display = ('fullname', 'email', 'designation', 'department', 'date_joined')
    search_fields = ('fullname', 'email__email', 'designation')
    list_filter = ('department', 'date_joined')
    readonly_fields = ('email',)


# ------------------- SCHOOL ADMIN -------------------
@admin.register(SchoolAdmin)
class SchoolAdminAdmin(admin.ModelAdmin):
    list_display = ('fullname', 'email', 'phone')
    search_fields = ('fullname', 'email__email')
    readonly_fields = ('email',)


# ------------------- PARENT ADMIN -------------------
@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ('fullname', 'email', 'phone', 'occupation')
    search_fields = ('fullname', 'email__email')
    readonly_fields = ('email',)


# ------------------- ATTENDANCE ADMIN -------------------
@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'class_fk', 'date', 'status')
    search_fields = ('student__fullname', 'student__student_id')
    list_filter = ('status', 'date', 'class_fk')
    date_hierarchy = 'date'
    readonly_fields = ()


# ------------------- GRADE ADMIN -------------------
@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'exam_type', 'marks_obtained', 'total_marks', 'percentage', 'exam_date')
    search_fields = ('student__fullname', 'student__student_id', 'subject__subject_name')
    list_filter = ('exam_type', 'subject', 'exam_date')
    readonly_fields = ('created_at', 'updated_at')


# ------------------- FEE STRUCTURE ADMIN -------------------
@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ('class_fk', 'fee_type', 'amount', 'frequency')
    search_fields = ('class_fk__class_name', 'fee_type')
    list_filter = ('fee_type', 'frequency', 'class_fk')
    readonly_fields = ('created_at', 'updated_at')


# ------------------- FEE PAYMENT ADMIN -------------------
@admin.register(FeePayment)
class FeePaymentAdmin(admin.ModelAdmin):
    list_display = ('student', 'fee_structure', 'amount_paid', 'payment_date', 'payment_method', 'status')
    search_fields = ('student__fullname', 'student__student_id', 'transaction_id')
    list_filter = ('status', 'payment_method', 'payment_date')
    date_hierarchy = 'payment_date'
    readonly_fields = ('created_at', 'updated_at')


# ------------------- TIMETABLE ADMIN -------------------
@admin.register(Timetable)
class TimetableAdmin(admin.ModelAdmin):
    list_display = ('class_fk', 'subject', 'teacher', 'day_of_week', 'start_time', 'end_time', 'room_number')
    search_fields = ('class_fk__class_name', 'subject__subject_name', 'teacher__fullname')
    list_filter = ('day_of_week', 'class_fk')
    readonly_fields = ('created_at', 'updated_at')


# ------------------- FORMER MEMBER ADMIN -------------------
@admin.register(FormerMember)
class FormerMemberAdmin(admin.ModelAdmin):
    list_display = ('email', 'fullname', 'role', 'left_date', 'phone')
    search_fields = ('email', 'fullname', 'student_id', 'teacher_id')
    list_filter = ('role', 'left_date', 'gender')
    date_hierarchy = 'left_date'
    readonly_fields = ('left_date',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('email', 'fullname', 'role', 'phone', 'date_of_birth', 'gender')
        }),
        ('Academic Information', {
            'fields': ('student_id', 'teacher_id', 'admission_date', 'date_joined', 'class_name', 'department_name', 'designation', 'qualification', 'experience_years')
        }),
        ('Contact & Address', {
            'fields': ('residential_address', 'office_address', 'emergency_contact_name', 'emergency_contact_relationship', 'emergency_contact_no')
        }),
        ('Additional Information', {
            'fields': ('nationality', 'blood_group', 'profile_picture', 'occupation', 'bio')
        }),
        ('Departure Information', {
            'fields': ('left_date', 'reason')
        }),
    )


# Register User model
admin.site.register(User, CustomUserAdmin)
