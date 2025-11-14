from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    User, Student, Teacher, Principal, Management, Admin, Parent,
    Department, Subject, Attendance, Grade, FeeStructure,
    FeePayment, Timetable, FormerMember, Document, Notice, Issue, Holiday, Award,
    Assignment, SubmittedAssignment, Leave, Task, Project, Program, Activity, Report, FinanceTransaction, TransportDetails, Class, IDCard
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


# ------------------- CLASS SERIALIZER -------------------
class ClassSerializer(serializers.ModelSerializer):
    class_teacher_name = serializers.CharField(source='class_teacher.fullname', read_only=True, allow_null=True)
    
    class Meta:
        model = Class
        fields = '__all__'


# ------------------- STUDENT SERIALIZERS -------------------
class StudentSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='email.email', read_only=True)
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
    class_name = serializers.CharField(source='class_id.class_name', read_only=True, allow_null=True)

    class Meta:
        model = Teacher
        fields = '__all__'


class TeacherCreateSerializer(serializers.ModelSerializer):
    subjects = serializers.PrimaryKeyRelatedField(queryset=Subject.objects.all(), many=True, required=False)
    
    class Meta:
        model = Teacher
        fields = '__all__'
        
    def create(self, validated_data):
        subjects = validated_data.pop('subjects', [])
        # Ensure is_classteacher is initialized if not provided
        if 'is_classteacher' not in validated_data:
            validated_data['is_classteacher'] = False
        teacher = Teacher.objects.create(**validated_data)
        if subjects:
            teacher.subjects.set(subjects)
        return teacher
        
    def update(self, instance, validated_data):
        subjects = validated_data.pop('subjects', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if subjects is not None:
            instance.subjects.set(subjects)
        return instance


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
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()
    check_in = serializers.TimeField(format='%H:%M:%S', read_only=True)
    check_out = serializers.TimeField(format='%H:%M:%S', read_only=True)
    date = serializers.DateField(format='%Y-%m-%d', read_only=True)

    class Meta:
        model = Attendance
        fields = ['id', 'user_email', 'user_name', 'date', 
                 'check_in', 'check_out', 'status', 'role', 'remarks']
        read_only_fields = ['status', 'role']
        
    def get_user_name(self, obj):
        # Try to get the name from the related user profile
        if hasattr(obj.user, 'admin') and obj.user.admin:
            return obj.user.admin.fullname
        elif hasattr(obj.user, 'teacher') and obj.user.teacher:
            return obj.user.teacher.fullname
        elif hasattr(obj.user, 'principal') and obj.user.principal:
            return obj.user.principal.fullname
        elif hasattr(obj.user, 'management') and obj.user.management:
            return obj.user.management.fullname
        elif hasattr(obj.user, 'student') and obj.user.student:
            return obj.user.student.fullname
        elif hasattr(obj.user, 'parent') and obj.user.parent:
            return obj.user.parent.fullname
        else:
            # Fallback to email if no name found
            return obj.user.email


class AttendanceCreateSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(write_only=True)
    
    class Meta:
        model = Attendance
        fields = ['user_email', 'remarks']
        extra_kwargs = {
            'user_email': {'required': True},
            'remarks': {'required': False}
        }
    
    def create(self, validated_data):
        # Get the user instance from the email
        user_email = validated_data.pop('user_email')
        
        try:
            user = User.objects.get(email=user_email)
        except User.DoesNotExist:
            raise serializers.ValidationError({'user_email': 'User with this email does not exist.'})
        
        # Check if user is a parent (parents should not have attendance)
        if user.role == 'Parent':
            raise serializers.ValidationError({'user_email': 'Parents cannot have attendance records.'})
        
        validated_data['user'] = user
        return super().create(validated_data)


class AttendanceUpdateSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Attendance
        fields = ['check_out', 'status', 'remarks']
        read_only_fields = ['user', 'date', 'check_in', 'role']
    
    def update(self, instance, validated_data):
        return super().update(instance, validated_data)


# ------------------- GRADE SERIALIZERS -------------------
class GradeSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.fullname', read_only=True)
    student_class = serializers.CharField(source='student.class_id.class_name', read_only=True)
    student_section = serializers.CharField(source='student.class_id.sec', read_only=True)
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
    notice_by_email = serializers.EmailField(source='notice_by.email', read_only=True, allow_null=True)
    notice_by_name = serializers.SerializerMethodField()
    notice_to_email = serializers.EmailField(source='notice_to.email', read_only=True, allow_null=True)
    notice_to_name = serializers.SerializerMethodField()

    class Meta:
        model = Notice
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # For bulk_create, allow email as string input
        if hasattr(self, 'context') and self.context.get('bulk_create'):
            self.fields['email'] = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), slug_field='email', write_only=True, required=True)
            self.fields['notice_by'] = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), slug_field='email', write_only=True, required=True)
    
    def get_notice_by_name(self, obj):
        if obj.notice_by:
            # Try to get the name from the related user profile
            if hasattr(obj.notice_by, 'admin') and obj.notice_by.admin:
                return obj.notice_by.admin.fullname
            elif hasattr(obj.notice_by, 'teacher') and obj.notice_by.teacher:
                return obj.notice_by.teacher.fullname
            elif hasattr(obj.notice_by, 'principal') and obj.notice_by.principal:
                return obj.notice_by.principal.fullname
            elif hasattr(obj.notice_by, 'management') and obj.notice_by.management:
                return obj.notice_by.management.fullname
            elif hasattr(obj.notice_by, 'student') and obj.notice_by.student:
                return obj.notice_by.student.fullname
            elif hasattr(obj.notice_by, 'parent') and obj.notice_by.parent:
                return obj.notice_by.parent.fullname
            else:
                # Fallback to email if no name found
                return obj.notice_by.email
        return None
    
    def get_notice_to_name(self, obj):
        if obj.notice_to:
            # Try to get the name from the related user profile
            if hasattr(obj.notice_to, 'admin') and obj.notice_to.admin:
                return obj.notice_to.admin.fullname
            elif hasattr(obj.notice_to, 'teacher') and obj.notice_to.teacher:
                return obj.notice_to.teacher.fullname
            elif hasattr(obj.notice_to, 'principal') and obj.notice_to.principal:
                return obj.notice_to.principal.fullname
            elif hasattr(obj.notice_to, 'management') and obj.notice_to.management:
                return obj.notice_to.management.fullname
            elif hasattr(obj.notice_to, 'student') and obj.notice_to.student:
                return obj.notice_to.student.fullname
            elif hasattr(obj.notice_to, 'parent') and obj.notice_to.parent:
                return obj.notice_to.parent.fullname
            else:
                # Fallback to email if no name found
                return obj.notice_to.email
        return None


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
    subject_name = serializers.CharField(source='subject.subject_name', read_only=True, allow_null=True)
    class_name = serializers.CharField(source='class_id.class_name', read_only=True, allow_null=True)
    assigned_by_email = serializers.EmailField(source='assigned_by.email', read_only=True, allow_null=True)
    assigned_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Assignment
        fields = '__all__'
        
    def get_assigned_by_name(self, obj):
        if obj.assigned_by:
            # Try to get the name from the related user profile
            if hasattr(obj.assigned_by, 'admin') and obj.assigned_by.admin:
                return obj.assigned_by.admin.fullname
            elif hasattr(obj.assigned_by, 'teacher') and obj.assigned_by.teacher:
                return obj.assigned_by.teacher.fullname
            elif hasattr(obj.assigned_by, 'principal') and obj.assigned_by.principal:
                return obj.assigned_by.principal.fullname
            elif hasattr(obj.assigned_by, 'management') and obj.assigned_by.management:
                return obj.assigned_by.management.fullname
            elif hasattr(obj.assigned_by, 'student') and obj.assigned_by.student:
                return obj.assigned_by.student.fullname
            elif hasattr(obj.assigned_by, 'parent') and obj.assigned_by.parent:
                return obj.assigned_by.parent.fullname
            else:
                # Fallback to email if no name found
                return obj.assigned_by.email
        return None


class AssignmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assignment
        fields = '__all__'
        
    def create(self, validated_data):
        # Handle the creation of Assignment instances
        return super().create(validated_data)
        
    def update(self, instance, validated_data):
        # Handle the update of Assignment instances
        return super().update(instance, validated_data)

# ------------------- SUBMITTED ASSIGNMENT -------------------
class SubmittedAssignmentSerializer(serializers.ModelSerializer):
    assignment_title = serializers.CharField(source='assignment.title', read_only=True)
    student_name = serializers.CharField(source='student.fullname', read_only=True)
    student_email = serializers.EmailField(source='student.email.email', read_only=True)
    subject_name = serializers.CharField(source='assignment.subject.subject_name', read_only=True)
    class_name = serializers.CharField(source='assignment.class_id.class_name', read_only=True)
    section = serializers.CharField(source='assignment.class_id.sec', read_only=True)

    class Meta:
        model = SubmittedAssignment
        fields = '__all__'


class SubmittedAssignmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubmittedAssignment
        fields = '__all__'
        
    def create(self, validated_data):
        # Handle the creation of SubmittedAssignment instances
        return super().create(validated_data)
        
    def update(self, instance, validated_data):
        # Handle the update of SubmittedAssignment instances
        return super().update(instance, validated_data)

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
    owner_name = serializers.SerializerMethodField()

    class Meta:
        model = Project
        exclude = ['owner']  # Remove the raw owner field to avoid "owner": null in response

    def get_owner_name(self, obj):
        if obj.owner:
            # Try to get the name from the related user profile
            if hasattr(obj.owner, 'admin') and obj.owner.admin:
                return obj.owner.admin.fullname
            elif hasattr(obj.owner, 'teacher') and obj.owner.teacher:
                return obj.owner.teacher.fullname
            elif hasattr(obj.owner, 'principal') and obj.owner.principal:
                return obj.owner.principal.fullname
            elif hasattr(obj.owner, 'management') and obj.owner.management:
                return obj.owner.management.fullname
            elif hasattr(obj.owner, 'student') and obj.owner.student:
                return obj.owner.student.fullname
            elif hasattr(obj.owner, 'parent') and obj.owner.parent:
                return obj.owner.parent.fullname
            else:
                # Fallback to email if no name found
                return obj.owner.email
        return None


