from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model

from .models import (
    User, Student, Teacher, Principal, Management, Admin, Parent,
    Department, Class, Subject, Attendance, Grade, FeeStructure,
    FeePayment, Timetable, FormerMember
)
from .serializers import (
    UserSerializer, UserRegistrationSerializer,
    StudentSerializer, StudentCreateSerializer,
    TeacherSerializer, TeacherCreateSerializer,
    PrincipalSerializer, ManagementSerializer, AdminSerializer, ParentSerializer,
    DepartmentSerializer, ClassSerializer, SubjectSerializer,
    AttendanceSerializer, AttendanceCreateSerializer,
    GradeSerializer, GradeCreateSerializer,
    FeeStructureSerializer, FeePaymentSerializer, FeePaymentCreateSerializer,
    TimetableSerializer, TimetableCreateSerializer, FormerMemberSerializer
)


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


# ------------------- CLASS VIEWSET -------------------
class ClassViewSet(viewsets.ModelViewSet):
    queryset = Class.objects.all()
    serializer_class = ClassSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['class_name', 'section']
    ordering_fields = ['class_name', 'created_at']


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
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]  # type: ignore[assignment]
    filterset_fields = ['class_enrolled', 'gender', 'blood_group']
    search_fields = ['fullname', 'student_id', 'email__email']
    ordering_fields = ['fullname', 'admission_date']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return StudentCreateSerializer
        return StudentSerializer

    @action(detail=False, methods=['get'])
    def by_class(self, request):
        """Get students by class"""
        class_id = request.query_params.get('class_id')
        if class_id:
            students = self.queryset.filter(class_enrolled_id=class_id)  # type: ignore[union-attr]
            serializer = self.get_serializer(students, many=True)
            return Response(serializer.data)
        return Response({'error': 'class_id parameter required'}, status=status.HTTP_400_BAD_REQUEST)


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
            teachers = self.queryset.filter(department_id=dept_id)  # type: ignore[union-attr]
            serializer = self.get_serializer(teachers, many=True)
            return Response(serializer.data)
        return Response({'error': 'department_id parameter required'}, status=status.HTTP_400_BAD_REQUEST)


# ------------------- PRINCIPAL VIEWSET -------------------
class PrincipalViewSet(viewsets.ModelViewSet):
    queryset = Principal.objects.all()
    serializer_class = PrincipalSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ['fullname', 'email__email']


# ------------------- MANAGEMENT VIEWSET -------------------
class ManagementViewSet(viewsets.ModelViewSet):
    queryset = Management.objects.all()
    serializer_class = ManagementSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]  # type: ignore[assignment]
    filterset_fields = ['department', 'designation']
    search_fields = ['fullname', 'designation', 'email__email']


# ------------------- ADMIN VIEWSET -------------------
class AdminViewSet(viewsets.ModelViewSet):
    queryset = Admin.objects.all()
    serializer_class = AdminSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ['fullname', 'email__email']


# ------------------- PARENT VIEWSET -------------------
class ParentViewSet(viewsets.ModelViewSet):
    queryset = Parent.objects.all()
    serializer_class = ParentSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ['fullname', 'email__email', 'occupation']


# ------------------- ATTENDANCE VIEWSET -------------------
class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.all()
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]  # type: ignore[assignment]
    filterset_fields = ['student', 'class_enrolled', 'status', 'date']
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
            attendance = self.queryset.filter(date__range=[start_date, end_date])  # type: ignore[union-attr]
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
            grades = self.queryset.filter(student__email=student_email)  # type: ignore[union-attr]
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
            fees = self.queryset.filter(class_level_id=class_id)  # type: ignore[union-attr]
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
            payments = self.queryset.filter(student__email=student_email)  # type: ignore[union-attr]
            serializer = self.get_serializer(payments, many=True)
            return Response(serializer.data)
        return Response({'error': 'student_email parameter required'}, status=status.HTTP_400_BAD_REQUEST)


# ------------------- TIMETABLE VIEWSET -------------------
class TimetableViewSet(viewsets.ModelViewSet):
    queryset = Timetable.objects.all()
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]  # type: ignore[assignment]
    filterset_fields = ['class_enrolled', 'subject', 'teacher', 'day_of_week']
    search_fields = ['class_enrolled__class_name', 'subject__subject_name', 'teacher__fullname']
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
            timetable = self.queryset.filter(class_enrolled_id=class_id)  # type: ignore[union-attr]
            serializer = self.get_serializer(timetable, many=True)
            return Response(serializer.data)
        return Response({'error': 'class_id parameter required'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def by_teacher(self, request):
        """Get timetable by teacher"""
        teacher_email = request.query_params.get('teacher_email')
        if teacher_email:
            timetable = self.queryset.filter(teacher__email=teacher_email)  # type: ignore[union-attr]
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
            members = self.queryset.filter(role=role)  # type: ignore[union-attr]
            serializer = self.get_serializer(members, many=True)
            return Response(serializer.data)
        return Response({'error': 'role parameter required'}, status=status.HTTP_400_BAD_REQUEST)
