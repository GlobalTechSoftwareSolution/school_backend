from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView
from .token_serializers import CustomTokenObtainPairView

urlpatterns = [
    # Authentication
    path('signup/', views.register_user, name='signup'),
    path('token/', CustomTokenObtainPairView.as_view(), name='token'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('check_token/', views.current_user, name='current-user'),
    path('login/', views.login_with_credentials, name='login'),
    
    # ID Card
    path('', views.id_card_view, name='id-card'),
    path('test-id-card/', views.test_id_card_view, name='test-id-card'),
    
    # User Management
    path('users/', views.UserViewSet.as_view({'get': 'list', 'post': 'create'}), name='user-list'),
    path('users/<str:pk>/', views.UserViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'}), name='user-detail'),
    path('users/<str:pk>/approve/', views.UserViewSet.as_view({'post': 'approve'}), name='user-approve'),
    path('users/<str:pk>/reject/', views.UserViewSet.as_view({'post': 'deactivate'}), name='user-deactivate'),
    
    # Departments
    path('departments/', views.DepartmentViewSet.as_view({'get': 'list', 'post': 'create'}), name='department-list'),
    path('departments/<int:pk>/', views.DepartmentViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'}), name='department-detail'),
    
    # Subjects
    path('subjects/', views.SubjectViewSet.as_view({'get': 'list', 'post': 'create'}), name='subject-list'),
    path('subjects/<int:pk>/', views.SubjectViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'}), name='subject-detail'),
    
    # Classes
    path('classes/', views.ClassViewSet.as_view({'get': 'list', 'post': 'create'}), name='class-list'),
    path('classes/<int:pk>/', views.ClassViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'}), name='class-detail'),
    
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
    path('attendance/mark/', views.AttendanceViewSet.as_view({'post': 'mark'}), name='attendance-mark'),
    path('attendance/get_users_for_marking/', views.AttendanceViewSet.as_view({'post': 'get_users_for_marking'}), name='attendance-get-users'),
    path('mark_students_attendance/', views.AttendanceViewSet.as_view({'post': 'bulk_update_status'}), name='attendance-bulk-update'),
    path('school_attendance/', views.school_attendance_view, name='school-attendance-view'),
    
    # Student Attendance
    path('student_attendance/', views.StudentAttendanceViewSet.as_view({'get': 'list', 'post': 'create'}), name='student-attendance-list'),
    path('student_attendance/<int:pk>/', views.StudentAttendanceViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'}), name='student-attendance-detail'),
    path('student_attendance/by_student/', views.StudentAttendanceViewSet.as_view({'get': 'by_student'}), name='student-attendance-by-student'),
    path('student_attendance/by_class/', views.StudentAttendanceViewSet.as_view({'get': 'by_class'}), name='student-attendance-by-class'),
    path('student_attendance/by_subject/', views.StudentAttendanceViewSet.as_view({'get': 'by_subject'}), name='student-attendance-by-subject'),
    path('student_attendance/bulk_create/', views.StudentAttendanceViewSet.as_view({'post': 'bulk_create'}), name='student-attendance-bulk-create'),

    # Grades
    path('grades/', views.GradeViewSet.as_view({'get': 'list', 'post': 'create'}), name='grade-list'),
    path('grades/<int:pk>/', views.GradeViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'}), name='grade-detail'),
    
    # Fee Structures
    path('fee_structures/', views.FeeStructureViewSet.as_view({'get': 'list', 'post': 'create'}), name='fee-structure-list'),
    path('fee_structures/<int:pk>/', views.FeeStructureViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'}), name='fee-structure-detail'),
    
    # Fee Payments
    path('fee_payments/', views.FeePaymentViewSet.as_view({'get': 'list', 'post': 'create'}), name='fee-payment-list'),
    path('fee_payments/<int:pk>/', views.FeePaymentViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'}), name='fee-payment-detail'),
    
    # Timetable
    path('timetable/', views.TimetableViewSet.as_view({'get': 'list', 'post': 'create'}), name='timetable-list'),
    path('timetable/<int:pk>/', views.TimetableViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'}), name='timetable-detail'),
    
    # Former Members (Read-only)
    path('former_members/', views.FormerMemberViewSet.as_view({'get': 'list'}), name='former-member-list'),
    path('former_members/<str:pk>/', views.FormerMemberViewSet.as_view({'get': 'retrieve'}), name='former-member-detail'),

    # Documents
    path('documents/', views.DocumentViewSet.as_view({'get': 'list', 'post': 'create'}), name='document-list'),
    path('documents/bulk_upsert/', views.DocumentViewSet.as_view({'post': 'bulk_upsert'}), name='document-bulk-upsert'),
    path('documents/upload/', views.DocumentViewSet.as_view({'post': 'upload'}), name='document-upload'),
    path('documents/<str:email>/', views.DocumentViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'}), name='document-detail'),

    # Notices
    path('notices/', views.NoticeViewSet.as_view({'get': 'list', 'post': 'create'}), name='notice-list'),
    path('notices/bulk_create/', views.NoticeViewSet.as_view({'post': 'bulk_create'}), name='notice-bulk-create'),
    path('notices/<int:pk>/', views.NoticeViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'}), name='notice-detail'),

    # Issues
    path('issues/', views.IssueViewSet.as_view({'get': 'list', 'post': 'create'}), name='issue-list'),
    path('issues/bulk_create/', views.IssueViewSet.as_view({'post': 'bulk_create'}), name='issue-bulk-create'),
    path('issues/<int:pk>/', views.IssueViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'}), name='issue-detail'),

    # Holidays
    path('holidays/', views.HolidayViewSet.as_view({'get': 'list', 'post': 'create'}), name='holiday-list'),
    path('holidays/bulk_upsert/', views.HolidayViewSet.as_view({'post': 'bulk_upsert'}), name='holiday-bulk-upsert'),
    path('holidays/<int:pk>/', views.HolidayViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'}), name='holiday-detail'),

    # Awards
    path('awards/', views.AwardViewSet.as_view({'get': 'list', 'post': 'create'}), name='award-list'),
    path('awards/bulk_upsert/', views.AwardViewSet.as_view({'post': 'bulk_upsert'}), name='award-bulk-upsert'),
    path('awards/<int:pk>/', views.AwardViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'}), name='award-detail'),

    # Assignments
    path('assignments/', views.AssignmentViewSet.as_view({'get': 'list', 'post': 'create'}), name='assignment-list'),
    path('assignments/<int:pk>/', views.AssignmentViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'}), name='assignment-detail'),
    path('assignments/<int:pk>/submit/', views.AssignmentViewSet.as_view({'post': 'submit'}), name='assignment-submit'),

    # Leaves
    path('leaves/', views.LeaveViewSet.as_view({'get': 'list', 'post': 'create'}), name='leave-list'),
    path('leaves/<int:pk>/', views.LeaveViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'}), name='leave-detail'),
    path('leaves/<int:pk>/approve/', views.LeaveViewSet.as_view({'post': 'approve'}), name='leave-approve'),
    path('leaves/<int:pk>/reject/', views.LeaveViewSet.as_view({'post': 'reject'}), name='leave-reject'),

    # Tasks
    path('tasks/', views.TaskViewSet.as_view({'get': 'list', 'post': 'create'}), name='task-list'),
    path('tasks/<int:pk>/', views.TaskViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'}), name='task-detail'),
    path('tasks/<int:pk>/mark_done/', views.TaskViewSet.as_view({'post': 'mark_done'}), name='task-mark-done'),

    # Projects
    path('projects/', views.ProjectViewSet.as_view({'get': 'list', 'post': 'create'}), name='project-list'),
    path('projects/<int:pk>/', views.ProjectViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'}), name='project-detail'),

    # Programs
    path('programs/', views.ProgramViewSet.as_view({'get': 'list', 'post': 'create'}), name='program-list'),
    path('programs/<int:pk>/', views.ProgramViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'}), name='program-detail'),

    # Activities
    path('activities/', views.ActivityViewSet.as_view({'get': 'list', 'post': 'create'}), name='activity-list'),
    path('activities/<int:pk>/', views.ActivityViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'}), name='activity-detail'),

    # Reports
    path('reports/', views.ReportViewSet.as_view({'get': 'list', 'post': 'create'}), name='report-list'),
    path('reports/<int:pk>/', views.ReportViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'}), name='report-detail'),

    # Finance Transactions
    path('finance/', views.FinanceTransactionViewSet.as_view({'get': 'list', 'post': 'create'}), name='finance-transaction-list'),
    path('finance/<int:pk>/', views.FinanceTransactionViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'}), name='finance-transaction-detail'),

    # Transport Details
    path('transport_details/', views.TransportDetailsViewSet.as_view({'get': 'list', 'post': 'create'}), name='transport-details-list'),
    path('transport_details/<int:pk>/', views.TransportDetailsViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'}), name='transport-details-detail'),

    # Submitted Assignments
    path('submitted_assignments/', views.SubmittedAssignmentViewSet.as_view({'get': 'list', 'post': 'create'}), name='submitted-assignment-list'),
    path('submitted_assignments/<int:pk>/', views.SubmittedAssignmentViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'}), name='submitted-assignment-detail'),
    path('submitted_assignments/<int:pk>/grade/', views.SubmittedAssignmentViewSet.as_view({'post': 'grade'}), name='submitted-assignment-grade'),
    
    # ID Cards
    path('id_cards/', views.IDCardViewSet.as_view({'get': 'list', 'post': 'create'}), name='id-card-list'),
    path('id_cards/<int:pk>/', views.IDCardViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'}), name='id-card-detail'),
    path('id_cards/check_by_email/', views.IDCardViewSet.as_view({'get': 'check_by_email'}), name='id-card-check-by-email'),
    path('id_cards/generate/', views.IDCardViewSet.as_view({'post': 'generate_id_card'}), name='id-card-generate'),
]
