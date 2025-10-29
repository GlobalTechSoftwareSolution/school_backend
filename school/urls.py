from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView
from .token_serializers import CustomTokenObtainPairView

urlpatterns = [
    # Authentication
    path('signup/', views.register_user, name='signup'),
    path('token/', CustomTokenObtainPairView.as_view(), name='token'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('current-user/', views.current_user, name='current-user'),
    path('login/', views.login_with_credentials, name='login'),
    
    # User Management
    path('users/', views.UserViewSet.as_view({'get': 'list', 'post': 'create'}), name='user-list'),
    path('users/<str:pk>/', views.UserViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'}), name='user-detail'),
    path('users/<str:pk>/approve/', views.UserViewSet.as_view({'post': 'approve'}), name='user-approve'),
    path('users/<str:pk>/deactivate/', views.UserViewSet.as_view({'post': 'deactivate'}), name='user-deactivate'),
    
    # Departments
    path('departments/', views.DepartmentViewSet.as_view({'get': 'list', 'post': 'create'}), name='department-list'),
    path('departments/<int:pk>/', views.DepartmentViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'}), name='department-detail'),
    
    # Classes
    path('classes/', views.ClassViewSet.as_view({'get': 'list', 'post': 'create'}), name='class-list'),
    path('classes/<int:pk>/', views.ClassViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'}), name='class-detail'),
    
    # Subjects
    path('subjects/', views.SubjectViewSet.as_view({'get': 'list', 'post': 'create'}), name='subject-list'),
    path('subjects/<int:pk>/', views.SubjectViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'}), name='subject-detail'),
    
    # Students
    path('students/', views.StudentViewSet.as_view({'get': 'list', 'post': 'create'}), name='student-list'),
    path('students/<str:pk>/', views.StudentViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'}), name='student-detail'),
    path('students/by_class/', views.StudentViewSet.as_view({'get': 'by_class'}), name='student-by-class'),
    
    # Teachers
    path('teachers/', views.TeacherViewSet.as_view({'get': 'list', 'post': 'create'}), name='teacher-list'),
    path('teachers/<str:pk>/', views.TeacherViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'}), name='teacher-detail'),
    path('teachers/by_department/', views.TeacherViewSet.as_view({'get': 'by_department'}), name='teacher-by-department'),
    
    # Principals
    path('principals/', views.PrincipalViewSet.as_view({'get': 'list', 'post': 'create'}), name='principal-list'),
    path('principals/<str:pk>/', views.PrincipalViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'}), name='principal-detail'),
    
    # Management
    path('management/', views.ManagementViewSet.as_view({'get': 'list', 'post': 'create'}), name='management-list'),
    path('management/<str:pk>/', views.ManagementViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'}), name='management-detail'),
    
    # Admins
    path('admins/', views.AdminViewSet.as_view({'get': 'list', 'post': 'create'}), name='admin-list'),
    path('admins/<str:pk>/', views.AdminViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'}), name='admin-detail'),
    
    # Parents
    path('parents/', views.ParentViewSet.as_view({'get': 'list', 'post': 'create'}), name='parent-list'),
    path('parents/<str:pk>/', views.ParentViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'}), name='parent-detail'),
    
    # Attendance
    path('attendance/', views.AttendanceViewSet.as_view({'get': 'list', 'post': 'create'}), name='attendance-list'),
    path('attendance/<int:pk>/', views.AttendanceViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'}), name='attendance-detail'),
    
    # Grades
    path('grades/', views.GradeViewSet.as_view({'get': 'list', 'post': 'create'}), name='grade-list'),
    path('grades/<int:pk>/', views.GradeViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'}), name='grade-detail'),
    
    # Fee Structures
    path('fee-structures/', views.FeeStructureViewSet.as_view({'get': 'list', 'post': 'create'}), name='fee-structure-list'),
    path('fee-structures/<int:pk>/', views.FeeStructureViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'}), name='fee-structure-detail'),
    
    # Fee Payments
    path('fee-payments/', views.FeePaymentViewSet.as_view({'get': 'list', 'post': 'create'}), name='fee-payment-list'),
    path('fee-payments/<int:pk>/', views.FeePaymentViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'}), name='fee-payment-detail'),
    
    # Timetable
    path('timetable/', views.TimetableViewSet.as_view({'get': 'list', 'post': 'create'}), name='timetable-list'),
    path('timetable/<int:pk>/', views.TimetableViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'}), name='timetable-detail'),
    
    # Former Members (Read-only)
    path('former-members/', views.FormerMemberViewSet.as_view({'get': 'list'}), name='former-member-list'),
    path('former-members/<str:pk>/', views.FormerMemberViewSet.as_view({'get': 'retrieve'}), name='former-member-detail'),
]
