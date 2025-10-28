from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router and register viewsets
router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'departments', views.DepartmentViewSet, basename='department')
router.register(r'classes', views.ClassViewSet, basename='class')
router.register(r'subjects', views.SubjectViewSet, basename='subject')
router.register(r'students', views.StudentViewSet, basename='student')
router.register(r'teachers', views.TeacherViewSet, basename='teacher')
router.register(r'principals', views.PrincipalViewSet, basename='principal')
router.register(r'management', views.ManagementViewSet, basename='management')
router.register(r'admins', views.AdminViewSet, basename='admin')
router.register(r'parents', views.ParentViewSet, basename='parent')
router.register(r'attendance', views.AttendanceViewSet, basename='attendance')
router.register(r'grades', views.GradeViewSet, basename='grade')
router.register(r'fee-structures', views.FeeStructureViewSet, basename='fee-structure')
router.register(r'fee-payments', views.FeePaymentViewSet, basename='fee-payment')
router.register(r'timetable', views.TimetableViewSet, basename='timetable')
router.register(r'former-members', views.FormerMemberViewSet, basename='former-member')

urlpatterns = [
    # Authentication endpoints
    path('auth/register/', views.register_user, name='register'),
    path('auth/me/', views.current_user, name='current-user'),
    
    # All viewset routes
    path('', include(router.urls)),
]