# ------------------- PROGRAM -------------------
class ProgramSerializer(serializers.ModelSerializer):
    coordinator_email = serializers.EmailField(source='coordinator.email', read_only=True, allow_null=True)
    coordinator_name = serializers.SerializerMethodField()
    # Add writable fields for coordinator updates
    coordinator = serializers.EmailField(write_only=True, required=False, allow_null=True)
    coordinator_email_input = serializers.EmailField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Program
        fields = ['id', 'name', 'description', 'start_date', 'end_date', 'coordinator', 'coordinator_email_input', 'status', 'created_at', 'updated_at', 'coordinator_email', 'coordinator_name']

    def get_coordinator_name(self, obj):
        if obj.coordinator:
            # Try to get the name from the related user profile
            if hasattr(obj.coordinator, 'admin') and obj.coordinator.admin:
                return obj.coordinator.admin.fullname
            elif hasattr(obj.coordinator, 'teacher') and obj.coordinator.teacher:
                return obj.coordinator.teacher.fullname
            elif hasattr(obj.coordinator, 'principal') and obj.coordinator.principal:
                return obj.coordinator.principal.fullname
            elif hasattr(obj.coordinator, 'management') and obj.coordinator.management:
                return obj.coordinator.management.fullname
            elif hasattr(obj.coordinator, 'student') and obj.coordinator.student:
                return obj.coordinator.student.fullname
            elif hasattr(obj.coordinator, 'parent') and obj.coordinator.parent:
                return obj.coordinator.parent.fullname
            else:
                # Fallback to email if no name found
                return obj.coordinator.email
        return None

    def update(self, instance, validated_data):
        # Handle coordinator updates from either field
        coordinator_email = validated_data.pop('coordinator', None)
        coordinator_email_input = validated_data.pop('coordinator_email_input', None)
        
        # Use coordinator_email_input if coordinator is not provided
        update_email = coordinator_email or coordinator_email_input
        
        if update_email is not None:
            if update_email:
                try:
                    coordinator_user = User.objects.get(email=update_email)
                    instance.coordinator = coordinator_user
                except User.DoesNotExist:
                    raise serializers.ValidationError({'coordinator': f'User with email {update_email} does not exist.'})
            else:
                instance.coordinator = None
        
        return super().update(instance, validated_data)

    def create(self, validated_data):
        # Handle coordinator updates from either field
        coordinator_email = validated_data.pop('coordinator', None)
        coordinator_email_input = validated_data.pop('coordinator_email_input', None)
        
        # Use coordinator_email_input if coordinator is not provided
        update_email = coordinator_email or coordinator_email_input
        
        instance = super().create(validated_data)
        
        if update_email is not None:
            if update_email:
                try:
                    coordinator_user = User.objects.get(email=update_email)
                    instance.coordinator = coordinator_user
                    instance.save()
                except User.DoesNotExist:
                    raise serializers.ValidationError({'coordinator': f'User with email {update_email} does not exist.'})
            else:
                instance.coordinator = None
                instance.save()
        
        return instance


