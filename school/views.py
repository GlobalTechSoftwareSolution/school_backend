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
from django.shortcuts import render
from django.shortcuts import get_object_or_404

from django.core.mail import send_mail
from django.db import models
from decimal import Decimal
import os, tempfile, requests, pytz
from geopy.distance import geodesic
from datetime import datetime, date, timedelta
try:
    import face_recognition
except Exception:  # pragma: no cover
    face_recognition = None

# Import barcode library
try:
    import barcode
    from barcode.writer import ImageWriter
except Exception:  # pragma: no cover
    barcode = None
    ImageWriter = None

# Define IST timezone for Indian Standard Time
IST = pytz.timezone("Asia/Kolkata")

from .models import (
    User, Student, Teacher, Principal, Management, Admin, Parent,
    Department, Subject, Attendance, StudentAttendance, Grade, FeeStructure,
    FeePayment, Timetable, FormerMember, Document, Notice, Issue, Holiday, Award, Assignment, SubmittedAssignment, Leave, Task,
    Project, Program, Activity, Report, FinanceTransaction, TransportDetails, Class, IDCard,
)
from .serializers import (
    UserSerializer, UserRegistrationSerializer,
    StudentSerializer, StudentCreateSerializer,
    TeacherSerializer, TeacherCreateSerializer,
    PrincipalSerializer, ManagementSerializer, AdminSerializer, ParentSerializer,
    DepartmentSerializer, SubjectSerializer, ClassSerializer,
    AttendanceSerializer, AttendanceCreateSerializer, AttendanceUpdateSerializer,
    StudentAttendanceSerializer, StudentAttendanceCreateSerializer,
    GradeSerializer, GradeCreateSerializer,
    FeeStructureSerializer, FeePaymentSerializer, FeePaymentCreateSerializer,
    TimetableSerializer, TimetableCreateSerializer, FormerMemberSerializer,
    DocumentSerializer, NoticeSerializer, IssueSerializer, HolidaySerializer, AwardSerializer,
    AssignmentSerializer, SubmittedAssignmentSerializer, SubmittedAssignmentCreateSerializer, LeaveSerializer, TaskSerializer,
    ProjectSerializer, ProgramSerializer, ActivitySerializer, ActivityCreateSerializer, ReportSerializer,
    FinanceTransactionSerializer, TransportDetailsSerializer, IDCardSerializer,
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

# ------------------- ID CARD VIEW -------------------
def id_card_view(request):
    """
    Serve the ID card template with user data
    """
    # Get the current authenticated user
    user = request.user
    
    # Initialize context with default values
    context = {
        'name': 'NAME SURNAME',
        'position': 'Your Position Here',
        'dob': 'MM/DD/YEAR',
        'email': 'email@example.com',
        'phone': '+91 9876543210',
        'id_no': 'RST-0012',
        'profile_picture': 'profile.jpg',
        'barcode': 'barcode.png',
        'company_name': 'SCHOOL NAME',
    }
    
    # If user is authenticated, populate with actual data
    if user.is_authenticated:
        context['email'] = user.email
        context['position'] = user.role
        
        # Try to get role-specific data
        if hasattr(user, 'student') and user.student:
            student = user.student
            context['name'] = student.fullname
            context['dob'] = student.date_of_birth.strftime('%m/%d/%Y') if student.date_of_birth else 'MM/DD/YEAR'
            context['phone'] = student.phone or '+91 9876543210'
            context['id_no'] = student.student_id or 'RST-0012'
            context['profile_picture'] = student.profile_picture or 'profile.jpg'
            
            # Add class information if available
            if student.class_id:
                context['position'] = f"Student - {student.class_id.class_name} {student.class_id.sec}"
                
        elif hasattr(user, 'teacher') and user.teacher:
            teacher = user.teacher
            context['name'] = teacher.fullname
            context['dob'] = teacher.date_of_birth.strftime('%m/%d/%Y') if teacher.date_of_birth else 'MM/DD/YEAR'
            context['phone'] = teacher.phone or '+91 9876543210'
            context['id_no'] = teacher.teacher_id or 'RST-0012'
            context['profile_picture'] = teacher.profile_picture or 'profile.jpg'
            
            # Add department information if available
            if teacher.department:
                context['position'] = f"Teacher - {teacher.department.department_name}"
                
        elif hasattr(user, 'principal') and user.principal:
            principal = user.principal
            context['name'] = principal.fullname
            context['dob'] = principal.date_of_birth.strftime('%m/%d/%Y') if principal.date_of_birth else 'MM/DD/YEAR'
            context['phone'] = principal.phone or '+91 9876543210'
            context['id_no'] = 'PRN-001'
            context['profile_picture'] = principal.profile_picture or 'profile.jpg'
            context['position'] = 'Principal'
            
        elif hasattr(user, 'management') and user.management:
            management = user.management
            context['name'] = management.fullname
            context['dob'] = management.date_of_birth.strftime('%m/%d/%Y') if management.date_of_birth else 'MM/DD/YEAR'
            context['phone'] = management.phone or '+91 9876543210'
            context['id_no'] = 'MGT-001'
            context['profile_picture'] = management.profile_picture or 'profile.jpg'
            
            # Add designation if available
            if management.designation:
                context['position'] = f"Management - {management.designation}"
                
        elif hasattr(user, 'admin') and user.admin:
            admin = user.admin
            context['name'] = admin.fullname
            context['phone'] = admin.phone or '+91 9876543210'
            context['id_no'] = 'ADM-001'
            context['profile_picture'] = admin.profile_picture or 'profile.jpg'
            context['position'] = 'Admin'
            
        elif hasattr(user, 'parent') and user.parent:
            parent = user.parent
            context['name'] = parent.fullname
            context['dob'] = parent.date_of_birth.strftime('%m/%d/%Y') if parent.date_of_birth else 'MM/DD/YEAR'
            context['phone'] = parent.phone or '+91 9876543210'
            context['id_no'] = 'PRT-001'
            context['profile_picture'] = parent.profile_picture or 'profile.jpg'
            context['position'] = 'Parent'
        
        # Check if ID card exists in database, if not create it
        try:
            from .models import IDCard
            # Check if ID card already exists for this user
            id_card, created = IDCard.objects.get_or_create(user=user)
            
            # If it was just created or doesn't have a URL, generate one
            if created or not id_card.id_card_url:
                # Generate ID card using IDCardViewSet methods
                id_card_viewset = IDCardViewSet()
                pdf_content = id_card_viewset._generate_id_card_pdf(user)
                url = id_card_viewset._upload_file_to_minio(user, pdf_content, user.email)
                if url:
                    id_card.id_card_url = url
                    id_card.save()
                
            # Add ID card URL to context if available
            if id_card.id_card_url:
                context['id_card_url'] = id_card.id_card_url
        except Exception:
            # If there's any error, continue with default behavior
            pass

    return render(request, 'index.html', context)


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
    filterset_fields = ['class_id', 'gender', 'blood_group', 'father_name', 'mother_name']
    search_fields = ['fullname', 'student_id', 'email__email', 'father_name', 'mother_name']
    ordering_fields = ['fullname', 'admission_date']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return StudentCreateSerializer
        return StudentSerializer

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

    @action(detail=False, methods=['get'])
    def by_class(self, request):
        """Get students by class name (and optional section)."""
        class_id = request.query_params.get('class_id')
        if class_id:
            qs = self.get_queryset().filter(class_id=class_id)
            serializer = self.get_serializer(qs, many=True)
            return Response(serializer.data)
        return Response({'error': 'class_id parameter required'}, status=status.HTTP_400_BAD_REQUEST)


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


# ------------------- ID CARD VIEWSET -------------------
class IDCardViewSet(viewsets.ModelViewSet):
    queryset = IDCard.objects.all()
    serializer_class = IDCardSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]  # type: ignore[assignment]
    filterset_fields = ['user']
    search_fields = ['user__email']
    ordering_fields = ['created_at', 'updated_at']

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

    def _object_name_for_idcard(self, user, fallback_email: str | None = None) -> str:
        identifier = None
        if hasattr(user, 'email'):
            identifier = user.email.replace('@', '_').replace('.', '_')
        if not identifier and fallback_email:
            identifier = fallback_email.replace('@', '_').replace('.', '_')
        if not identifier:
            identifier = 'unknown'
        return f"id_cards/{identifier}.pdf"

    def _upload_file_to_minio(self, user, pdf_content, fallback_email: str | None = None):
        client = self._minio_client()
        if client is None:
            return None
        bucket = settings.MINIO_STORAGE['BUCKET_NAME']
        object_name = self._object_name_for_idcard(user, fallback_email)
        
        # Upload PDF content directly
        client.put_object(bucket, object_name, pdf_content, len(pdf_content.getvalue()), content_type='application/pdf')
        base = settings.BASE_BUCKET_URL
        if not base.endswith('/'):
            base += '/'
        return f"{base}{object_name}"

    def _generate_id_card_pdf(self, user):
        """Generate PDF for the ID card using the theme from index.html."""
        try:
            # Import ReportLab modules for PDF generation
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.colors import Color
            from reportlab.lib.utils import ImageReader
            import requests
            from io import BytesIO
            
            # Get user details based on role
            user_name = getattr(user, 'email', 'Unknown User')
            position = getattr(user, 'role', 'Unknown Role')
            phone = ''
            id_no = ''
            profile_picture_url = ''
            dob = ''
            company_name = 'SCHOOL NAME'
            
            if hasattr(user, 'student') and user.student:
                student = user.student
                user_name = student.fullname
                dob = student.date_of_birth.strftime('%m/%d/%Y') if student.date_of_birth else 'MM/DD/YEAR'
                phone = student.phone or '+91 9876543210'
                id_no = student.student_id or 'RST-0012'
                profile_picture_url = student.profile_picture or 'profile.jpg'
                if student.class_id:
                    position = f"Student - {student.class_id.class_name} {student.class_id.sec}"
                    
            elif hasattr(user, 'teacher') and user.teacher:
                teacher = user.teacher
                user_name = teacher.fullname
                dob = teacher.date_of_birth.strftime('%m/%d/%Y') if teacher.date_of_birth else 'MM/DD/YEAR'
                phone = teacher.phone or '+91 9876543210'
                id_no = teacher.teacher_id or 'RST-0012'
                profile_picture_url = teacher.profile_picture or 'profile.jpg'
                if teacher.department:
                    position = f"Teacher - {teacher.department.department_name}"
                    
            elif hasattr(user, 'principal') and user.principal:
                principal = user.principal
                user_name = principal.fullname
                dob = principal.date_of_birth.strftime('%m/%d/%Y') if principal.date_of_birth else 'MM/DD/YEAR'
                phone = principal.phone or '+91 9876543210'
                id_no = 'PRN-001'
                profile_picture_url = principal.profile_picture or 'profile.jpg'
                position = 'Principal'
                
            elif hasattr(user, 'management') and user.management:
                management = user.management
                user_name = management.fullname
                dob = management.date_of_birth.strftime('%m/%d/%Y') if management.date_of_birth else 'MM/DD/YEAR'
                phone = management.phone or '+91 9876543210'
                id_no = 'MGT-001'
                profile_picture_url = management.profile_picture or 'profile.jpg'
                if management.designation:
                    position = f"Management - {management.designation}"
                    
            elif hasattr(user, 'admin') and user.admin:
                admin = user.admin
                user_name = admin.fullname
                phone = admin.phone or '+91 9876543210'
                id_no = 'ADM-001'
                profile_picture_url = admin.profile_picture or 'profile.jpg'
                position = 'Admin'
                
            elif hasattr(user, 'parent') and user.parent:
                parent = user.parent
                user_name = parent.fullname
                dob = parent.date_of_birth.strftime('%m/%d/%Y') if parent.date_of_birth else 'MM/DD/YEAR'
                phone = parent.phone or '+91 9876543210'
                id_no = 'PRT-001'
                profile_picture_url = parent.profile_picture or 'profile.jpg'
                position = 'Parent'

            # Create PDF with dimensions matching the HTML template (330px width)
            # Convert pixels to points (1 pixel = 0.75 points)
            # Increase height from 400 to 450 pixels to add more space below barcode
            width_points = 330 * 0.75
            height_points = 450 * 0.75
            
            # Create a BytesIO buffer for the PDF
            pdf_buffer = BytesIO()
            
            # Create canvas
            c = canvas.Canvas(pdf_buffer, pagesize=(width_points, height_points))
            
            # Define colors
            background_color = Color(0.913, 0.929, 0.945)  # #e9edf1
            header_color = Color(0.027, 0.153, 0.235)     # #07273C
            text_color = Color(0, 0, 0)                    # #000000
            gray_text = Color(0.467, 0.467, 0.467)        # #777777
            light_gray = Color(0.867, 0.867, 0.867)       # #dddddd
            
            # Draw background
            c.setFillColor(background_color)
            c.rect(0, 0, width_points, height_points, fill=1)
            
            # Draw header area (dark blue background)
            header_height = 120 * 0.75
            c.setFillColor(header_color)
            c.rect(0, height_points - header_height, width_points, header_height, fill=1)
            
            # Add company name in header
            c.setFillColor(Color(1, 1, 1))  # White text
            c.setFont("Helvetica-Bold", 15)
            c.drawCentredString(width_points/2, height_points - 35*0.75, company_name)
            
            # Removed skewed header effect to eliminate empty box lines
            
            # Draw profile picture area (110x110px)
            profile_size = 110 * 0.75
            profile_x = width_points // 2 - profile_size // 2
            # Move profile picture up (decrease offset from 100*0.75 to 90*0.75)
            profile_y = height_points - 90*0.75 - profile_size
            
            # Add white border around profile picture
            border_width = 5 * 0.75
            c.setFillColor(Color(1, 1, 1))  # White border
            c.rect(profile_x - border_width, profile_y - border_width, 
                   profile_size + 2*border_width, profile_size + 2*border_width, fill=1)
            
            # Load profile picture if available
            if profile_picture_url and profile_picture_url.strip() and profile_picture_url != 'profile.jpg':
                try:
                    # Add scheme if missing
                    if not profile_picture_url.startswith(('http://', 'https://')):
                        profile_picture_url = 'https://' + profile_picture_url
                    response = requests.get(profile_picture_url, timeout=10)
                    if response.status_code == 200:
                        profile_image_buffer = BytesIO(response.content)
                        # Draw profile picture
                        c.drawImage(ImageReader(profile_image_buffer), 
                                   profile_x, profile_y, 
                                   profile_size, profile_size)
                except Exception as e:
                    # If profile picture fails to load, continue without it
                    pass
            
            # Add user name and position (shifted upward)
            name_y = profile_y - 30*0.75  # Moved up from 40*0.75 to 30*0.75
            c.setFillColor(text_color)
            c.setFont("Helvetica-Bold", 15)
            c.drawCentredString(width_points/2, name_y, user_name)
            
            position_y = name_y - 22*0.75
            c.setFillColor(gray_text)
            c.setFont("Helvetica", 12)
            c.drawCentredString(width_points/2, position_y, position)
            
            # Add info section (shifted upward)
            info_start_y = position_y - 28*0.75  # Moved up from 38*0.75 to 28*0.75
            info_padding = 35 * 0.75
            info_x_start = info_padding
            info_x_end = width_points - info_padding
            
            # Draw info items (without email and horizontal lines)
            c.setFont("Helvetica-Bold", 10)
            c.setFillColor(text_color)
            
            info_items = [
                ('DOB:', dob),
                ('Phone:', phone),
                ('ID No:', id_no)
            ]
            
            current_y = info_start_y
            for label, value in info_items:
                # Draw label in bold
                c.setFont("Helvetica-Bold", 10)
                c.drawString(info_x_start, current_y, label)
                # Draw value aligned to the right
                c.setFont("Helvetica", 10)
                c.drawRightString(info_x_end, current_y, value)
                # Skip drawing horizontal lines
                # Increased line spacing from 18*0.75 to 25*0.75 for better readability
                current_y -= 25*0.75
            
            # Generate barcode
            try:
                # Import barcode modules if not already imported
                import barcode
                from barcode.writer import ImageWriter
                
                if barcode is not None and ImageWriter is not None:
                    code128 = barcode.get_barcode_class('code128')
                    barcode_instance = code128(user.email, writer=ImageWriter())
                    
                    # Generate the barcode image in memory without text
                    barcode_buffer = BytesIO()
                    barcode_instance.write(barcode_buffer, options={'write_text': False})
                    barcode_buffer.seek(0)
                    
                    # NOTE: We no longer upload barcode to MinIO separately
                    # The barcode is only embedded in the ID card PDF
                    
                    # Add barcode to PDF if available (centered)
                    # Move barcode upward (closer to info section)
                    barcode_y = current_y - 45*0.75  # Moved up from 55 to 45 pixels
                    barcode_width = 160 * 0.75
                    barcode_height = 45 * 0.75
                    barcode_x = width_points // 2 - barcode_width // 2
                    
                    # Draw barcode image
                    c.drawImage(ImageReader(barcode_buffer), 
                               barcode_x, barcode_y, 
                               barcode_width, barcode_height)
                    
                    # Add more space below the barcode (move footer down)
                    space_below_barcode = 40 * 0.75  # Moved up from 50 to 40 pixels
            except Exception as e:
                # If barcode generation fails, continue without it
                pass
                space_below_barcode = 0
            
            # Draw footer at the bottom of the card
            footer_height = 45 * 0.75
            footer_y = 0  # Position at the very bottom
            c.setFillColor(header_color)
            c.rect(0, footer_y, width_points, footer_height, fill=1)
            
            # Removed footer skewed effect to eliminate empty box lines
            
            # Save the PDF
            c.save()
            pdf_buffer.seek(0)
            
            return pdf_buffer
        except Exception as e:
            # If anything fails, return a simple placeholder PDF
            try:
                from reportlab.pdfgen import canvas
                from io import BytesIO
                
                width_points = 330 * 0.75
                height_points = 400 * 0.75
                
                pdf_buffer = BytesIO()
                c = canvas.Canvas(pdf_buffer, pagesize=(width_points, height_points))
                
                # Draw background
                c.setFillColor(Color(0.913, 0.929, 0.945))
                c.rect(0, 0, width_points, height_points, fill=1)
                
                # Add error message
                c.setFillColor(Color(0, 0, 0))
                c.setFont("Helvetica", 12)
                c.drawCentredString(width_points/2, height_points/2, 'ID Card Generation Failed')
                
                c.save()
                pdf_buffer.seek(0)
                
                return pdf_buffer
            except Exception:
                # If even the fallback fails, return a minimal PDF
                from reportlab.pdfgen import canvas
                from io import BytesIO
                
                width_points = 330 * 0.75
                height_points = 400 * 0.75
                
                pdf_buffer = BytesIO()
                c = canvas.Canvas(pdf_buffer, pagesize=(width_points, height_points))
                c.save()
                pdf_buffer.seek(0)
                
                return pdf_buffer

    @action(detail=False, methods=['get'])
    def check_by_email(self, request):
        """Check if ID card exists for user by email."""
        email = request.query_params.get('email')
        if not email:
            return Response({'error': 'Email parameter required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
            
        # Check if ID card exists
        try:
            id_card = IDCard.objects.get(user=user)
            serializer = self.get_serializer(id_card)
            return Response(serializer.data)
        except IDCard.DoesNotExist:
            return Response({'exists': False, 'message': 'ID card not found for this user'})
    
    @action(detail=False, methods=['post'])
    def generate_id_card(self, request):
        """Generate ID card for user: check if exists, if not create it."""
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email required'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
            
        # Check if ID card already exists
        id_card, created = IDCard.objects.get_or_create(user=user)
        
        # Always regenerate the ID card to ensure it's a PDF
        # Generate PDF content for ID card
        pdf_content = self._generate_id_card_pdf(user)
        
        # Upload to MinIO
        url = self._upload_file_to_minio(user, pdf_content, email)
        if url is None:
            return Response({'error': 'Failed to upload ID card to storage'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Save URL to database
        id_card.id_card_url = url
        id_card.save()
        
        serializer = self.get_serializer(id_card)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
            
        # Generate PDF content for ID card
        pdf_content = self._generate_id_card_pdf(user)
        
        # Upload to MinIO
        url = self._upload_file_to_minio(user, pdf_content, email)
        if url is None:
            return Response({'error': 'Failed to upload ID card to storage'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        # Save URL to database
        id_card.id_card_url = url
        id_card.save()
        
        serializer = self.get_serializer(id_card)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

def _generate_barcode_for_user(user):
    """Generate a barcode for a user and return the MinIO URL without uploading."""
    # Check if barcode library is available
    if barcode is None or ImageWriter is None:
        raise Exception('Barcode generation library not installed. Please install python-barcode.')
    
    try:
        # Create a Code128 barcode using the user's email as the data
        code128 = barcode.get_barcode_class('code128')
        if code128 is None:
            raise Exception('Failed to get barcode class')
        barcode_instance = code128(user.email, writer=ImageWriter())
        
        # Generate the barcode image in memory without text
        from io import BytesIO
        buffer = BytesIO()
        # Write the barcode without text
        barcode_instance.write(buffer, options={'write_text': False})
        buffer.seek(0)
        
        # NOTE: We no longer upload barcode to MinIO separately
        # The barcode is only embedded in the ID card PDF
        # Return None to indicate no separate storage
        return None
    except Exception as e:
        # Re-raise the exception with more details
        raise Exception(f'Failed to generate barcode: {str(e)}')


def _object_name_for_barcode_global(user) -> str:
    """Generate object name for user barcode."""
    # This function is no longer used since we don't store barcodes separately
    return ""


# ------------------- USER REGISTRATION -------------------
# Class UserRegistrationView was removed as it was a duplicate of the register_user function


# ------------------- TIMETABLE VIEWSET -------------------
class TimetableViewSet(viewsets.ModelViewSet):
    queryset = Timetable.objects.all()
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]  # type: ignore[assignment]
    filterset_fields = ['class_id', 'subject', 'teacher', 'day_of_week']
    search_fields = ['subject__subject_name', 'teacher__fullname']
    ordering_fields = ['day_of_week', 'start_time']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return TimetableCreateSerializer
        return TimetableSerializer

    @action(detail=False, methods=['get'])
    def by_class(self, request):
        """Get timetable by class"""
        class_id = request.query_params.get('class_id')
        if class_id:
            timetable = self.get_queryset().filter(class_id=class_id)
            serializer = self.get_serializer(timetable, many=True)
            return Response(serializer.data)
        return Response({'error': 'class_id parameter required'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def by_teacher(self, request):
        """Get timetable by teacher"""
        teacher_email = request.query_params.get('teacher_email')
        if teacher_email:
            timetable = self.get_queryset().filter(teacher__email=teacher_email)  # type: ignore[union-attr]
            serializer = self.get_serializer(timetable, many=True)
            return Response(serializer.data)
        return Response({'error': 'teacher_email parameter required'}, status=status.HTTP_400_BAD_REQUEST)

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
    filterset_fields = ['department', 'gender', 'blood_group', 'is_classteacher', 'class_id']
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
    queryset = Attendance.objects.all().select_related('user')
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
        Mark attendance for a user (except parents)
        Required: user_email
        Optional: date, check_in, check_out, marked_by_role
        """
        user_email = request.data.get('user_email')
        if not user_email:
            return Response(
                {'error': 'user_email is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=user_email)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
            
        # Check if user is a parent (parents should not have attendance)
        if user.role == 'Parent':
            return Response(
                {'error': 'Parents cannot have attendance records'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get current time with seconds precision in IST
        now = timezone.now().astimezone(IST)
        current_time = now.time()
        current_date = now.date()
        
        # Get or create attendance record
        attendance, created = Attendance.objects.get_or_create(
            user=user,
            date=current_date,
            defaults={
                'check_in': current_time,
                'user': user
            }
        )

        # If updating existing record (e.g., for check-out)
        if not created:
            if 'check_out' in request.data and not attendance.check_out:
                attendance.check_out = request.data['check_out']
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
    def get_users_for_marking(self, request):
        """
        Get users (except parents) for marking attendance
        """
        # Get all non-parent users
        users_qs = User.objects.exclude(role='Parent')
        
        today = timezone.now().astimezone(IST).date()
        users_data = []

        for user in users_qs:
            # Get or create attendance for today
            attendance, created = Attendance.objects.get_or_create(
                user=user,
                date=today,
                defaults={
                    'user': user
                }
            )
            
            # Get user name based on their role
            user_name = user.email  # Default to email
            if hasattr(user, 'admin') and user.admin:
                user_name = user.admin.fullname
            elif hasattr(user, 'teacher') and user.teacher:
                user_name = user.teacher.fullname
            elif hasattr(user, 'principal') and user.principal:
                user_name = user.principal.fullname
            elif hasattr(user, 'management') and user.management:
                user_name = user.management.fullname
            elif hasattr(user, 'student') and user.student:
                user_name = user.student.fullname
            
            users_data.append({
                'user_id': getattr(user, 'admin', getattr(user, 'teacher', getattr(user, 'principal', getattr(user, 'management', getattr(user, 'student', None))))),
                'fullname': user_name,
                'email': user.email,
                'role': user.role,
                'status': attendance.status
            })

        return Response({
            'date': today,
            'users': users_data
        })

    @action(detail=False, methods=['post'])
    def bulk_update_status(self, request):
        """
        POST /api/attendance/bulk_update_status/
        Bulk update attendance status for users (except parents).
        Body: {
            "marked_by_email": "admin@example.com",
            "date": "2023-10-01",  // optional, defaults to today
            "updates": [
                {"user_email": "teacher1@example.com", "status": "Present"},
                {"user_email": "principal1@example.com", "status": "Absent"}
            ]
        }
        """

        marked_by_email = request.data.get('marked_by_email')
        date_str = request.data.get('date')
        updates = request.data.get('updates', [])

        if not marked_by_email:
            return Response({'error': 'marked_by_email required'}, status=status.HTTP_400_BAD_REQUEST)
        if not updates:
            return Response({'error': 'updates list required'}, status=status.HTTP_400_BAD_REQUEST)

        # Verify the marker exists
        try:
            marker = User.objects.get(email=marked_by_email)
        except User.DoesNotExist:
            return Response({'error': 'Marker user not found'}, status=status.HTTP_404_NOT_FOUND)

        # Parse date
        if date_str:
            try:
                target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response({'error': 'Invalid date format. Use YYYY-MM-DD'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            target_date = timezone.now().astimezone(IST).date()

        updated_count = 0
        errors = []

        for update in updates:
            user_email = update.get('user_email')
            new_status = update.get('status')
            if not user_email or new_status not in ['Present', 'Absent']:
                errors.append({'update': update, 'error': 'Invalid user_email or status'})
                continue

            try:
                user = User.objects.get(email=user_email)
                
                # Skip parents
                if user.role == 'Parent':
                    errors.append({'user_email': user_email, 'error': 'Parents cannot have attendance records'})
                    continue

                # Get or create attendance record with proper defaults
                attendance, created = Attendance.objects.get_or_create(
                    user=user,
                    date=target_date,
                    defaults={
                        'status': new_status,
                        'user': user  # This ensures the role is set correctly in save()
                    }
                )
                
                # If the record already existed, update the status
                if not created:
                    attendance.status = new_status
                    attendance.save()
                    
                updated_count += 1

            except User.DoesNotExist:
                errors.append({'user_email': user_email, 'error': 'User not found'})

        return Response({
            'marked_by_email': marked_by_email,
            'updated_count': updated_count,
            'date': target_date,
            'errors': errors
        })

# ------------------- STUDENT ATTENDANCE VIEWSET -------------------
class StudentAttendanceViewSet(viewsets.ModelViewSet):
    queryset = StudentAttendance.objects.all().select_related('student', 'subject', 'teacher', 'class_id')
    serializer_class = StudentAttendanceSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]  # type: ignore[assignment]
    filterset_fields = ['student', 'subject', 'teacher', 'class_id', 'date', 'status']
    search_fields = ['student__fullname', 'subject__subject_name', 'teacher__fullname', 'class_id__class_name']
    ordering_fields = ['date', 'created_time', 'student__fullname']

    def get_serializer_class(self):
        if self.action == 'create':
            return StudentAttendanceCreateSerializer
        return StudentAttendanceSerializer

    def list(self, request):
        """
        GET /api/student-attendance/
        Returns all student attendance records from the database
        """
        return super().list(request)

    @action(detail=False, methods=['get'])
    def by_student(self, request):
        """
        GET /api/student-attendance/by_student/
        Get attendance records for a specific student
        """
        student_email = request.query_params.get('student_email')
        if not student_email:
            return Response({'error': 'student_email parameter required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            student = Student.objects.get(email=student_email)
        except Student.DoesNotExist:
            return Response({'error': 'Student not found'}, status=status.HTTP_404_NOT_FOUND)
            
        attendance_records = self.get_queryset().filter(student=student)
        serializer = self.get_serializer(attendance_records, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_class(self, request):
        """
        GET /api/student-attendance/by_class/
        Get attendance records for a specific class
        """
        class_id = request.query_params.get('class_id')
        if not class_id:
            return Response({'error': 'class_id parameter required'}, status=status.HTTP_400_BAD_REQUEST)
        
        attendance_records = self.get_queryset().filter(class_id=class_id)
        serializer = self.get_serializer(attendance_records, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_subject(self, request):
        """
        GET /api/student-attendance/by_subject/
        Get attendance records for a specific subject
        """
        subject_id = request.query_params.get('subject_id')
        if not subject_id:
            return Response({'error': 'subject_id parameter required'}, status=status.HTTP_400_BAD_REQUEST)
        
        attendance_records = self.get_queryset().filter(subject=subject_id)
        serializer = self.get_serializer(attendance_records, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """
        POST /api/student-attendance/bulk_create/
        Create multiple student attendance records
        Body: [
            {
                "student": "student@example.com",
                "subject": 1,
                "teacher": "teacher@example.com",
                "class_id": 1,
                "date": "2023-10-01",
                "status": "Present"
            },
            ...
        ]
        """
        if not isinstance(request.data, list):
            return Response({'error': 'Expected a JSON array'}, status=status.HTTP_400_BAD_REQUEST)
        
        created_count = 0
        errors = []
        
        for idx, record_data in enumerate(request.data):
            try:
                # Create a serializer instance for validation
                serializer = StudentAttendanceCreateSerializer(data=record_data)
                if serializer.is_valid():
                    serializer.save()
                    created_count += 1
                else:
                    errors.append({'index': idx, 'errors': serializer.errors, 'data': record_data})
            except Exception as e:
                errors.append({'index': idx, 'error': str(e), 'data': record_data})
        
        return Response({
            'created_count': created_count,
            'errors': errors
        }, status=status.HTTP_201_CREATED if not errors else status.HTTP_207_MULTI_STATUS)

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
    filterset_fields = ['class_id', 'fee_type', 'frequency']
    search_fields = ['fee_type', 'description']

    @action(detail=False, methods=['get'])
    def by_class(self, request):
        """Get fee structure by class"""
        class_id = request.query_params.get('class_id')
        if class_id:
            fees = self.get_queryset().filter(class_id=class_id)
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


# ------------------- ACTIVITY VIEWSET -------------------
class ActivityViewSet(viewsets.ModelViewSet):
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]  # type: ignore[assignment]
    filterset_fields = ['type', 'conducted_by', 'class_id', 'date']
    search_fields = ['name', 'description', 'conducted_by__email']
    ordering_fields = ['date', 'created_at']
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ActivityCreateSerializer
        return ActivitySerializer


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
# =================== FACE + LOCATION ATTENDANCE (ALL USERS) ===================
# Office location and radius
OFFICE_LAT = 13.068906816007116
OFFICE_LON = 77.55541294505542
LOCATION_RADIUS_METERS = 1000
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
    """Mark attendance by matching face image and verifying location for all users (except parents)."""
    # Only require face_recognition if an image is provided; allow deterministic marking via user_email otherwise
    # Get request parameters from both POST data and JSON data
    if request.content_type == 'application/json':
        # Handle JSON data
        data = request.data
        forced_email = data.get('user_email')
        barcode = data.get('barcode')
        lat = data.get('latitude')
        lon = data.get('longitude')
    else:
        # Handle form data
        forced_email = request.POST.get('user_email')
        barcode = request.POST.get('barcode')
        lat = request.POST.get('latitude')
        lon = request.POST.get('longitude')
    
    # Check if face_recognition is available
    if face_recognition is None:
        # If face_recognition is not available, we can only process barcode or email
        uploaded_file = request.FILES.get('image') or request.FILES.get('file')
        if uploaded_file or (request.content_type == 'application/json' and request.data.get('image')):
            if not barcode and not forced_email:
                return JsonResponse({
                    'status': 'error',
                    'message': 'face_recognition package not installed. Please install dependencies or provide user_email or barcode without an image.'
                }, status=500)
    
    # Validate that we have the required data
    if not lat and not lon:
        return JsonResponse({'status': 'fail', 'message': 'Latitude and longitude required'}, status=400)

    if lat is None or lon is None:
        return JsonResponse({'status': 'fail', 'message': 'Latitude and longitude required'}, status=400)
    try:
        lat_f = float(lat)
        lon_f = float(lon)
    except (ValueError, TypeError):
        return JsonResponse({'status': 'fail', 'message': 'Invalid latitude or longitude'}, status=400)

    uploaded_file = request.FILES.get('image') or request.FILES.get('file')
    # forced_email and barcode are already defined above
    
    # Require at least one method: image, email, or barcode
    if not uploaded_file and not forced_email and not barcode:
        return JsonResponse({'status': 'fail', 'message': 'Provide either user_email, barcode, or an image'}, status=400)
    
    # Validate that if we have an uploaded file, it's not empty
    if uploaded_file and uploaded_file.size == 0:
        return JsonResponse({'status': 'fail', 'message': 'Uploaded file is empty'}, status=400)

    tmp_path = None
    if uploaded_file:
        # Get the file extension from the uploaded file
        file_extension = '.jpg'  # default
        if hasattr(uploaded_file, 'name'):
            name = getattr(uploaded_file, 'name', '')
            if name and '.' in name:
                ext = name.split('.')[-1].lower()
                # Validate extension is a common image format
                if ext in ['jpg', 'jpeg', 'png', 'bmp', 'tiff']:
                    file_extension = '.' + ext
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp:
            for chunk in uploaded_file.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name

    try:
        uploaded_encoding = None
        if tmp_path:
            try:
                fr = face_recognition
                if fr is None:
                    # If face_recognition is not available, try fallback methods
                    if not barcode and not forced_email:
                        return JsonResponse({'status': 'fail', 'message': 'Face recognition library not available. Please provide barcode or user_email as fallback.'}, status=400)
                else:
                    try:
                        uploaded_img = fr.load_image_file(tmp_path)
                        uploaded_encodings = fr.face_encodings(uploaded_img)
                        if not uploaded_encodings:
                            # If face detection fails, try barcode as fallback
                            if not barcode and not forced_email:
                                return JsonResponse({'status': 'fail', 'message': 'No face detected. Please provide barcode or user_email as fallback.'}, status=400)
                        else:
                            uploaded_encoding = uploaded_encodings[0]
                            # Validate the encoding to prevent array comparison issues
                            try:
                                # Try to convert to a list if it's a numpy array
                                import numpy as np
                                if isinstance(uploaded_encoding, np.ndarray):
                                    # Convert to list to avoid comparison issues
                                    uploaded_encoding = uploaded_encoding.tolist()
                            except ImportError:
                                # numpy not available, keep as is
                                pass
                    except ValueError as ve:
                        # Handle numpy array comparison errors
                        if not barcode and not forced_email:
                            return JsonResponse({'status': 'fail', 'message': f'ValueError processing uploaded image: {str(ve)}. Please provide barcode or user_email as fallback.'}, status=400)
                    except Exception as e:
                        # If there's an error processing the image, try fallback methods
                        if not barcode and not forced_email:
                            return JsonResponse({'status': 'fail', 'message': f'Error processing uploaded image: {str(e)}. Please provide barcode or user_email as fallback.'}, status=400)
            except Exception as e:
                # If there's an error processing the image, try fallback methods
                if not barcode and not forced_email:
                    return JsonResponse({'status': 'fail', 'message': f'Error processing image: {str(e)}. Please provide barcode or user_email as fallback.'}, status=400)

        # Determine target user (excluding parents)
        matched_user = None
        from .models import User, Attendance  # local import to avoid cycles
        
        # Try barcode first if provided
        if barcode:
            try:
                # Assuming barcode is the user's email for simplicity
                # In a real implementation, you might have a separate barcode field
                matched_user = User.objects.get(email=barcode)
                # Check if user is a parent or student (these roles should not have attendance)
                if matched_user.role == 'Parent' or matched_user.role == 'Student':
                    return JsonResponse({'status': 'fail', 'message': f'Invalid user role: {matched_user.role}. Only staff members can mark attendance.'}, status=400)
            except User.DoesNotExist:
                # If barcode lookup fails, continue with other methods
                if not uploaded_file and not forced_email:
                    return JsonResponse({'status': 'fail', 'message': f'User not found for barcode: {barcode}'}, status=404)
        
        # Try forced email if provided and barcode didn't work
        if forced_email and not matched_user:
            try:
                matched_user = User.objects.get(email=forced_email)
                # Check if user is a parent or student (these roles should not have attendance)
                if matched_user.role == 'Parent' or matched_user.role == 'Student':
                    return JsonResponse({'status': 'fail', 'message': f'Invalid user role: {matched_user.role}. Only staff members can mark attendance.'}, status=400)
            except User.DoesNotExist:
                return JsonResponse({'status': 'fail', 'message': f'User not found: {forced_email}'}, status=404)
        
        # Try face recognition if image was provided and other methods didn't work
        elif uploaded_encoding is not None and not matched_user:
            # Validate that we have a proper encoding
            if not isinstance(uploaded_encoding, list) and not hasattr(uploaded_encoding, '__len__'):
                # If the encoding is not valid, try fallback methods
                if not barcode and not forced_email:
                    return JsonResponse({'status': 'fail', 'message': 'Invalid face encoding. Please provide barcode or user_email as fallback.'}, status=400)
            
            # Additional validation for numpy arrays
            try:
                # Try to convert to list if it's a numpy array to avoid comparison issues
                import numpy as np
                if isinstance(uploaded_encoding, np.ndarray):
                    # Ensure it's a 1D array of numbers
                    if uploaded_encoding.ndim != 1:
                        if not barcode and not forced_email:
                            return JsonResponse({'status': 'fail', 'message': 'Invalid face encoding format. Please provide barcode or user_email as fallback.'}, status=400)
            except ImportError:
                # numpy not available, skip this check
                pass
            # Auto-set check_in for face recognition flow
            check_in = timezone.now().time()
            
            # Iterate over users (only staff members) with profile images and pick the best match by distance
            best_user = None
            best_distance = None
            # Get only staff users (not students or parents) with profile pictures
            # We need to check profile pictures in related models since User doesn't have this field directly
            candidates = User.objects.exclude(role__in=['Parent', 'Student']).filter(
                models.Q(teacher__profile_picture__isnull=False) & ~models.Q(teacher__profile_picture='') |
                models.Q(admin__profile_picture__isnull=False) & ~models.Q(admin__profile_picture='') |
                models.Q(principal__profile_picture__isnull=False) & ~models.Q(principal__profile_picture='') |
                models.Q(management__profile_picture__isnull=False) & ~models.Q(management__profile_picture='')
            ).select_related('teacher', 'admin', 'principal', 'management').distinct()
            
            for user in candidates:
                try:
                    # Get the actual user profile object to access profile_picture
                    profile_obj = None
                    if hasattr(user, 'admin') and user.admin and user.admin.profile_picture:
                        profile_obj = user.admin
                    elif hasattr(user, 'teacher') and user.teacher and user.teacher.profile_picture:
                        profile_obj = user.teacher
                    elif hasattr(user, 'principal') and user.principal and user.principal.profile_picture:
                        profile_obj = user.principal
                    elif hasattr(user, 'management') and user.management and user.management.profile_picture:
                        profile_obj = user.management
                    
                    # Skip users without a profile object
                    if profile_obj is None:
                        continue
                    
                    if not profile_obj or not profile_obj.profile_picture:
                        continue
                        
                    resp = requests.get(profile_obj.profile_picture, timeout=10)
                    if resp.status_code != 200:
                        continue
                    # Determine file extension from content type or default to .jpg
                    file_extension = '.jpg'  # default
                    content_type = resp.headers.get('content-type', '')
                    if 'png' in content_type:
                        file_extension = '.png'
                    elif 'jpeg' in content_type:
                        file_extension = '.jpeg'
                    elif 'jpg' in content_type:
                        file_extension = '.jpg'
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as s_tmp:
                        s_tmp.write(resp.content)
                        s_path = s_tmp.name
                    try:
                        fr = face_recognition
                        if fr is None:
                            # Skip face recognition if library is not available
                            if os.path.exists(s_path):
                                os.remove(s_path)
                            continue
                        s_img = fr.load_image_file(s_path)
                        s_encs = fr.face_encodings(s_img)
                        if os.path.exists(s_path):
                            os.remove(s_path)
                        if not s_encs:
                            continue
                        # Validate uploaded encoding before computing distance
                        if uploaded_encoding is None:
                            continue
                        
                        # Additional validation for the encoding
                        try:
                            # Ensure encoding is a list or can be converted to list
                            if not isinstance(uploaded_encoding, (list, tuple)):
                                import numpy as np
                                if not isinstance(uploaded_encoding, np.ndarray):
                                    continue  # Skip if not a valid encoding format
                        except ImportError:
                            # numpy not available
                            if not isinstance(uploaded_encoding, (list, tuple)):
                                continue  # Skip if not a valid encoding format
                        # Compute distance and keep the closest under threshold
                        try:
                            # Convert back to numpy array for face_distance calculation
                            import numpy as np
                            uploaded_encoding_np = np.array(uploaded_encoding) if isinstance(uploaded_encoding, list) else uploaded_encoding
                            distances = fr.face_distance([s_encs[0]], uploaded_encoding_np)
                            if len(distances) > 0:
                                distance_val = float(distances[0])
                                # Stricter threshold to avoid random mismatches
                                if distance_val <= 0.45 and (best_distance is None or distance_val < best_distance):
                                    best_distance = distance_val
                                    best_user = user
                        except (ValueError, TypeError) as ve:
                            # Handle the specific numpy array comparison error
                            # This can happen when comparing arrays directly
                            pass  # Continue with other users
                        except Exception as e:
                            # If distance calculation fails, continue with other users
                            pass
                    except Exception:
                        # If there's an error processing this user's image, continue with others
                        if os.path.exists(s_path):
                            os.remove(s_path)
                        continue
                except Exception:
                    continue
            matched_user = best_user

        if matched_user is None:
            # DEBUG: Return detailed info about why it failed
            debug_info = []
            
            # Re-run the loop to gather debug info (only if we have an encoding)
            if uploaded_encoding is not None:
                candidates = User.objects.exclude(role__in=['Parent', 'Student']).filter(
                    models.Q(teacher__profile_picture__isnull=False) & ~models.Q(teacher__profile_picture='') |
                    models.Q(admin__profile_picture__isnull=False) & ~models.Q(admin__profile_picture='') |
                    models.Q(principal__profile_picture__isnull=False) & ~models.Q(principal__profile_picture='') |
                    models.Q(management__profile_picture__isnull=False) & ~models.Q(management__profile_picture='')
                ).select_related('teacher', 'admin', 'principal', 'management').distinct()
                
                for user in candidates:
                    try:
                        profile_obj = None
                        if hasattr(user, 'admin') and user.admin and user.admin.profile_picture: profile_obj = user.admin
                        elif hasattr(user, 'teacher') and user.teacher and user.teacher.profile_picture: profile_obj = user.teacher
                        elif hasattr(user, 'principal') and user.principal and user.principal.profile_picture: profile_obj = user.principal
                        elif hasattr(user, 'management') and user.management and user.management.profile_picture: profile_obj = user.management
                        
                        if not profile_obj: continue
                        
                        debug_entry = {'email': user.email, 'url': profile_obj.profile_picture, 'status': 'Checking'}
                        
                        try:
                            resp = requests.get(profile_obj.profile_picture, timeout=5)
                            if resp.status_code != 200:
                                debug_entry['status'] = f'Download Failed: {resp.status_code}'
                                debug_info.append(debug_entry)
                                continue
                            
                            # Determine extension
                            file_extension = '.jpg'
                            content_type = resp.headers.get('content-type', '')
                            if 'png' in content_type: file_extension = '.png'
                            elif 'jpeg' in content_type: file_extension = '.jpeg'
                            
                            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as s_tmp:
                                s_tmp.write(resp.content)
                                s_path = s_tmp.name
                                
                            try:
                                # Check if face_recognition is available before calling its methods
                                if face_recognition is not None:
                                    s_img = face_recognition.load_image_file(s_path)
                                    s_encs = face_recognition.face_encodings(s_img)
                                    if not s_encs:
                                        debug_entry['status'] = 'No face found in profile pic'
                                    else:
                                        # Convert back to numpy array for face_distance calculation
                                        import numpy as np
                                        uploaded_encoding_np = np.array(uploaded_encoding) if isinstance(uploaded_encoding, list) else uploaded_encoding
                                        # Check if face_recognition is still available before calling face_distance
                                        if face_recognition is not None:
                                            distances = face_recognition.face_distance([s_encs[0]], uploaded_encoding_np)
                                            dist = float(distances[0])
                                            debug_entry['status'] = f'Distance: {dist:.4f}'
                                            debug_entry['match'] = dist <= 0.45
                                        else:
                                            debug_entry['status'] = 'Face recognition library not available for distance calculation'
                                else:
                                    debug_entry['status'] = 'Face recognition library not available'
                            except Exception as e:
                                debug_entry['status'] = f'Processing Error: {str(e)}'
                            finally:
                                if os.path.exists(s_path): os.remove(s_path)
                        except Exception as e:
                            debug_entry['status'] = f'Connection Error: {str(e)}'
                        
                        debug_info.append(debug_entry)
                    except Exception:
                        continue

            return JsonResponse({
                'status': 'fail', 
                'message': 'No matching user found',
                'debug_info': debug_info
            }, status=404)

        # Verify location proximity
        try:
            is_within, distance_m = _verify_location(lat_f, lon_f)
            if not is_within:
                return JsonResponse({
                    'status': 'fail',
                    'message': f'Too far from office ({distance_m:.2f}m). Must be within {LOCATION_RADIUS_METERS}m.'
                }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'fail',
                'message': f'Error verifying location: {str(e)}'
            }, status=400)

        # Mark attendance for today (works regardless of USE_TZ setting)
        today = timezone.now().astimezone(IST).date()
        # Allow overriding status and remarks
        status_param = request.POST.get('status')
        if status_param not in (None, 'Present', 'Absent'):
            status_param = None
        remarks_param = request.POST.get('remarks')
        
        # Validate that we have a valid user before proceeding
        if matched_user is None:
            return JsonResponse({'status': 'fail', 'message': 'No valid user found for attendance'}, status=404)

        # Create or update attendance record with auto check_in
        # Only set check_in time if we used face recognition
        # Validate face recognition before using in conditional
        face_recognition_used = False
        try:
            face_recognition_used = (uploaded_encoding is not None and matched_user == best_user)
        except (ValueError, TypeError):
            # Handle array comparison issues
            face_recognition_used = False
            
        attendance_data = {
            'check_in': timezone.now().time() if face_recognition_used else None,
            'status': 'Present',  # Auto-mark as present
            'user': matched_user
        }
        attendance, created = Attendance.objects.update_or_create(
            user=matched_user,
            date=today,
            defaults=attendance_data
        )
        if not created:
            attendance.status = status_param or 'Present'
            attendance.save()

        # Get user name based on their role
        user_name = matched_user.email  # Default to email
        if hasattr(matched_user, 'admin') and matched_user.admin:
            user_name = matched_user.admin.fullname
        elif hasattr(matched_user, 'teacher') and matched_user.teacher:
            user_name = matched_user.teacher.fullname
        elif hasattr(matched_user, 'principal') and matched_user.principal:
            user_name = matched_user.principal.fullname
        elif hasattr(matched_user, 'management') and matched_user.management:
            user_name = matched_user.management.fullname
        elif hasattr(matched_user, 'student') and matched_user.student:
            user_name = matched_user.student.fullname
            
        # Determine which method was used
        method_used = "email"
        if barcode and matched_user.email == barcode:
            method_used = "barcode"
        else:
            # Validate face recognition usage to avoid array comparison issues
            try:
                if uploaded_encoding is not None and matched_user == best_user:
                    method_used = "face_recognition"
            except (ValueError, TypeError):
                # Handle array comparison issues
                pass
            
        return JsonResponse({
            'status': 'success',
            'message': f'Attendance marked for {user_name}',
            'user': user_name,
            'email': matched_user.email,
            'date': str(today),
            'role': matched_user.role,
            'method_used': method_used
        })
    except ValueError as ve:
        # Handle ValueError specifically
        try:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass
        return JsonResponse({
            'status': 'fail',
            'message': f'ValueError: {str(ve)}. This might be due to invalid data types in face recognition processing.'
        }, status=400)
    except Exception as e:
        # Clean up temporary files even if there's an error
        try:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass
        # Return a more user-friendly error message
        return JsonResponse({
            'status': 'fail',
            'message': f'An error occurred: {str(e)}'
        }, status=500)
    finally:
        try:
            if tmp_path and os.path.exists(tmp_path):
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
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]  # type: ignore[assignment]
    filterset_fields = ['subject', 'class_id', 'assigned_by', 'due_date', 'status']
    search_fields = ['title', 'description', 'subject__subject_name', 'assigned_by__email']
    ordering_fields = ['created_at', 'due_date']

    def _upload_student_submission_to_minio(self, assignment, file):
        """Upload student submission file to MinIO and return URL."""
        client = _minio_client_global()
        if client is None:
            return None
        bucket = settings.MINIO_STORAGE['BUCKET_NAME']
        base = settings.BASE_BUCKET_URL
        if not base.endswith('/'):
            base += '/'
        
        # Create a unique identifier for the assignment submission
        import os as _os
        _, ext = _os.path.splitext(getattr(file, 'name', '') or '')
        if not ext:
            ext = '.bin'
        
        # Generate object name based on assignment ID and student info
        object_name = f"assignments/{assignment.id}/submissions/{assignment.class_id.class_name}_{assignment.class_id.sec}_{assignment.title.replace(' ', '_')}_{timezone.now().strftime('%Y%m%d_%H%M%S')}{ext}"
        
        client.put_object(bucket, object_name, file.file, file.size, content_type=getattr(file, 'content_type', 'application/octet-stream'))
        return f"{base}{object_name}"

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

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        assignment = Assignment.objects.get(pk=response.data['id'])
        # Send emails to students and parents
        try:
            students = Student.objects.filter(class_id=assignment.class_id)
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

    def update(self, request, *args, **kwargs):
        # Handle file uploads for student submissions
        instance = self.get_object()
        
        # If there's a file in the request, handle it
        if 'student_submission_file' in request.FILES:
            file = request.FILES['student_submission_file']
            
            # Delete previous submission if it exists
            if instance.student_submission:
                self._delete_minio_object_by_url(instance.student_submission)
            
            # Upload new file to MinIO
            url = self._upload_student_submission_to_minio(instance, file)
            if url is None:
                return Response({'error': 'Failed to upload file to storage'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Update the student_submission field
            instance.student_submission = url
            instance.save()
            
            # Also update status to 'Submitted' if it's not already
            if instance.status != 'Submitted':
                instance.status = 'Submitted'
                instance.save()
        
        # Continue with normal update process
        return super().update(request, *args, **kwargs)

    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def submit(self, request, pk=None):
        """Submit an assignment with a file upload."""
        assignment = self.get_object()
        
        # Check if student is in the class
        student_email = request.data.get('student_email')
        if not student_email:
            return Response({'error': 'student_email is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            student = Student.objects.get(email=student_email)
        except Student.DoesNotExist:
            return Response({'error': 'Student not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Verify student is in the correct class
        if student.class_id != assignment.class_id:
            return Response({'error': 'Student is not enrolled in this class'}, status=status.HTTP_403_FORBIDDEN)
        
        # Handle file upload
        if 'file' not in request.FILES:
            return Response({'error': 'file is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        file = request.FILES['file']
        
        # Delete previous submission if it exists
        if assignment.student_submission:
            self._delete_minio_object_by_url(assignment.student_submission)
        
        # Upload new file to MinIO
        url = self._upload_student_submission_to_minio(assignment, file)
        if url is None:
            return Response({'error': 'Failed to upload file to storage'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Update the assignment
        assignment.student_submission = url
        assignment.status = 'Submitted'
        assignment.save()
        
        return Response({
            'message': 'Assignment submitted successfully',
            'student_submission': url,
            'status': assignment.status
        })


# ------------------- SUBMITTED ASSIGNMENT VIEWSET -------------------
class SubmittedAssignmentViewSet(viewsets.ModelViewSet):
    queryset = SubmittedAssignment.objects.all()
    serializer_class = SubmittedAssignmentSerializer
    permission_classes = [AllowAny]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]  # type: ignore[assignment]
    filterset_fields = ['assignment', 'student', 'is_late']
    search_fields = ['assignment__title', 'student__fullname', 'student__email__email']
    ordering_fields = ['submission_date', 'assignment__due_date']
    
    def _upload_student_submission_to_minio(self, submitted_assignment, file, assignment=None, student=None):
        """Upload student submission file to MinIO and return URL."""
        client = _minio_client_global()
        if client is None:
            return None
        bucket = settings.MINIO_STORAGE['BUCKET_NAME']
        base = settings.BASE_BUCKET_URL
        if not base.endswith('/'):
            base += '/'
        
        # Create a unique identifier for the assignment submission
        import os as _os
        _, ext = _os.path.splitext(getattr(file, 'name', '') or '')
        if not ext:
            ext = '.bin'
        
        # Get assignment and student objects
        if submitted_assignment:
            assignment = submitted_assignment.assignment
            student = submitted_assignment.student
        
        # Generate object name based on student name only
        if student:
            student_name = student.fullname.replace(' ', '_')
            object_name = f"submissions/{student_name}_{timezone.now().strftime('%Y%m%d_%H%M%S')}{ext}"
        else:
            # Fallback naming if we don't have the student object
            object_name = f"submissions/unknown_{timezone.now().strftime('%Y%m%d_%H%M%S')}{ext}"
        
        client.put_object(bucket, object_name, file.file, file.size, content_type=getattr(file, 'content_type', 'application/octet-stream'))
        return f"{base}{object_name}"

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

    def create(self, request, *args, **kwargs):
        # Handle file uploads for student submissions
        student_email = request.data.get('student')
        assignment_id = request.data.get('assignment')
        
        # Validate student and assignment
        if not student_email or not assignment_id:
            return Response({'error': 'student and assignment are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            student = Student.objects.get(email=student_email)
            assignment = Assignment.objects.get(id=assignment_id)
        except Student.DoesNotExist:
            return Response({'error': 'Student not found'}, status=status.HTTP_404_NOT_FOUND)
        except Assignment.DoesNotExist:
            return Response({'error': 'Assignment not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Verify student is in the correct class
        if student.class_id != assignment.class_id:
            return Response({'error': 'Student is not enrolled in this class'}, status=status.HTTP_403_FORBIDDEN)
        
        # Handle file upload
        if 'file' not in request.FILES:
            return Response({'error': 'file is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        file = request.FILES['file']
        
        # Upload file to MinIO
        url = self._upload_student_submission_to_minio(None, file, assignment, student)
        if url is None:
            return Response({'error': 'Failed to upload file to storage'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Check if submission already exists
        submitted_assignment, created = SubmittedAssignment.objects.get_or_create(
            assignment=assignment,
            student=student,
            defaults={
                'submission_file': url,
                'is_late': assignment.due_date and date.today() > assignment.due_date
            }
        )
        
        if not created:
            # Update existing submission
            # Delete previous file
            if submitted_assignment.submission_file:
                self._delete_minio_object_by_url(submitted_assignment.submission_file)
            
            # Update with new file
            submitted_assignment.submission_file = url
            submitted_assignment.is_late = assignment.due_date and date.today() > assignment.due_date
            submitted_assignment.save()
            
            # Update assignment status
            assignment.status = 'Submitted'
            assignment.save()
        
        serializer = self.get_serializer(submitted_assignment)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def grade(self, request, pk=None):
        """Grade a submitted assignment."""
        submitted_assignment = self.get_object()
        grade = request.data.get('grade')
        feedback = request.data.get('feedback', '')
        
        if grade is None:
            return Response({'error': 'grade is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            grade_decimal = Decimal(str(grade))
            submitted_assignment.grade = grade_decimal
            submitted_assignment.feedback = feedback
            submitted_assignment.save()
            
            return Response({
                'message': 'Assignment graded successfully',
                'grade': submitted_assignment.grade,
                'feedback': submitted_assignment.feedback
            })
        except Exception as e:
            return Response({'error': f'Invalid grade value: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)


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
    filterset_fields = ['status', 'owner', 'class_id', 'start_date', 'end_date']
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


# ------------------- PASSWORD RESET VIEWS -------------------
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
from .serializers import PasswordResetRequestSerializer, PasswordResetConfirmSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_request(request):
    """
    Request a password reset token.
    Sends an email with a reset link to the user's email address.
    """
    serializer = PasswordResetRequestSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
            
            # Generate token and uid
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Create reset link
            reset_link = f"https://school.globaltechsoftwaresolutions.cloud/api/reset_password/{uid}/{token}"
            
            # Send email
            subject = "Password Reset Request"
            message = render_to_string('password_reset_email.html', {
                'user': user,
                'reset_link': reset_link,
            })
            
            try:
                import smtplib
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                    html_message=message
                )
            except smtplib.SMTPAuthenticationError as e:
                return Response({
                    'error': 'SMTP Authentication Failed',
                    'detail': 'The server refused the email credentials.',
                    'debug_loaded_user': settings.EMAIL_HOST_USER,
                    'server_response': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            except Exception as e:
                return Response({
                    'error': 'Email Sending Failed',
                    'detail': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            return Response({
                'message': 'Password reset email sent successfully. Please check your inbox.'
            }, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            # For security reasons, we don't reveal if the email exists
            return Response({
                'message': 'Password reset email sent successfully. Please check your inbox.'
            }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_confirm(request, uidb64=None, token=None):
    """
    Confirm password reset with token.
    Allows user to set a new password.
    """
    # Validate input data
    serializer = PasswordResetConfirmSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # Decode uid and get user
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))  # pyright: ignore[reportArgumentType]
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return Response({
            'error': 'Invalid reset link'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Check token validity
    if not default_token_generator.check_token(user, token):
        return Response({
            'error': 'Invalid or expired reset link'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Set new password
    new_password = serializer.validated_data['new_password']
    user.set_password(new_password)
    user.save()
    
    return Response({
        'message': 'Password reset successful. You can now login with your new password.'
    }, status=status.HTTP_200_OK)


# ------------------- MARKS CARD VIEW -------------------
@api_view(['POST'])
@permission_classes([AllowAny])
def send_marks_card(request):
    """
    Generate and send marks card as PDF to student and parent via email
    """
    # Get student email from request body
    student_email = request.data.get('email')
    
    if not student_email:
        return Response({'error': 'Student email is required in the request body'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Get the student user
        user = User.objects.get(email=student_email, role='Student')
        student = user.student
    except User.DoesNotExist:
        return Response({'error': 'Student not found'}, status=status.HTTP_404_NOT_FOUND)
    except Student.DoesNotExist:
        return Response({'error': 'Student profile not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Initialize context with student data
    context = {
        'student_name': student.fullname,
        'roll_no': '',  # Will be populated if available
        'class_section': '',  # Will be populated if available
        'academic_year': timezone.now().astimezone(IST).strftime('%Y-%Y'),  # Default to current year
        'date_of_birth': student.date_of_birth.strftime('%d/%m/%Y') if student.date_of_birth else '',
        'admission_no': student.student_id or '',
    }
    
    # Add class information if available
    if student.class_id:
        context['class_section'] = f"{student.class_id.class_name} {student.class_id.sec}"
        # Update academic year based on current date
        current_year = timezone.now().astimezone(IST).year
        context['academic_year'] = f"{current_year}-{current_year + 1}"
    
    # Get student grades
    grades = Grade.objects.filter(student=student).select_related('subject')
    
    # Process grades for display
    subject_marks = []
    total_max_marks = 0
    total_marks_obtained = 0
    
    for grade in grades:
        max_marks = float(grade.total_marks) if grade.total_marks else 0
        marks_obtained = float(grade.marks_obtained) if grade.marks_obtained else 0
        
        # Calculate grade based on percentage with float precision
        percentage = (marks_obtained / max_marks) * 100 if max_marks > 0 else 0
        if percentage >= 90:
            grade_letter = 'A+'
        elif percentage >= 80:
            grade_letter = 'A'
        elif percentage >= 70:
            grade_letter = 'B+'
        elif percentage >= 60:
            grade_letter = 'B'
        elif percentage >= 50:
            grade_letter = 'C'
        else:
            grade_letter = 'F'
        
        # Determine pass/fail
        result = 'Pass' if percentage >= 35 else 'Fail'
        
        subject_marks.append({
            'subject': grade.subject.subject_name,
            'max_marks': f"{max_marks:.0f}",  # Show as integer
            'marks_obtained': f"{marks_obtained:.0f}",  # Show as integer
            'percentage': f"{percentage:.2f}%",  # Show percentage with 2 decimal places
            'grade': grade_letter,
            'result': result
        })
        
        total_max_marks += max_marks
        total_marks_obtained += marks_obtained
    
    context['subject_marks'] = subject_marks
    
    # Calculate overall result with float precision
    if total_max_marks > 0:
        overall_percentage = (total_marks_obtained / total_max_marks) * 100
        context['total_max_marks'] = f"{total_max_marks:.0f}"
        context['total_marks_obtained'] = f"{total_marks_obtained:.0f}"
        context['overall_percentage'] = f"{overall_percentage:.2f}%"
        context['overall_result'] = 'PASS' if overall_percentage >= 35 else 'FAIL'
    else:
        context['total_max_marks'] = "0"
        context['total_marks_obtained'] = "0"
        context['overall_percentage'] = "0.00%"
        context['overall_result'] = 'N/A'
    
    # Generate PDF using ReportLab
    try:
        from io import BytesIO
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
        
        # Create a buffer to store the PDF
        buffer = BytesIO()
        
        # Create PDF document with custom margins
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        elements = []
        
        # Define styles
        styles = getSampleStyleSheet()
        
        # Title style
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            spaceAfter=5,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#2C5AA0')
        )
        
        # Subtitle style
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#2C5AA0')
        )
        
        # School info style
        school_style = ParagraphStyle(
            'SchoolInfo',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=5,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#555555')
        )
        
        # Normal text style
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=5
        )
        
        # Add a frame/border around the entire content
        # Create a decorative frame at the beginning
        elements.append(Spacer(1, 5))
        
        # Header
        school_name = Paragraph("GREENWOOD PUBLIC SCHOOL", title_style)
        school_address = Paragraph("123, MG Road, Bengaluru - 560001 | Ph: (080) 2345 6789", school_style)
        exam_title = Paragraph("ANNUAL EXAMINATION MARKS CARD", subtitle_style)
        
        elements.append(school_name)
        elements.append(school_address)
        elements.append(exam_title)
        elements.append(Spacer(1, 20))
        
        # Student information table with completely new design
        student_data = [
            ['Student Name:', context['student_name'], 'Roll No:', context['roll_no'] or 'N/A'],
            ['Class & Section:', context['class_section'] or 'N/A', 'Academic Year:', context['academic_year']],
            ['Date of Birth:', context['date_of_birth'] or 'N/A', 'Admission No:', context['admission_no'] or 'N/A']
        ]
        
        student_table = Table(student_data, colWidths=[1.5*inch, 2*inch, 1.5*inch, 2*inch])
        student_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FFFFFF')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#333333')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#CCCCCC')),
            ('BOX', (0, 0), (-1, -1), 0.3, colors.HexColor('#CCCCCC')),
            ('INNERGRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#CCCCCC')),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F0F5FF')),
            ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#F0F5FF')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#2C5AA0')),
            ('TEXTCOLOR', (2, 0), (2, -1), colors.HexColor('#2C5AA0')),
        ]))
        
        elements.append(student_table)
        elements.append(Spacer(1, 20))
        
        # Marks table header
        marks_header = Paragraph("Academic Performance", subtitle_style)
        marks_header.style.alignment = TA_LEFT
        marks_header.style.fontSize = 13
        marks_header.style.textColor = colors.HexColor('#2C5AA0')
        elements.append(marks_header)
        
        # Marks table with completely new styling
        # Header row
        marks_data = [
            ['Subject', 'Max Marks', 'Marks Obtained', 'Percentage', 'Grade', 'Result']
        ]
        
        # Add subject rows
        for subject in context['subject_marks']:
            marks_data.append([
                subject['subject'],
                subject['max_marks'],
                subject['marks_obtained'],
                subject['percentage'],
                subject['grade'],
                subject['result']
            ])
        
        # Add total row
        marks_data.append([
            'Total',
            context['total_max_marks'],
            context['total_marks_obtained'],
            context['overall_percentage'],
            '',
            context['overall_result']
        ])
        
        marks_table = Table(marks_data, colWidths=[2*inch, 1*inch, 1*inch, 1*inch, 0.7*inch, 0.8*inch])
        marks_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C5AA0')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#FFFFFF')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#FFFFFF')),
            ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#CCCCCC')),
            ('BOX', (0, 0), (-1, -1), 0.3, colors.HexColor('#CCCCCC')),
            ('INNERGRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#CCCCCC')),
            ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
            ('FONTNAME', (-1, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTNAME', (0, -1), (0, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#F0F5FF')),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#2C5AA0')),
        ]))
        
        elements.append(marks_table)
        elements.append(Spacer(1, 25))
        
        # Performance summary with new styling
        summary_text = f"Overall Percentage: {context['overall_percentage']}"
        summary_para = Paragraph(summary_text, normal_style)
        summary_para.style.textColor = colors.HexColor('#2C5AA0')
        summary_para.style.fontSize = 11
        elements.append(summary_para)
        elements.append(Spacer(1, 10))
        
        # Footer with signatures and new borders
        footer_data = [
            ['Class Teacher', 'Principal'],
            ['', '']
        ]
        
        footer_table = Table(footer_data, colWidths=[3*inch, 3*inch])
        footer_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, 0), 0.3, colors.HexColor('#CCCCCC')),
            ('BOX', (0, 0), (-1, 0), 0.3, colors.HexColor('#CCCCCC')),
            ('LINEBELOW', (0, 0), (-1, 0), 0.3, colors.HexColor('#CCCCCC')),
            ('LINEAFTER', (0, 0), (0, 0), 0.3, colors.HexColor('#CCCCCC')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#666666')),
        ]))
        
        elements.append(footer_table)
        elements.append(Spacer(1, 20))
        
        # Final result display with new styling
        result_color = '#32A852' if context['overall_result'] == 'PASS' else '#C70039'
        result_text = f"Final Result: <font color='{result_color}'><b>{context['overall_result']}</b></font>"
        result_para = Paragraph(result_text, subtitle_style)
        result_para.style.alignment = TA_CENTER
        result_para.style.fontSize = 16
        result_para.style.textColor = colors.HexColor('#2C5AA0')
        elements.append(result_para)
        
        # Build PDF
        doc.build(elements)
        
        # Get PDF content
        pdf_content = buffer.getvalue()
        buffer.close()
        
    except Exception as e:
        return Response({'error': f'Failed to generate PDF: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Send email to student with PDF attachment
    student_subject = f"Marks Card for {student.fullname}"
    
    # Send email to parent if parent exists
    parent_emails = []
    if student.parent:
        parent_emails.append(student.parent.email.email)
        
        parent_subject = f"Marks Card for your child {student.fullname}"
        
        try:
            from django.core.mail import EmailMessage
            # Send email to parent with PDF attachment
            email = EmailMessage(
                parent_subject,
                'Please find attached the marks card for your child.',
                settings.DEFAULT_FROM_EMAIL,
                parent_emails,
            )
            email.attach(f'marks_card_{student.fullname}.pdf', pdf_content, 'application/pdf')
            email.send()
        except Exception as e:
            return Response({'error': f'Failed to send email to parent: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Send email to student with PDF attachment
    try:
        from django.core.mail import EmailMessage
        email = EmailMessage(
            student_subject,
            'Please find attached your marks card.',
            settings.DEFAULT_FROM_EMAIL,
            [student_email],
        )
        email.attach(f'marks_card_{student.fullname}.pdf', pdf_content, 'application/pdf')
        email.send()
    except Exception as e:
        return Response({'error': f'Failed to send email to student: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response({
        'message': 'Marks card PDF sent successfully to student and parent',
        'student_email': student_email,
        'parent_emails': parent_emails
    }, status=status.HTTP_200_OK)

