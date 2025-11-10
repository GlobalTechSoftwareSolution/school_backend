from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model
from django.conf import settings
from minio import Minio
from django.utils import timezone
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
import os, tempfile, requests, pytz
from geopy.distance import geodesic
from datetime import datetime, date, timedelta
try:
    import face_recognition
except Exception:  # pragma: no cover
    face_recognition = None

from .models import (
    User, Student, Teacher, Principal, Management, Admin, Parent,
    Department, Subject, Attendance, Grade, FeeStructure,
    FeePayment, Timetable, FormerMember, Document, Notice, Issue, Holiday, Award, Assignment, Leave, Task,
    Project, Program, Activity, Report, FinanceTransaction, TransportDetails, Class,
)
from .serializers import (
    UserSerializer, UserRegistrationSerializer,
    StudentSerializer, StudentCreateSerializer,
    TeacherSerializer, TeacherCreateSerializer,
    PrincipalSerializer, ManagementSerializer, AdminSerializer, ParentSerializer,
    DepartmentSerializer, SubjectSerializer, ClassSerializer,
    AttendanceSerializer, AttendanceCreateSerializer, AttendanceUpdateSerializer,
    GradeSerializer, GradeCreateSerializer,
    FeeStructureSerializer, FeePaymentSerializer, FeePaymentCreateSerializer,
    TimetableSerializer, TimetableCreateSerializer, FormerMemberSerializer,
    DocumentSerializer, NoticeSerializer, IssueSerializer, HolidaySerializer, AwardSerializer,
    AssignmentSerializer, LeaveSerializer, TaskSerializer,
    ProjectSerializer, ProgramSerializer, ActivitySerializer, ReportSerializer,
    FinanceTransactionSerializer, TransportDetailsSerializer,
)


def _minio_client_global():
    if Minio is None:
        return None
    cfg = settings.MINIO_STORAGE
    return Minio(
        cfg['ENDPOINT'],
        access_key=cfg['ACCESS_KEY'],
        secret_key=cfg['SECRET_KEY'],
        secure=cfg.get('USE_SSL', True),
    )

def _object_name_for_member_global(member, fallback_email: str | None = None, fallback_id: str | None = None) -> str:
    identifier = None
    for attr in ('student_id', 'teacher_id'):
        if hasattr(member, attr) and getattr(member, attr):
            identifier = getattr(member, attr)
            break
    if not identifier:
        if hasattr(member, 'email'):
            email_val = getattr(member.email, 'email', None) if hasattr(member.email, 'email') else member.email
            if email_val:
                identifier = str(email_val).split('@')[0]
    if not identifier:
        identifier = (fallback_id or (fallback_email.split('@')[0] if fallback_email else 'unknown'))
    return f"images/{identifier}/profile.jpg"

def _upload_file_to_minio_global(member, file, fallback_email: str | None = None, fallback_id: str | None = None):
    client = _minio_client_global()
    if client is None:
        return None
    bucket = settings.MINIO_STORAGE['BUCKET_NAME']
    object_name = _object_name_for_member_global(member, fallback_email, fallback_id)
    client.put_object(bucket, object_name, file.file, file.size, content_type=getattr(file, 'content_type', 'application/octet-stream'))
    base = settings.BASE_BUCKET_URL
    if not base.endswith('/'):
        base += '/'
    return f"{base}{object_name}"

 


