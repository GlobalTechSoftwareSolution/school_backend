from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    User, Student, Teacher, Principal, Management, Admin, Parent,
    Department, Subject, Attendance, Grade, FeeStructure,
    FeePayment, Timetable, FormerMember, Document, Notice, Issue, Holiday, Award,
    Assignment, Leave, Task, Project, Program, Activity, Report, FinanceTransaction, TransportDetails,
)

UserModel = get_user_model()


# ------------------- USER SERIALIZERS -------------------
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'role', 'is_active', 'is_approved', 'is_staff', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at', 'is_staff']


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'}, label='Confirm Password')

    class Meta:
        model = User
        fields = ['email', 'role', 'password', 'password2']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(
            email=validated_data['email'],
            role=validated_data['role'],
            password=validated_data['password']
        )
        return user


# ------------------- DEPARTMENT SERIALIZER -------------------
class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'


# ------------------- SUBJECT SERIALIZER -------------------
class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = '__all__'


# ------------------- STUDENT SERIALIZERS -------------------
class StudentSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='email', read_only=True)
    # class_name and section are direct fields now
    parent_name = serializers.CharField(source='parent.fullname', read_only=True, allow_null=True)

    class Meta:
        model = Student
        fields = '__all__'


class StudentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = '__all__'


# ------------------- TEACHER SERIALIZERS -------------------
class TeacherSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='email', read_only=True)
    department_name = serializers.CharField(source='department.department_name', read_only=True, allow_null=True)
    subject_list = SubjectSerializer(source='subjects', many=True, read_only=True)

    class Meta:
        model = Teacher
        fields = '__all__'


class TeacherCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Teacher
        fields = '__all__'


# ------------------- PRINCIPAL SERIALIZER -------------------
class PrincipalSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='email', read_only=True)

    class Meta:
        model = Principal
        fields = '__all__'


# ------------------- MANAGEMENT SERIALIZER -------------------
class ManagementSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='email', read_only=True)
    department_name = serializers.CharField(source='department.department_name', read_only=True, allow_null=True)

    class Meta:
        model = Management
        fields = '__all__'


# ------------------- ADMIN SERIALIZER -------------------
class AdminSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='email', read_only=True)

    class Meta:
        model = Admin
        fields = '__all__'


# ------------------- PARENT SERIALIZER -------------------
class ParentSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='email', read_only=True)
    children_list = StudentSerializer(source='children', many=True, read_only=True)

    class Meta:
        model = Parent
        fields = '__all__'


# ------------------- ATTENDANCE SERIALIZERS -------------------
class AttendanceSerializer(serializers.ModelSerializer):
    student_email = serializers.EmailField(source='student.email', read_only=True)
    student_name = serializers.CharField(source='student.fullname', read_only=True)
    check_in = serializers.TimeField(format='%H:%M:%S', read_only=True)
    check_out = serializers.TimeField(format='%H:%M:%S', read_only=True)
    date = serializers.DateField(format='%Y-%m-%d', read_only=True)

    class Meta:
        model = Attendance
        fields = ['id', 'student_email', 'student_name', 'class_name', 'date', 
                 'check_in', 'check_out', 'status', 'marked_by_role']
        read_only_fields = ['status']


class AttendanceCreateSerializer(serializers.ModelSerializer):
    student_email = serializers.EmailField(write_only=True)
    
    class Meta:
        model = Attendance
        fields = ['student_email', 'class_name', 'marked_by_role']
        extra_kwargs = {
            'student_email': {'required': True},
            'class_name': {'required': True},
            'marked_by_role': {'required': False}
        }
    
    def create(self, validated_data):
        # Get the student instance from the email
        student_email = validated_data.pop('student_email')
        try:
            student = Student.objects.get(email=student_email)
        except Student.DoesNotExist:
            raise serializers.ValidationError({'student_email': 'Student with this email does not exist.'})
        
        validated_data['student'] = student
        return super().create(validated_data)


class AttendanceUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = ['check_out', 'class_name', 'marked_by_role', 'status']
        read_only_fields = ['student', 'date', 'check_in']


# ------------------- GRADE SERIALIZERS -------------------
class GradeSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.fullname', read_only=True)
    subject_name = serializers.CharField(source='subject.subject_name', read_only=True)
    teacher_name = serializers.CharField(source='teacher.fullname', read_only=True, allow_null=True)
    percentage = serializers.ReadOnlyField()

    class Meta:
        model = Grade
        fields = '__all__'


class GradeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grade
        fields = '__all__'


# ------------------- FEE STRUCTURE SERIALIZER -------------------
class FeeStructureSerializer(serializers.ModelSerializer):
    # class_name is a direct field now

    class Meta:
        model = FeeStructure
        fields = '__all__'


# ------------------- FEE PAYMENT SERIALIZERS -------------------
class FeePaymentSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.fullname', read_only=True)
    fee_type = serializers.CharField(source='fee_structure.fee_type', read_only=True)

    class Meta:
        model = FeePayment
        fields = '__all__'


class FeePaymentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeePayment
        fields = '__all__'


# ------------------- TIMETABLE SERIALIZERS -------------------
class TimetableSerializer(serializers.ModelSerializer):
    # class_name is a direct field now
    subject_name = serializers.CharField(source='subject.subject_name', read_only=True)
    teacher_name = serializers.CharField(source='teacher.fullname', read_only=True, allow_null=True)

    class Meta:
        model = Timetable
        fields = '__all__'


class TimetableCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Timetable
        fields = '__all__'


# ------------------- FORMER MEMBER SERIALIZER -------------------
class FormerMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormerMember
        fields = '__all__'
        read_only_fields = ['left_date']


# ------------------- DOCUMENT -------------------
class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = '__all__'


# ------------------- NOTICE -------------------
class NoticeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notice
        fields = '__all__'


# ------------------- ISSUE -------------------
class IssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Issue
        fields = '__all__'


# ------------------- HOLIDAY -------------------
class HolidaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Holiday
        fields = '__all__'


# ------------------- AWARD -------------------
class AwardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Award
        fields = '__all__'


# ------------------- ASSIGNMENT -------------------
class AssignmentSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.subject_name', read_only=True)

    class Meta:
        model = Assignment
        fields = '__all__'


# ------------------- LEAVE -------------------
class LeaveSerializer(serializers.ModelSerializer):
    applicant_email = serializers.EmailField(source='applicant.email', read_only=True)
    approved_by_email = serializers.EmailField(source='approved_by.email', read_only=True, allow_null=True)

    class Meta:
        model = Leave
        fields = '__all__'


# ------------------- TASK -------------------
class TaskSerializer(serializers.ModelSerializer):
    assigned_to_email = serializers.EmailField(source='assigned_to.email', read_only=True, allow_null=True)
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True, allow_null=True)

    class Meta:
        model = Task
        fields = '__all__'


# ------------------- PROJECT -------------------
class ProjectSerializer(serializers.ModelSerializer):
    owner_email = serializers.EmailField(source='owner.email', read_only=True, allow_null=True)

    class Meta:
        model = Project
        fields = '__all__'


# ------------------- PROGRAM -------------------
class ProgramSerializer(serializers.ModelSerializer):
    coordinator_email = serializers.EmailField(source='coordinator.email', read_only=True, allow_null=True)

    class Meta:
        model = Program
        fields = '__all__'


# ------------------- ACTIVITY -------------------
class ActivitySerializer(serializers.ModelSerializer):
    conducted_by_email = serializers.EmailField(source='conducted_by.email', read_only=True, allow_null=True)

    class Meta:
        model = Activity
        fields = '__all__'


# ------------------- REPORT -------------------
class ReportSerializer(serializers.ModelSerializer):
    student_email = serializers.EmailField(source='student.email', read_only=True, allow_null=True)
    teacher_email = serializers.EmailField(source='teacher.email', read_only=True, allow_null=True)
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True, allow_null=True)

    class Meta:
        model = Report
        fields = '__all__'


# ------------------- FINANCE TRANSACTION -------------------
class FinanceTransactionSerializer(serializers.ModelSerializer):
    recorded_by_email = serializers.EmailField(source='recorded_by.email', read_only=True, allow_null=True)

    class Meta:
        model = FinanceTransaction
        fields = '__all__'


# ------------------- TRANSPORT DETAILS -------------------
class TransportDetailsSerializer(serializers.ModelSerializer):
    student_email = serializers.EmailField(source='student.email', read_only=True)

    class Meta:
        model = TransportDetails
        fields = '__all__'
