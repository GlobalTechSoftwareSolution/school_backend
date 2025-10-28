from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    User, Student, Teacher, Principal, Management, Admin, Parent,
    Department, Class, Subject, Attendance, Grade, FeeStructure,
    FeePayment, Timetable, FormerMember
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


# ------------------- CLASS SERIALIZER -------------------
class ClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = Class
        fields = '__all__'


# ------------------- SUBJECT SERIALIZER -------------------
class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = '__all__'


# ------------------- STUDENT SERIALIZERS -------------------
class StudentSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='email', read_only=True)
    class_name = serializers.CharField(source='class_enrolled.class_name', read_only=True)
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
    student_name = serializers.CharField(source='student.fullname', read_only=True)
    class_name = serializers.CharField(source='class_enrolled.class_name', read_only=True)

    class Meta:
        model = Attendance
        fields = '__all__'


class AttendanceCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = '__all__'


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
    class_name = serializers.CharField(source='class_level.class_name', read_only=True)

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
    class_name = serializers.CharField(source='class_enrolled.class_name', read_only=True)
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
