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
import os
import tempfile
import requests
import pytz
from geopy.distance import geodesic
try:
    import face_recognition
except Exception:  # pragma: no cover
    face_recognition = None

from .models import (
    User, Student, Teacher, Principal, Management, Admin, Parent,
    Department, Subject, Attendance, Grade, FeeStructure,
    FeePayment, Timetable, FormerMember, Document, Notice, Issue, Holiday, Award,
    Assignment, Leave, Task,
)
from .serializers import (
    UserSerializer, UserRegistrationSerializer,
    StudentSerializer, StudentCreateSerializer,
    TeacherSerializer, TeacherCreateSerializer,
    PrincipalSerializer, ManagementSerializer, AdminSerializer, ParentSerializer,
    DepartmentSerializer, SubjectSerializer,
    AttendanceSerializer, AttendanceCreateSerializer,
    GradeSerializer, GradeCreateSerializer,
    FeeStructureSerializer, FeePaymentSerializer, FeePaymentCreateSerializer,
    TimetableSerializer, TimetableCreateSerializer, FormerMemberSerializer,
    DocumentSerializer, NoticeSerializer, IssueSerializer, HolidaySerializer, AwardSerializer,
    AssignmentSerializer, LeaveSerializer, TaskSerializer,
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


# ------------------- STUDENT VIEWSET -------------------
class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    permission_classes = [AllowAny]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]  # type: ignore[assignment]
    filterset_fields = ['class_name', 'section', 'gender', 'blood_group']
    search_fields = ['fullname', 'student_id', 'email__email']
    ordering_fields = ['fullname', 'admission_date']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return StudentCreateSerializer
        return StudentSerializer

    @action(detail=False, methods=['get'])
    def by_class(self, request):
        """Get students by class name (and optional section)."""
        class_name = request.query_params.get('class_name')
        section = request.query_params.get('section')
        if class_name:
            qs = self.get_queryset().filter(class_name=class_name)
            if section:
                qs = qs.filter(section=section)
            serializer = self.get_serializer(qs, many=True)
            return Response(serializer.data)
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
    queryset = Attendance.objects.all()
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]  # type: ignore[assignment]
    filterset_fields = ['student', 'class_name', 'status', 'date']
    search_fields = ['student__fullname', 'student__student_id']
    ordering_fields = ['date', 'created_at']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return AttendanceCreateSerializer
        return AttendanceSerializer

    @action(detail=False, methods=['get'])
    def by_date_range(self, request):
        """Get attendance by date range"""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        if start_date and end_date:
            attendance = self.get_queryset().filter(date__range=[start_date, end_date])  # type: ignore[union-attr]
            serializer = self.get_serializer(attendance, many=True)
            return Response(serializer.data)
        return Response({'error': 'start_date and end_date parameters required'}, status=status.HTTP_400_BAD_REQUEST)


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
    filterset_fields = ['class_level', 'fee_type', 'frequency']
    search_fields = ['fee_type', 'description']

    @action(detail=False, methods=['get'])
    def by_class(self, request):
        """Get fee structure by class"""
        class_id = request.query_params.get('class_id')
        if class_id:
            fees = self.get_queryset().filter(class_level_id=class_id)  # type: ignore[union-attr]
            serializer = self.get_serializer(fees, many=True)
            return Response(serializer.data)
        return Response({'error': 'class_id parameter required'}, status=status.HTTP_400_BAD_REQUEST)


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
    filterset_fields = ['class_name', 'subject', 'teacher', 'day_of_week']
    search_fields = ['class_name', 'subject__subject_name', 'teacher__fullname']
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

        att, created = Attendance.objects.get_or_create(
            student=matched_student,
            date=today,
            defaults={
                'class_name': matched_student.class_name,
                'status': status_param or 'Present',
                'marked_by_role': actor_role,
                'remarks': remarks_param,
            }
        )
        if not created:
            # Update status/role if already exists
            att.status = status_param or 'Present'
            att.marked_by_role = actor_role
            if matched_student.class_name:
                att.class_name = matched_student.class_name
            if remarks_param is not None:
                att.remarks = remarks_param
            att.save()

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


# ------------------- ASSIGNMENT VIEWSET -------------------
class AssignmentViewSet(viewsets.ModelViewSet):
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]  # type: ignore[assignment]
    filterset_fields = ['subject', 'class_name', 'assigned_by', 'due_date']
    search_fields = ['title', 'description', 'subject__subject_name', 'assigned_by__email']
    ordering_fields = ['created_at', 'due_date']


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


# ------------------- NOTICE VIEWSET -------------------
class NoticeViewSet(viewsets.ModelViewSet):
    queryset = Notice.objects.all()
    serializer_class = NoticeSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]  # type: ignore[assignment]
    filterset_fields = ['email', 'important']
    search_fields = ['title', 'message', 'email__email']
    ordering_fields = ['posted_date', 'important']

    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Create multiple notices. Expects JSON array. Does not upsert."""
        if not isinstance(request.data, list):
            return Response({'error': 'Expected a JSON array'}, status=status.HTTP_400_BAD_REQUEST)
        ser = self.get_serializer(data=request.data, many=True)
        ser.is_valid(raise_exception=True)
        self.perform_create(ser)
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