# ------------------- USER REGISTRATION -------------------
@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """
    Register a new user (Student, Teacher, Principal, etc.)
    """
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response({
            'message': 'User registered successfully. Awaiting approval.',
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def current_user(request):
    """
    Get current authenticated user details
    """
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_with_credentials(request):
    """
    Login with credentials even if you have a token.
    Validates email, password, and role, then returns that user's details.
    """
    from django.contrib.auth import authenticate
    
    email = request.data.get('email')
    password = request.data.get('password')
    role = request.data.get('role')
    
    if not email or not password or not role:
        return Response(
            {'error': 'Email, password, and role are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Authenticate the provided credentials
    user = authenticate(request, username=email, password=password)
    
    if not user:
        return Response(
            {'error': 'Invalid email or password'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Check if user is approved
    if not user.is_approved:  # type: ignore[attr-defined]
        return Response(
            {'error': 'Your account is pending approval'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Check if user is active
    if not user.is_active:
        return Response(
            {'error': 'Your account has been deactivated'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Check if role matches
    if user.role != role:  # type: ignore[attr-defined]
        return Response(
            {'error': f"Invalid role. You are registered as '{user.role}', but provided '{role}'"},  # type: ignore[attr-defined]
            status=status.HTTP_403_FORBIDDEN
        )
    
    # All checks passed - return the user's details
    serializer = UserSerializer(user)
    return Response({
        'message': f'Login successful as {role}',
        'user': serializer.data
    }, status=status.HTTP_200_OK)


# ------------------- USER VIEWSET -------------------
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]  # type: ignore[assignment]
    filterset_fields = ['role', 'is_active', 'is_approved']
    search_fields = ['email', 'role']
    ordering_fields = ['created_at', 'email']

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a user"""
        user = self.get_object()
        user.is_approved = True
        user.save()
        return Response({'message': 'User approved successfully'})

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a user"""
        user = self.get_object()
        user.is_active = False
        user.save()
        return Response({'message': 'User deactivated successfully'})


# ------------------- DEPARTMENT VIEWSET -------------------
class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['department_name', 'description']
    ordering_fields = ['department_name', 'created_at']


# ------------------- SUBJECT VIEWSET -------------------
class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['subject_name', 'subject_code']
    ordering_fields = ['subject_name', 'created_at']


# ------------------- CLASS VIEWSET -------------------
class ClassViewSet(viewsets.ModelViewSet):
    queryset = Class.objects.all()
    serializer_class = ClassSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['class_name', 'sec']
    ordering_fields = ['class_name', 'created_at']


# ------------------- STUDENT VIEWSET -------------------
class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    permission_classes = [AllowAny]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]  # type: ignore[assignment]
    filterset_fields = ['class_fk', 'gender', 'blood_group', 'father_name', 'mother_name']
    search_fields = ['fullname', 'student_id', 'email__email', 'father_name', 'mother_name']
    ordering_fields = ['fullname', 'admission_date']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return StudentCreateSerializer
        return StudentSerializer

    @action(detail=False, methods=['get'])
    def by_class(self, request):
        """Get students by class name (and optional section)."""
        class_id = request.query_params.get('class_id')
        if class_id:
            qs = self.get_queryset().filter(class_fk=class_id)
            serializer = self.get_serializer(qs, many=True)
            return Response(serializer.data)
        return Response({'error': 'class_id parameter required'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'error': 'class_name parameter required'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['patch'])
    def upload_profile(self, request, pk=None):
        student = self.get_object()
        file = request.FILES.get('profile_picture')
        if not file:
            return Response({'error': 'profile_picture parameter required'}, status=status.HTTP_400_BAD_REQUEST)
        url = self._upload_file_to_minio(student, file)
        if url is None:
            return Response({'error': 'minio Python package is not installed. Please install dependencies from requirements.txt.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        student.profile_picture = url
        student.save()
        serializer = self.get_serializer(student)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def _minio_client(self):
        if Minio is None:
            return None
        cfg = settings.MINIO_STORAGE
        return Minio(
            cfg['ENDPOINT'],
            access_key=cfg['ACCESS_KEY'],
            secret_key=cfg['SECRET_KEY'],
            secure=cfg.get('USE_SSL', True),
        )

    def _object_name_for_student(self, student, fallback_email: str | None = None, fallback_student_id: str | None = None) -> str:
        identifier = None
        if hasattr(student, 'student_id') and student.student_id:
            identifier = student.student_id
        elif hasattr(student, 'email') and hasattr(student.email, 'email'):
            identifier = student.email.email.split('@')[0]
        else:
            identifier = (fallback_student_id or (fallback_email.split('@')[0] if fallback_email else 'unknown'))
        return f"images/{identifier}/profile.jpg"

    def _upload_file_to_minio(self, student, file, fallback_email: str | None = None, fallback_student_id: str | None = None):
        client = self._minio_client()
        if client is None:
            return None
        bucket = settings.MINIO_STORAGE['BUCKET_NAME']
        object_name = self._object_name_for_student(student, fallback_email, fallback_student_id)
        client.put_object(bucket, object_name, file.file, file.size, content_type=getattr(file, 'content_type', 'application/octet-stream'))
        base = settings.BASE_BUCKET_URL
        if not base.endswith('/'):
            base += '/'
        return f"{base}{object_name}"

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        data = request.data.copy()
        file = request.FILES.get('profile_picture') or request.FILES.get('file')
        if file:
            url = self._upload_file_to_minio(instance, file)
            if url is None:
                return Response({'error': 'minio Python package is not installed. Please install dependencies from requirements.txt.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            data['profile_picture'] = url
        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        file = request.FILES.get('profile_picture') or request.FILES.get('file')
        # For create, we may not have a Student instance yet; use fallbacks from request data
        fallback_email = data.get('email')
        fallback_student_id = data.get('student_id')
        if file:
            # No Student instance yet; rely on fallback values for object path
            url = self._upload_file_to_minio(None, file, fallback_email=fallback_email, fallback_student_id=fallback_student_id)
            if url is None:
                return Response({'error': 'minio Python package is not installed. Please install dependencies from requirements.txt.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            data['profile_picture'] = url
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


# ------------------- TEACHER VIEWSET -------------------
class TeacherViewSet(viewsets.ModelViewSet):
    queryset = Teacher.objects.all()
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]  # type: ignore[assignment]
    filterset_fields = ['department', 'gender', 'blood_group']
    search_fields = ['fullname', 'teacher_id', 'email__email', 'qualification']
    ordering_fields = ['fullname', 'date_joined']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return TeacherCreateSerializer
        return TeacherSerializer

    @action(detail=False, methods=['get'])
    def by_department(self, request):
        """Get teachers by department"""
        dept_id = request.query_params.get('department_id')
        if dept_id:
            teachers = self.get_queryset().filter(department_id=dept_id)  # type: ignore[union-attr]
            serializer = self.get_serializer(teachers, many=True)
            return Response(serializer.data)
        return Response({'error': 'department_id parameter required'}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        data = request.data.copy()
        file = request.FILES.get('profile_picture') or request.FILES.get('file')
        if file:
            url = _upload_file_to_minio_global(instance, file)
            if url is None:
                return Response({'error': 'minio Python package is not installed. Please install dependencies from requirements.txt.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            data['profile_picture'] = url
        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)


# ------------------- PRINCIPAL VIEWSET -------------------
class PrincipalViewSet(viewsets.ModelViewSet):
    queryset = Principal.objects.all()
    serializer_class = PrincipalSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ['fullname', 'email__email']

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        data = request.data.copy()
        file = request.FILES.get('profile_picture') or request.FILES.get('file')
        if file:
            url = _upload_file_to_minio_global(instance, file)
            if url is None:
                return Response({'error': 'minio Python package is not installed. Please install dependencies from requirements.txt.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            data['profile_picture'] = url
        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)


# ------------------- MANAGEMENT VIEWSET -------------------
class ManagementViewSet(viewsets.ModelViewSet):
    queryset = Management.objects.all()
    serializer_class = ManagementSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]  # type: ignore[assignment]
    filterset_fields = ['department', 'designation']
    search_fields = ['fullname', 'designation', 'email__email']

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        data = request.data.copy()
        file = request.FILES.get('profile_picture') or request.FILES.get('file')
        if file:
            url = _upload_file_to_minio_global(instance, file)
            if url is None:
                return Response({'error': 'minio Python package is not installed. Please install dependencies from requirements.txt.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            data['profile_picture'] = url
        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)


# ------------------- ADMIN VIEWSET -------------------
class AdminViewSet(viewsets.ModelViewSet):
    queryset = Admin.objects.all()
    serializer_class = AdminSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ['fullname', 'email__email']

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        data = request.data.copy()
        file = request.FILES.get('profile_picture') or request.FILES.get('file')
        if file:
            url = _upload_file_to_minio_global(instance, file)
            if url is None:
                return Response({'error': 'minio Python package is not installed. Please install dependencies from requirements.txt.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            data['profile_picture'] = url
        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

# ------------------- PARENT VIEWSET -------------------
class ParentViewSet(viewsets.ModelViewSet):
    queryset = Parent.objects.all()
    serializer_class = ParentSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ['fullname', 'email__email', 'occupation']

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        data = request.data.copy()
        file = request.FILES.get('profile_picture') or request.FILES.get('file')
        if file:
            url = _upload_file_to_minio_global(instance, file)
            if url is None:
                return Response({'error': 'minio Python package is not installed. Please install dependencies from requirements.txt.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            data['profile_picture'] = url
        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)


# ------------------- ATTENDANCE VIEWSET -------------------
class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.all().select_related('student')
    serializer_class = AttendanceSerializer
    permission_classes = [AllowAny]  # No authentication required
    lookup_field = 'pk'
    
    def get_serializer_class(self):
        if self.action == 'create':
            return AttendanceCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return AttendanceUpdateSerializer
        return AttendanceSerializer

    def list(self, request):
        """
        GET /api/attendance/
        Returns all attendance records from the database
        """
        # Use the default ModelViewSet list behavior
        return super().list(request)

    @action(detail=False, methods=['post'])
    def mark(self, request):
        """
        POST /api/attendance/mark/
        Mark attendance for a student
        Required: student_email, class_name
        Optional: date, check_in, check_out, marked_by_role
        """
        student_email = request.data.get('student_email')
        class_name = request.data.get('class_name')
        marked_by_role = request.data.get('marked_by_role', 'Admin')  # Default to 'Admin' if not provided
        
        if not all([student_email, class_name]):
            return Response(
                {'error': 'student_email and class_name are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            student = Student.objects.get(email=student_email)
        except Student.DoesNotExist:
            return Response(
                {'error': 'Student not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get current time with seconds precision
        now = timezone.now()
        current_time = now.time()
        current_date = now.date()
        
        # Get seconds from the current time
        seconds = now.second
        
        # Get sec value from request data if provided, otherwise use current seconds
        sec_value = request.data.get('sec', seconds)
        
        # Get or create attendance record
        # First, get the Class object
        try:
            class_obj = Class.objects.get(class_name=class_name)
        except Class.DoesNotExist:
            return Response(
                {'error': f'Class {class_name} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        attendance, created = Attendance.objects.get_or_create(
            student=student,
            date=current_date,
            defaults={
                'class_fk': class_obj,
                'check_in': current_time,
                'sec': sec_value,
                'marked_by_role': marked_by_role
            }
        )

        # If updating existing record (e.g., for check-out)
        if not created:
            if 'check_out' in request.data and not attendance.check_out:
                attendance.check_out = request.data['check_out']
                # Update seconds if provided
                if 'sec' in request.data:
                    attendance.sec = request.data['sec']
                attendance.save()

        serializer = self.get_serializer(attendance)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )

    def partial_update(self, request, pk=None):
        """
        PATCH /api/attendance/{pk}/
        Update an attendance record
        """
        attendance = self.get_object()
        serializer = self.get_serializer(attendance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def get_students_for_marking(self, request):

        teacher_email = request.data.get('teacher_email')
        class_name = request.data.get('class_name')
        section = request.data.get('section')

        if not teacher_email or not class_name:
            return Response({'error': 'teacher_email and class_name are required'}, status=status.HTTP_400_BAD_REQUEST)

        # Verify the teacher exists
        try:
            teacher = Teacher.objects.get(email=teacher_email)
        except Teacher.DoesNotExist:
            return Response({'error': 'Teacher not found'}, status=status.HTTP_404_NOT_FOUND)

        # Get students in the class/section
        try:
            class_obj = Class.objects.get(class_name=class_name)
            students_qs = Student.objects.filter(class_fk=class_obj)
        except Class.DoesNotExist:
            return Response({'error': f'Class {class_name} not found'}, status=status.HTTP_404_NOT_FOUND)
        if section:
            students_qs = students_qs.filter(section=section)

        today = timezone.now().date()
        students_data = []

        # Get the Class object
        try:
            class_obj = Class.objects.get(class_name=class_name)
        except Class.DoesNotExist:
            return Response({'error': f'Class {class_name} not found'}, status=status.HTTP_404_NOT_FOUND)

        for student in students_qs:
            # Get or create attendance for today
            attendance, created = Attendance.objects.get_or_create(
                student=student,
                date=today,
                defaults={
                    'class_fk': class_obj,
                    'marked_by_role': 'Teacher'
                }
            )
            students_data.append({
                'student_id': student.student_id,
                'fullname': student.fullname,
                'email': student.email.email,
                'status': attendance.status
            })

        return Response({
            'teacher_email': teacher_email,
            'class_name': class_name,
            'section': section,
            'date': today,
            'students': students_data
        })

    @action(detail=False, methods=['post'])
    def bulk_update_status(self, request):
        """
        POST /api/attendance/bulk_update_status/
        Bulk update attendance status for students.
        Body: {
            "teacher_email": "teacher@example.com",
            "class_name": "10A",
            "section": "A",  // optional
            "date": "2023-10-01",  // optional, defaults to today
            "updates": [
                {"student_email": "student1@example.com", "status": "Present"},
                {"student_email": "student2@example.com", "status": "Absent"}
            ]
        }
        """

        teacher_email = request.data.get('teacher_email')
        class_name = request.data.get('class_name')
        section = request.data.get('section')
        date_str = request.data.get('date')
        updates = request.data.get('updates', [])

        if not teacher_email or not class_name:
            return Response({'error': 'teacher_email and class_name required'}, status=status.HTTP_400_BAD_REQUEST)
        if not updates:
            return Response({'error': 'updates list required'}, status=status.HTTP_400_BAD_REQUEST)

        # Verify the teacher exists
        try:
            teacher = Teacher.objects.get(email=teacher_email)
        except Teacher.DoesNotExist:
            return Response({'error': 'Teacher not found'}, status=status.HTTP_404_NOT_FOUND)

        # Parse date
        if date_str:
            try:
                target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response({'error': 'Invalid date format. Use YYYY-MM-DD'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            target_date = timezone.now().date()

        updated_count = 0
        errors = []

        for update in updates:
            student_email = update.get('student_email')
            new_status = update.get('status')
            if not student_email or new_status not in ['Present', 'Absent']:
                errors.append({'update': update, 'error': 'Invalid student_email or status'})
                continue

            try:
                student = Student.objects.get(email=student_email, class_name=class_name)
                if section and student.class_fk and student.class_fk.sec != section:
                    errors.append({'student_email': student_email, 'error': 'Student not in specified section'})
                    continue

                # Get the Class object
                try:
                    class_obj = Class.objects.get(class_name=class_name)
                except Class.DoesNotExist:
                    errors.append({'student_email': student_email, 'error': f'Class {class_name} not found'})
                    continue

                attendance, created = Attendance.objects.get_or_create(
                    student=student,
                    date=target_date,
                    defaults={
                        'class_fk': class_obj,
                        'marked_by_role': 'Teacher'
                    }
                )
                attendance.status = new_status
                attendance.marked_by_role = 'Teacher'
                attendance.save()
                updated_count += 1

                # Send email notification if marked as absent
                if new_status == 'Absent':
                    student_email = student.email.email
                    parent_email = student.parent.email.email if student.parent else None

                    # Email to student
                    send_mail(
                        subject='Attendance Notification: Marked Absent',
                        message=f'Dear {student.fullname},\n\nYou have been marked as absent for {class_name} on {target_date}.\n\nRegards,\nSchool Administration',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[student_email],
                        fail_silently=True,
                    )

                    # Email to parent if available
                    if parent_email:
                        send_mail(
                            subject='Attendance Notification: Your Child Marked Absent',
                            message=f'Dear Parent,\n\nYour child {student.fullname} has been marked as absent for {class_name} on {target_date}.\n\nRegards,\nSchool Administration',
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            recipient_list=[parent_email],
                            fail_silently=True,
                        )
            except Student.DoesNotExist:
                errors.append({'student_email': student_email, 'error': 'Student not found or not in class'})

        return Response({
            'teacher_email': teacher_email,
            'updated_count': updated_count,
            'date': target_date,
            'errors': errors
        })

# ------------------- GRADE VIEWSET -------------------
class GradeViewSet(viewsets.ModelViewSet):
    queryset = Grade.objects.all()
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]  # type: ignore[assignment]
    filterset_fields = ['student', 'subject', 'teacher', 'exam_type']
    search_fields = ['student__fullname', 'student__student_id', 'subject__subject_name']
    ordering_fields = ['exam_date', 'created_at']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return GradeCreateSerializer
        return GradeSerializer

    @action(detail=False, methods=['get'])
    def student_report(self, request):
        """Get grade report for a specific student"""
        student_email = request.query_params.get('student_email')
        if student_email:
            grades = self.get_queryset().filter(student__email=student_email)  # type: ignore[union-attr]
            serializer = self.get_serializer(grades, many=True)
            return Response(serializer.data)
        return Response({'error': 'student_email parameter required'}, status=status.HTTP_400_BAD_REQUEST)


# ------------------- FEE STRUCTURE VIEWSET -------------------
class FeeStructureViewSet(viewsets.ModelViewSet):
    queryset = FeeStructure.objects.all()
    serializer_class = FeeStructureSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]  # type: ignore[assignment]
    filterset_fields = ['class_name', 'fee_type', 'frequency']
    search_fields = ['fee_type', 'description']

    @action(detail=False, methods=['get'])
    def by_class(self, request):
        """Get fee structure by class name"""
        class_name = request.query_params.get('class_name')
        if class_name:
            fees = self.get_queryset().filter(class_name=class_name)
            serializer = self.get_serializer(fees, many=True)
            return Response(serializer.data)
        return Response({'error': 'class_name parameter required'}, status=status.HTTP_400_BAD_REQUEST)


# ------------------- FEE PAYMENT VIEWSET -------------------
class FeePaymentViewSet(viewsets.ModelViewSet):
    queryset = FeePayment.objects.all()
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]  # type: ignore[assignment]
    filterset_fields = ['student', 'fee_structure', 'payment_method', 'status']
    search_fields = ['student__fullname', 'student__student_id', 'transaction_id']
    ordering_fields = ['payment_date', 'created_at']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return FeePaymentCreateSerializer
        return FeePaymentSerializer

    @action(detail=False, methods=['get'])
    def student_payments(self, request):
        """Get payment history for a specific student"""
        student_email = request.query_params.get('student_email')
        if student_email:
            payments = self.get_queryset().filter(student__email=student_email)  # type: ignore[union-attr]
            serializer = self.get_serializer(payments, many=True)
            return Response(serializer.data)
        return Response({'error': 'student_email parameter required'}, status=status.HTTP_400_BAD_REQUEST)


# ------------------- TIMETABLE VIEWSET -------------------
class TimetableViewSet(viewsets.ModelViewSet):
    queryset = Timetable.objects.all()
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]  # type: ignore[assignment]
    filterset_fields = ['class_name', 'section', 'subject', 'teacher', 'day_of_week']
    search_fields = ['class_name', 'section', 'subject__subject_name', 'teacher__fullname']
    ordering_fields = ['day_of_week', 'start_time']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return TimetableCreateSerializer
        return TimetableSerializer

    @action(detail=False, methods=['get'])
    def by_class(self, request):
        """Get timetable by class name"""
        class_name = request.query_params.get('class_name')
        if class_name:
            timetable = self.get_queryset().filter(class_name=class_name)
            serializer = self.get_serializer(timetable, many=True)
            return Response(serializer.data)
        return Response({'error': 'class_name parameter required'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def by_teacher(self, request):
        """Get timetable by teacher"""
        teacher_email = request.query_params.get('teacher_email')
        if teacher_email:
            timetable = self.get_queryset().filter(teacher__email=teacher_email)  # type: ignore[union-attr]
            serializer = self.get_serializer(timetable, many=True)
            return Response(serializer.data)
        return Response({'error': 'teacher_email parameter required'}, status=status.HTTP_400_BAD_REQUEST)


# ------------------- FORMER MEMBER VIEWSET -------------------
class FormerMemberViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for Former Members (backup of deleted users).
    Allows viewing and searching but not creation or modification.
    """
    queryset = FormerMember.objects.all()
    serializer_class = FormerMemberSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]  # type: ignore[assignment]
    filterset_fields = ['role', 'gender', 'blood_group']
    search_fields = ['email', 'fullname', 'student_id', 'teacher_id', 'phone']
    ordering_fields = ['left_date', 'fullname', 'role']
    
    @action(detail=False, methods=['get'])
    def by_role(self, request):
        """Get former members by role"""
        role = request.query_params.get('role')
        if role:
            members = self.get_queryset().filter(role=role)  # type: ignore[union-attr]
            serializer = self.get_serializer(members, many=True)
            return Response(serializer.data)
        return Response({'error': 'role parameter required'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['patch'])
    def upload_profile(self, request, pk=None):
        member = self.get_object()
        file = request.FILES.get('profile_picture')
        if not file:
            return Response({'error': 'profile_picture parameter required'}, status=status.HTTP_400_BAD_REQUEST)
        url = _upload_file_to_minio_global(member, file)
        if url is None:
            return Response({'error': 'minio Python package is not installed. Please install dependencies from requirements.txt.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        member.profile_picture = url
        member.save()
        serializer = self.get_serializer(member)
        return Response(serializer.data, status=status.HTTP_200_OK)


# =================== FACE + LOCATION ATTENDANCE (STUDENTS) ===================
# Office location and radius
OFFICE_LAT = 13.068906816007116
OFFICE_LON = 77.55541294505542
LOCATION_RADIUS_METERS = 100
IST = pytz.timezone("Asia/Kolkata")


def _verify_location(latitude: float, longitude: float, radius_meters: int | None = None):
    if radius_meters is None:
        radius_meters = LOCATION_RADIUS_METERS
    user_location = (latitude, longitude)
    office_location = (OFFICE_LAT, OFFICE_LON)
    distance_meters = geodesic(user_location, office_location).meters
    return distance_meters <= radius_meters, distance_meters


@api_view(['POST'])
@permission_classes([AllowAny])
def school_attendance_view(request):
    """Mark student attendance by matching face image and verifying location."""
    # Only require face_recognition if an image is provided; allow deterministic marking via student_email otherwise
    if face_recognition is None and (request.FILES.get('image') or request.FILES.get('file')):
        return JsonResponse({
            'status': 'error',
            'message': 'face_recognition package not installed. Please install dependencies or provide student_email without an image.'
        }, status=500)

    lat = request.POST.get('latitude')
    lon = request.POST.get('longitude')
    if lat is None or lon is None:
        return JsonResponse({'status': 'fail', 'message': 'Latitude and longitude required'}, status=400)
    try:
        lat_f = float(lat)
        lon_f = float(lon)
    except ValueError:
        return JsonResponse({'status': 'fail', 'message': 'Invalid latitude or longitude'}, status=400)

    uploaded_file = request.FILES.get('image') or request.FILES.get('file')
    forced_email = request.POST.get('student_email')
    if not uploaded_file and not forced_email:
        return JsonResponse({'status': 'fail', 'message': 'Provide either student_email or an image'}, status=400)

    tmp_path = None
    if uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            for chunk in uploaded_file.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name

    try:
        uploaded_encoding = None
        if tmp_path:
            fr = face_recognition
            assert fr is not None  # ensured above when image is provided
            uploaded_img = fr.load_image_file(tmp_path)
            uploaded_encodings = fr.face_encodings(uploaded_img)
            if not uploaded_encodings:
                return JsonResponse({'status': 'fail', 'message': 'No face detected'}, status=400)
            uploaded_encoding = uploaded_encodings[0]

        # Determine target student
        matched_student = None
        from .models import Student, Attendance  # local import to avoid cycles
        if forced_email:
            try:
                matched_student = Student.objects.get(email=forced_email)
            except Student.DoesNotExist:
                return JsonResponse({'status': 'fail', 'message': f'Student not found: {forced_email}'}, status=404)
        elif uploaded_encoding is not None:
            # Auto-set check_in for face recognition flow
            check_in = timezone.localtime().time()
            
            # Iterate over students with profile images and pick the best match by distance
            best_student = None
            best_distance = None
            candidates = Student.objects.exclude(profile_picture__isnull=True).exclude(profile_picture__exact='')
            for student in candidates:
                try:
                    resp = requests.get(student.profile_picture, timeout=10)
                    if resp.status_code != 200:
                        continue
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as s_tmp:
                        s_tmp.write(resp.content)
                        s_path = s_tmp.name
                    fr = face_recognition
                    assert fr is not None
                    s_img = fr.load_image_file(s_path)
                    s_encs = fr.face_encodings(s_img)
                    os.remove(s_path)
                    if not s_encs:
                        continue
                    # Compute distance and keep the closest under threshold
                    distances = fr.face_distance([s_encs[0]], uploaded_encoding)
                    distance_val = float(distances[0])
                    # Stricter threshold to avoid random mismatches
                    if distance_val <= 0.45 and (best_distance is None or distance_val < best_distance):
                        best_distance = distance_val
                        best_student = student
                except Exception:
                    continue
            matched_student = best_student

        if matched_student is None:
            return JsonResponse({'status': 'fail', 'message': 'No matching student found'}, status=404)

        # Verify location proximity
        is_within, distance_m = _verify_location(lat_f, lon_f)
        if not is_within:
            return JsonResponse({
                'status': 'fail',
                'message': f'Too far from office ({distance_m:.2f}m). Must be within {LOCATION_RADIUS_METERS}m.'
            }, status=400)

        # Mark attendance for today (works regardless of USE_TZ setting)
        today = timezone.now().date()
        # Determine actor role (who is marking)
        actor_role = getattr(getattr(request, 'user', None), 'role', None) or 'Admin'
        # Allow overriding status and remarks
        status_param = request.POST.get('status')
        if status_param not in (None, 'Present', 'Absent'):
            status_param = None
        remarks_param = request.POST.get('remarks')

        # Create or update attendance record with auto check_in
        # Get the Class object
        class_obj = matched_student.class_fk
        attendance_data = {
            'class_fk': class_obj,
            'check_in': check_in if 'check_in' in locals() else None,
            'status': 'Present'  # Auto-mark as present for face recognition
        }
        attendance, created = Attendance.objects.update_or_create(
            student=matched_student,
            date=today,
            defaults=attendance_data
        )
        if not created:
            attendance.status = status_param or 'Present'
            # Update class_fk if already exists
            if matched_student.class_fk:
                attendance.class_fk = matched_student.class_fk
            attendance.save()

        return JsonResponse({
            'status': 'success',
            'message': f'Attendance marked for {matched_student.fullname}',
            'student': matched_student.fullname,
            'student_id': matched_student.student_id,
            'date': str(today),
            'marked_by_role': actor_role,
        })
    finally:
        try:
            if tmp_path:
                os.remove(tmp_path)
        except Exception:
            pass


# ------------------- DOCUMENT VIEWSET -------------------
class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [AllowAny]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    lookup_field = 'email__email'
    lookup_url_kwarg = 'email'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]  # type: ignore[assignment]
    filterset_fields = ['email']
    search_fields = ['email__email']
    ordering_fields = ['uploaded_at']

    @action(detail=False, methods=['post'])
    def bulk_upsert(self, request):
        """Upsert documents by user email (OneToOne). Expects an array of objects with email and any doc fields."""
        if not isinstance(request.data, list):
            return Response({'error': 'Expected a JSON array'}, status=status.HTTP_400_BAD_REQUEST)
        created = 0
        updated = 0
        errors: list[dict] = []
        for idx, item in enumerate(request.data):
            try:
                email = item.get('email')
                if not email:
                    raise ValueError('email is required')
                try:
                    user = User.objects.get(email=email)
                except User.DoesNotExist:
                    raise ValueError(f"User not found: {email}")
                # remove email key for defaults
                defaults = {k: v for k, v in item.items() if k != 'email'}
                obj, was_created = Document.objects.update_or_create(
                    email=user,
                    defaults=defaults
                )
                if was_created:
                    created += 1
                else:
                    updated += 1
            except Exception as e:
                errors.append({'index': idx, 'error': str(e), 'item': item})
        return Response({'created': created, 'updated': updated, 'errors': errors})

    def _upload_doc_to_minio(self, member, file, field_name: str):
        client = _minio_client_global()
        if client is None:
            return None
        bucket = settings.MINIO_STORAGE['BUCKET_NAME']
        base = settings.BASE_BUCKET_URL
        if not base.endswith('/'):
            base += '/'
        identifier_path = _object_name_for_member_global(member, getattr(member, 'email', None))
        if identifier_path.startswith('images/'):
            identifier = identifier_path.split('/', 1)[1].split('/')[0]
        else:
            identifier = 'unknown'
        import os as _os
        _, ext = _os.path.splitext(getattr(file, 'name', '') or '')
        if not ext:
            ext = '.bin'
        object_name = f"documents/{identifier}/{field_name}{ext}"
        client.put_object(bucket, object_name, file.file, file.size, content_type=getattr(file, 'content_type', 'application/octet-stream'))
        return f"{base}{object_name}"

    def _member_identifier(self, member) -> str:
        """Extract a stable identifier for the member used in object paths."""
        identifier_path = _object_name_for_member_global(member, getattr(member, 'email', None))
        if identifier_path.startswith('images/'):
            return identifier_path.split('/', 1)[1].split('/')[0]
        return 'unknown'

    def _delete_minio_object_by_url(self, url: str):
        """Delete a MinIO object if the URL points to our BASE_BUCKET_URL."""
        if not url:
            return
        base = settings.BASE_BUCKET_URL
        if not base.endswith('/'):
            base += '/'
        if not url.startswith(base):
            return  # Not our bucket/path
        object_name = url[len(base):]
        client = _minio_client_global()
        if client is None:
            return
        bucket = settings.MINIO_STORAGE['BUCKET_NAME']
        try:
            client.remove_object(bucket, object_name)
        except Exception:
            # Best effort delete; ignore errors
            pass

    @action(detail=False, methods=['post'])
    def upload(self, request):
        email = request.POST.get('email')
        if not email:
            return Response({'error': 'email is required in form-data'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': f'User not found: {email}'}, status=status.HTTP_404_NOT_FOUND)

        allowed_fields = {
            'tenth','twelth','degree','masters','marks_card','certificates','award','resume','id_proof',
            'transfer_certificate','study_certificate','conduct_certificate','student_id_card','admit_card',
            'fee_receipt','achievement_crt','bonafide_crt'
        }

        # Load existing document to support replace-delete
        existing = None
        try:
            existing = Document.objects.get(email=user)
        except Document.DoesNotExist:
            existing = None

        updates = {}
        for field_name, file in request.FILES.items():
            if field_name not in allowed_fields:
                continue
            # Delete previous object if present
            if existing is not None:
                prev_url = getattr(existing, field_name, None)
                if prev_url:
                    self._delete_minio_object_by_url(prev_url)
            url = self._upload_doc_to_minio(user, file, field_name)
            if url is None:
                return Response({'error': 'minio Python package is not installed. Please install dependencies from requirements.txt.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            updates[field_name] = url

        if not updates:
            return Response({'error': 'No valid document files provided'}, status=status.HTTP_400_BAD_REQUEST)

        obj, _ = Document.objects.update_or_create(
            email=user,
            defaults=updates
        )
        return Response(DocumentSerializer(obj).data, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        # Upsert behavior: create Document if missing for this email
        lookup_key = self.lookup_url_kwarg or 'email'
        email_key = self.kwargs.get(lookup_key)
        if not email_key:
            return Response({'error': 'email not provided in URL'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(email=email_key)
        except User.DoesNotExist:
            return Response({'error': f'User not found: {email_key}'}, status=status.HTTP_404_NOT_FOUND)
        instance, _ = Document.objects.get_or_create(email=user)
        data = request.data.copy()

        allowed_fields = {
            'tenth','twelth','degree','masters','marks_card','certificates','award','resume','id_proof',
            'transfer_certificate','study_certificate','conduct_certificate','student_id_card','admit_card',
            'fee_receipt','achievement_crt','bonafide_crt'
        }

        # Handle single or multiple file uploads via PATCH
        file_updates = {}
        for field_name, file in request.FILES.items():
            if field_name not in allowed_fields:
                continue
            # Delete previous object if present
            prev_url = getattr(instance, field_name, None)
            if prev_url:
                self._delete_minio_object_by_url(prev_url)
            url = self._upload_doc_to_minio(instance.email, file, field_name)
            if url is None:
                return Response({'error': 'minio Python package is not installed. Please install dependencies from requirements.txt.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            file_updates[field_name] = url

        # Merge uploaded URLs into data
        for k, v in file_updates.items():
            data[k] = v

        # Handle clearing fields via PATCH (set to empty string or explicit null)
        for fname in allowed_fields:
            if fname in data and (data.get(fname) in ['', None, 'null', 'None']):
                prev_url = getattr(instance, fname, None)
                if prev_url:
                    self._delete_minio_object_by_url(prev_url)
                data[fname] = None

        serializer = self.get_serializer(instance, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        allowed_fields = {
            'tenth','twelth','degree','masters','marks_card','certificates','award','resume','id_proof',
            'transfer_certificate','study_certificate','conduct_certificate','student_id_card','admit_card',
            'fee_receipt','achievement_crt','bonafide_crt'
        }
        # Best-effort delete of all stored objects
        for fname in allowed_fields:
            url = getattr(instance, fname, None)
            if url:
                self._delete_minio_object_by_url(url)
        # Also delete any remaining objects under documents/{identifier}/ prefix
        try:
            client = _minio_client_global()
            if client is not None:
                bucket = settings.MINIO_STORAGE['BUCKET_NAME']
                identifier = self._member_identifier(instance.email)
                prefix = f"documents/{identifier}/"
                for obj in client.list_objects(bucket, prefix=prefix, recursive=True):
                    try:
                        object_name = getattr(obj, 'object_name', None)
                        if object_name:
                            client.remove_object(bucket, object_name)
                    except Exception:
                        pass
        except Exception:
            pass
        return super().destroy(request, *args, **kwargs)


# ------------------- ASSIGNMENT VIEWSET -------------------
class AssignmentViewSet(viewsets.ModelViewSet):
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]  # type: ignore[assignment]
    filterset_fields = ['subject', 'class_fk', 'assigned_by', 'due_date', 'status']
    search_fields = ['title', 'description', 'subject__subject_name', 'assigned_by__email']
    ordering_fields = ['created_at', 'due_date']

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        assignment = Assignment.objects.get(pk=response.data['id'])
        # Send emails to students and parents
        try:
            students = Student.objects.filter(class_fk=assignment.class_fk)
        except Class.DoesNotExist:
            students = Student.objects.none()
        for student in students:
            # Email to student
            send_mail(
                subject=f'New Assignment: {assignment.title}',
                message=f'Dear {student.fullname},\n\nA new assignment has been assigned to you.\n\nTitle: {assignment.title}\nSubject: {assignment.subject.subject_name}\nDescription: {assignment.description or ""}\nDue Date: {assignment.due_date or "N/A"}\n\nRegards,\nSchool Administration',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[student.email.email],
                fail_silently=True,
            )
            # Email to parent if available
            if student.parent:
                send_mail(
                    subject=f'New Assignment for Your Child: {assignment.title}',
                    message=f'Dear Parent,\n\nA new assignment has been assigned to your child {student.fullname}.\n\nTitle: {assignment.title}\nSubject: {assignment.subject.subject_name}\nDescription: {assignment.description or ""}\nDue Date: {assignment.due_date or "N/A"}\n\nRegards,\nSchool Administration',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[student.parent.email.email],
                    fail_silently=True,
                )
        return response


# ------------------- LEAVE VIEWSET -------------------
class LeaveViewSet(viewsets.ModelViewSet):
    queryset = Leave.objects.all()
    serializer_class = LeaveSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]  # type: ignore[assignment]
    filterset_fields = ['applicant', 'status', 'leave_type', 'start_date', 'end_date']
    search_fields = ['applicant__email', 'reason']
    ordering_fields = ['created_at', 'start_date', 'end_date', 'status']

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        leave = self.get_object()
        leave.status = 'Approved'
        approver = getattr(request, 'user', None)
        if getattr(approver, 'email', None):
            leave.approved_by_id = approver.email  # type: ignore[attr-defined]
        leave.save()
        return Response({'message': 'Leave approved', 'status': leave.status})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        leave = self.get_object()
        leave.status = 'Rejected'
        approver = getattr(request, 'user', None)
        if getattr(approver, 'email', None):
            leave.approved_by_id = approver.email  # type: ignore[attr-defined]
        leave.save()
        return Response({'message': 'Leave rejected', 'status': leave.status})


# ------------------- TASK VIEWSET -------------------
class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]  # type: ignore[assignment]
    filterset_fields = ['assigned_to', 'status', 'priority', 'due_date']
    search_fields = ['title', 'description', 'assigned_to__email', 'created_by__email']
    ordering_fields = ['created_at', 'due_date', 'priority', 'status']

    @action(detail=True, methods=['post'])
    def mark_done(self, request, pk=None):
        task = self.get_object()
        task.status = 'Done'
        task.completed_at = timezone.now()
        task.save()
        return Response({'message': 'Task marked as done'})


# ------------------- PROJECT VIEWSET -------------------
class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]  # type: ignore[assignment]
    filterset_fields = ['status', 'owner', 'class_fk', 'start_date', 'end_date']
    search_fields = ['title', 'description', 'owner__email']
    ordering_fields = ['created_at', 'start_date', 'end_date', 'status']


# ------------------- PROGRAM VIEWSET -------------------
class ProgramViewSet(viewsets.ModelViewSet):
    queryset = Program.objects.all()
    serializer_class = ProgramSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]  # type: ignore[assignment]
    filterset_fields = ['status', 'coordinator', 'start_date', 'end_date']
    search_fields = ['name', 'description', 'coordinator__email']
    ordering_fields = ['created_at', 'start_date', 'end_date', 'status']


# ------------------- ACTIVITY VIEWSET -------------------
class ActivityViewSet(viewsets.ModelViewSet):
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]  # type: ignore[assignment]
    filterset_fields = ['type', 'conducted_by', 'class_name', 'section', 'date']
    search_fields = ['name', 'description', 'conducted_by__email', 'class_name', 'section']
    ordering_fields = ['date', 'created_at']


# ------------------- REPORT VIEWSET -------------------
class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]  # type: ignore[assignment]
    filterset_fields = ['report_type', 'student', 'teacher', 'created_by', 'created_at']
    search_fields = ['title', 'description', 'student__fullname', 'teacher__fullname', 'created_by__email']
    ordering_fields = ['created_at', 'updated_at']


# ------------------- FINANCE TRANSACTION VIEWSET -------------------
class FinanceTransactionViewSet(viewsets.ModelViewSet):
    queryset = FinanceTransaction.objects.all()
    serializer_class = FinanceTransactionSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]  # type: ignore[assignment]
    filterset_fields = ['type', 'category', 'date', 'recorded_by']
    search_fields = ['description', 'reference_id', 'recorded_by__email', 'category']
    ordering_fields = ['date', 'created_at', 'amount']


# ------------------- TRANSPORT DETAILS VIEWSET -------------------

class TransportDetailsViewSet(viewsets.ModelViewSet):
    queryset = TransportDetails.objects.all()
    serializer_class = TransportDetailsSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]  # type: ignore[assignment]
    filterset_fields = ['user', 'route_name', 'bus_number', 'is_active'] # Changed student to user
    search_fields = ['user__fullname', 'route_name', 'bus_number', 'driver_name', 'driver_phone'] # Changed student__fullname to user__fullname
    ordering_fields = ['created_at', 'route_name']


# ------------------- NOTICE VIEWSET -------------------
class NoticeViewSet(viewsets.ModelViewSet):
    queryset = Notice.objects.all()
    serializer_class = NoticeSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]  # type: ignore[assignment]
    filterset_fields = ['email', 'important']
    search_fields = ['title', 'message', 'email__email']
    ordering_fields = ['posted_date', 'important']

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        notice = Notice.objects.get(pk=response.data['id'])
        if notice.email:
            send_mail(
                subject=f'Notice: {notice.title}',
                message=notice.message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[notice.email.email],
                fail_silently=True,
            )
        return response

    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Create multiple notices. Expects JSON array. Does not upsert."""
        if not isinstance(request.data, list):
            return Response({'error': 'Expected a JSON array'}, status=status.HTTP_400_BAD_REQUEST)
        ser = self.get_serializer(data=request.data, many=True, context={'bulk_create': True})
        ser.is_valid(raise_exception=True)
        notices = ser.save()
        # Send emails after bulk creation
        for notice in notices:
            if notice.email:
                send_mail(
                    subject=f'Notice: {notice.title}',
                    message=notice.message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[notice.email.email],
                    fail_silently=True,
                )
        return Response({'created': len(ser.data)}, status=status.HTTP_201_CREATED)


# ------------------- ISSUE VIEWSET -------------------
class IssueViewSet(viewsets.ModelViewSet):
    queryset = Issue.objects.all()
    serializer_class = IssueSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]  # type: ignore[assignment]
    filterset_fields = ['status', 'priority', 'raised_by', 'raised_to']
    search_fields = ['subject', 'description', 'raised_by__email', 'raised_to__email']
    ordering_fields = ['created_at', 'updated_at', 'priority', 'status']

    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Create multiple issues. Expects JSON array."""
        if not isinstance(request.data, list):
            return Response({'error': 'Expected a JSON array'}, status=status.HTTP_400_BAD_REQUEST)
        ser = self.get_serializer(data=request.data, many=True)
        ser.is_valid(raise_exception=True)
        self.perform_create(ser)
        return Response({'created': len(ser.data)}, status=status.HTTP_201_CREATED)


# ------------------- HOLIDAY VIEWSET -------------------
class HolidayViewSet(viewsets.ModelViewSet):
    queryset = Holiday.objects.all()
    serializer_class = HolidaySerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]  # type: ignore[assignment]
    filterset_fields = ['country', 'year', 'month', 'type']
    search_fields = ['name', 'type', 'country']
    ordering_fields = ['date', 'name']

    @action(detail=False, methods=['post'])
    def bulk_upsert(self, request):
        """Accepts a JSON array of holiday objects and upserts them."""
        if not isinstance(request.data, list):
            return Response({'error': 'Expected a JSON array'}, status=status.HTTP_400_BAD_REQUEST)

        created = 0
        updated = 0
        errors: list[dict] = []

        for idx, item in enumerate(request.data):
            try:
                # Validate via serializer (partial to allow minimal fields)
                ser = self.get_serializer(data=item)
                ser.is_valid(raise_exception=True)
                data = ser.validated_data

                # Required: date
                date_val = data.get('date')
                if date_val is None:
                    raise ValueError('date is required')

                defaults = {
                    'name': data.get('name') or '',
                    'country': data.get('country') or 'India',
                    'type': data.get('type') or '',
                    'year': data.get('year') or date_val.year,
                    'month': data.get('month') or date_val.month,
                    'weekday': data.get('weekday') or date_val.strftime('%A'),
                }
                obj, was_created = Holiday.objects.update_or_create(
                    date=date_val,
                    country=defaults['country'],
                    defaults=defaults
                )
                if was_created:
                    created += 1
                else:
                    updated += 1
            except Exception as e:
                errors.append({'index': idx, 'error': str(e), 'item': item})

        return Response({'created': created, 'updated': updated, 'errors': errors}, status=status.HTTP_200_OK)


# ------------------- AWARD VIEWSET -------------------
class AwardViewSet(viewsets.ModelViewSet):
    queryset = Award.objects.all()
    serializer_class = AwardSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]  # type: ignore[assignment]
    filterset_fields = ['email']
    search_fields = ['title', 'description', 'email__email']
    ordering_fields = ['created_at', 'title']

    @action(detail=False, methods=['post'])
    def bulk_upsert(self, request):
        """Upsert awards by (email, title). Expects JSON array."""
        if not isinstance(request.data, list):
            return Response({'error': 'Expected a JSON array'}, status=status.HTTP_400_BAD_REQUEST)
        created = 0
        updated = 0
        errors: list[dict] = []
        for idx, item in enumerate(request.data):
            try:
                email = item.get('email')
                title = item.get('title')
                if not email or not title:
                    raise ValueError('email and title are required')
                try:
                    user = User.objects.get(email=email)
                except User.DoesNotExist:
                    raise ValueError(f"User not found: {email}")
                defaults = {k: v for k, v in item.items() if k not in ('email', 'title')}
                obj, was_created = Award.objects.update_or_create(
                    email=user,
                    title=title,
                    defaults=defaults
                )
                if was_created:
                    created += 1
                else:
                    updated += 1
            except Exception as e:
                errors.append({'index': idx, 'error': str(e), 'item': item})
        return Response({'created': created, 'updated': updated, 'errors': errors})