# ------------------- ACTIVITY -------------------
class ActivitySerializer(serializers.ModelSerializer):
    conducted_by_email = serializers.EmailField(source='conducted_by.email', read_only=True, allow_null=True)
    class_id_name = serializers.CharField(source='class_id.class_name', read_only=True, allow_null=True)

    class Meta:
        model = Activity
        fields = ['id', 'name', 'description', 'type', 'date', 'conducted_by', 'conducted_by_email', 
                  'class_id', 'class_id_name', 'attachment', 'created_at', 'updated_at']

    def create(self, validated_data):
        # Handle the creation of Activity instances
        return super().create(validated_data)
        
    def update(self, instance, validated_data):
        # Handle the update of Activity instances
        return super().update(instance, validated_data)

class ActivityCreateSerializer(serializers.ModelSerializer):
    conducted_by_email_input = serializers.EmailField(write_only=True, required=False, allow_null=True)
    class_id_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Activity
        fields = ['name', 'description', 'type', 'date', 'conducted_by', 'conducted_by_email_input',
                  'class_id', 'class_id_id', 'attachment']
        
    def create(self, validated_data):
        # Handle conducted_by from either field
        conducted_by_email = validated_data.pop('conducted_by', None)
        conducted_by_email_input = validated_data.pop('conducted_by_email_input', None)
        
        # Use conducted_by_email_input if conducted_by is not provided
        update_email = conducted_by_email or conducted_by_email_input
        
        # Handle class_id from either field
        class_id = validated_data.pop('class_id', None)
        class_id_id = validated_data.pop('class_id_id', None)
        
        # Use class_id_id if class_id is not provided
        update_class_id = class_id or class_id_id
        
        instance = super().create(validated_data)
        
        if update_email is not None:
            if update_email:
                try:
                    conducted_by_user = User.objects.get(email=update_email)
                    instance.conducted_by = conducted_by_user
                    instance.save()
                except User.DoesNotExist:
                    raise serializers.ValidationError({'conducted_by': f'User with email {update_email} does not exist.'})
            else:
                instance.conducted_by = None
                instance.save()
                
        if update_class_id is not None:
            if update_class_id:
                try:
                    class_obj = Class.objects.get(id=update_class_id)
                    instance.class_id = class_obj
                    instance.save()
                except Class.DoesNotExist:
                    raise serializers.ValidationError({'class_id': f'Class with id {update_class_id} does not exist.'})
            else:
                instance.class_id = None
                instance.save()
        
        return instance


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
    user_email = serializers.EmailField(source='user.email', read_only=True)  # Changed student_email to user_email and student to user
    class Meta:
        model = TransportDetails
        fields = '__all__'


# ------------------- ID CARD -------------------
class IDCardSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()
    
    class Meta:
        model = IDCard
        fields = '__all__'
        
    def get_user_name(self, obj):
        # Try to get the name from the related user profile
        if hasattr(obj.user, 'admin') and obj.user.admin:
            return obj.user.admin.fullname
        elif hasattr(obj.user, 'teacher') and obj.user.teacher:
            return obj.user.teacher.fullname
        elif hasattr(obj.user, 'principal') and obj.user.principal:
            return obj.user.principal.fullname
        elif hasattr(obj.user, 'management') and obj.user.management:
            return obj.user.management.fullname
        elif hasattr(obj.user, 'student') and obj.user.student:
            return obj.user.student.fullname
        elif hasattr(obj.user, 'parent') and obj.user.parent:
            return obj.user.parent.fullname
        else:
            # Fallback to email if no name found
            return obj.user.email
