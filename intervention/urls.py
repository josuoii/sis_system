# intervention/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import reports_pdf_view, MBTIWizard
from .forms import MBTIEIForm, MBTISNForm, MBTITFForm, MBTIJPForm

app_name = 'intervention'

urlpatterns = [
    # Landing page for non-authenticated users
    path('', views.LandingPageView.as_view(), name='home'),
    
    # Dashboard URLs - Role-based routing
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('admin-dashboard/', views.DashboardView.as_view(), name='admin-dashboard'),
    
    # Authentication URLs - Custom login/logout with role-based redirection
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    
    # Password Reset URLs
    path('password-reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html',
        success_url='/reset/done/'
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html'
    ), name='password_reset_complete'),
    
    # Password Change URLs
    path('password-change/', auth_views.PasswordChangeView.as_view(
        template_name='registration/password_change.html',
        success_url='/password-change/done/'
    ), name='password_change'),
    path('password-change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='registration/password_change_done.html'
    ), name='password_change_done'),
    
    # Profile Management
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/update/', views.UpdateProfileView.as_view(), name='profile-update'),
    path('setup-wizard/', views.SetupWizardView.as_view(), name='setup-wizard'),
    
    # User Management (Admin only)
    path('users/', views.UserManagementView.as_view(), name='user-management'),
    path('users/create/', views.CreateUserView.as_view(), name='create-user'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user-detail'),
    
    # Intervention URLs
    path('interventions/', views.InterventionListView.as_view(), name='intervention-list'),
    path('interventions/<int:pk>/', views.InterventionDetailView.as_view(), name='intervention-detail'),
    path('interventions/create/', views.CreateInterventionView.as_view(), name='intervention-create'),
    path('interventions/create/<int:student_id>/', views.CreateInterventionView.as_view(), name='intervention-create-for-student'),
    path('interventions/<int:pk>/edit/', views.UpdateInterventionView.as_view(), name='intervention-update'),
    path('interventions/<int:pk>/delete/', views.DeleteInterventionView.as_view(), name='intervention-delete'),
    path('interventions/<int:pk>/stats/', views.InterventionStatsView.as_view(), name='intervention-stats'),
    
    # Document URLs
    path('interventions/<int:intervention_id>/upload-document/', views.DocumentUploadView.as_view(), name='document-upload'),
    path('documents/<int:pk>/delete/', views.DocumentDeleteView.as_view(), name='document-delete'),
    
    # Progress URLs
    path('interventions/<int:intervention_id>/progress/', views.ProgressUpdateView.as_view(), name='progress-update'),
    path('interventions/<int:pk>/progress-history/', views.ProgressHistoryView.as_view(), name='progress-history'),
    
    # Goal Management
    path('goals/', views.GoalListView.as_view(), name='goal-list'),
    path('goals/<int:pk>/', views.GoalDetailView.as_view(), name='goal-detail'),
    path('goals/create/', views.CreateGoalView.as_view(), name='goal-create'),
    path('goals/create/<int:student_id>/', views.CreateGoalView.as_view(), name='goal-create-for-student'),
    
    # Meeting Management
    path('meetings/', views.MeetingListView.as_view(), name='meeting-list'),
    path('meetings/create/', views.CreateMeetingView.as_view(), name='meeting-create'),
    
    # Message System
    path('messages/send/', views.SendMessageView.as_view(), name='send-message'),
    path('messages/<int:pk>/read/', views.MarkMessageReadView.as_view(), name='mark-message-read'),
    
    # Notifications
    path('notifications/', views.NotificationListView.as_view(), name='notification-list'),
    path('notifications/<int:pk>/read/', views.MarkNotificationReadView.as_view(), name='mark-notification-read'),
    
    # Search
    path('search/', views.SearchView.as_view(), name='search'),
    
    # Reports
    path('reports/', views.reports_view, name='reports'),
    path('interventions/<int:pk>/pdf/', views.GenerateInterventionPDF.as_view(), name='intervention-pdf'),
    path('reports/pdf/', reports_pdf_view, name='reports_pdf'),

    path('users/<int:pk>/edit/', views.UserUpdateView.as_view(), name='user-edit'),
    path('users/<int:pk>/activate/', views.activate_user, name='user-activate'),
    path('users/<int:pk>/deactivate/', views.deactivate_user, name='user-deactivate'),
    path('users/<int:pk>/delete/', views.UserDeleteView.as_view(), name='user-delete'),
    path('profile/<int:pk>/', views.ProfileView.as_view(), name='user-profile'),

    # Goal Management URLs (add these to your existing urlpatterns)
    path('goals/', views.GoalListView.as_view(), name='goal-list'),
    path('goals/<int:pk>/', views.GoalDetailView.as_view(), name='goal-detail'),
    path('goals/create/', views.CreateGoalView.as_view(), name='goal-create'),
    path('goals/create/<int:student_id>/', views.CreateGoalView.as_view(), name='goal-create-for-student'),
    path('goals/<int:pk>/edit/', views.UpdateGoalView.as_view(), name='goal-update'),
    path('goals/<int:pk>/delete/', views.DeleteGoalView.as_view(), name='goal-delete'),

    # Milestone management
    path('goals/<int:goal_id>/milestones/create/', views.CreateMilestoneView.as_view(), name='milestone-create'),
    path('milestones/<int:pk>/edit/', views.UpdateMilestoneView.as_view(), name='milestone-update'),
    path('milestones/<int:pk>/delete/', views.DeleteMilestoneView.as_view(), name='milestone-delete'),

    # Add these URL patterns to your urls.py file in the urlpatterns list:

    # Class Management URLs
    path('classes/', views.ClassListView.as_view(), name='class-list'),
    path('classes/<int:pk>/', views.ClassDetailView.as_view(), name='class-detail'),
    path('classes/create/', views.CreateClassView.as_view(), name='class-create'),
    path('classes/<int:pk>/edit/', views.UpdateClassView.as_view(), name='class-update'),
    path('classes/<int:pk>/delete/', views.DeleteClassView.as_view(), name='class-delete'),
    path('classes/<int:class_id>/assign-students/', views.assign_students, name='assign-students'),


    # Attendance Management URLs
    path('attendance/', views.AttendanceListView.as_view(), name='attendance-list'),
    path('attendance/create/', views.CreateAttendanceView.as_view(), name='attendance-create'),
    path('attendance/<int:pk>/edit/', views.UpdateAttendanceView.as_view(), name='attendance-update'),
    path('attendance/<int:pk>/delete/', views.DeleteAttendanceView.as_view(), name='attendance-delete'),

    # Academic Records URLs
    path('academic-records/', views.AcademicRecordListView.as_view(), name='academic-record-list'),
    path('academic-records/create/', views.CreateAcademicRecordView.as_view(), name='academic-record-create'),
    path('academic-records/<int:pk>/edit/', views.UpdateAcademicRecordView.as_view(), name='academic-record-update'),
    path('academic-records/<int:pk>/delete/', views.DeleteAcademicRecordView.as_view(), name='academic-record-delete'),

    # Class Management URLs
    path('classes/', views.ClassListView.as_view(), name='class-list'),
    path('classes/<int:pk>/', views.ClassDetailView.as_view(), name='class-detail'),
    path('classes/create/', views.CreateClassView.as_view(), name='class-create'),
    path('classes/<int:pk>/edit/', views.UpdateClassView.as_view(), name='class-update'),
    path('classes/<int:pk>/delete/', views.DeleteClassView.as_view(), name='class-delete'),
    path('classes/<int:class_id>/assign-students/', views.assign_students, name='assign-students'),

    # Student Management URLs
    path('students/', views.StudentListView.as_view(), name='student-list'),
    path('students/<int:pk>/', views.StudentDetailView.as_view(), name='student-detail'),
    # Student Management URLs

    path('students/', views.StudentListView.as_view(), name='student-list'),
    path('students/create/', views.StudentCreateView.as_view(), name='student-create'),
    path('students/<int:pk>/', views.StudentDetailView.as_view(), name='student-detail'),
    path('students/<int:pk>/edit/', views.StudentUpdateView.as_view(), name='student-update'),
    path('students/<int:pk>/delete/', views.StudentDeleteView.as_view(), name='student-delete'),

    

    # Meeting URLs
    path('meetings/', views.MeetingListView.as_view(), name='meeting-list'),
    path('meetings/create/', views.CreateMeetingView.as_view(), name='meeting-create'),
    path('meetings/<int:pk>/', views.MeetingDetailView.as_view(), name='meeting-detail'),
    path('meetings/<int:pk>/edit/', views.UpdateMeetingView.as_view(), name='meeting-update'),
    path('meetings/<int:pk>/delete/', views.DeleteMeetingView.as_view(), name='meeting-delete'),
    path('meetings/<int:pk>/toggle-status/', views.ToggleMeetingStatusView.as_view(), name='meeting-toggle-status'),

    # Message URLs
    path('messages/', views.MessageListView.as_view(), name='message-list'),
    path('messages/send/', views.SendMessageView.as_view(), name='send-message'),

    # Parent-child link request URLs
    path('parent/link-request/', views.ParentChildLinkRequestView.as_view(), name='parent-link-request'),
    path('parent/link-requests/', views.ParentChildLinkRequestListView.as_view(), name='parent-link-request-list'),

    # Student search API for parent link request
    path('api/student-search/', views.StudentSearchAPIView.as_view(), name='student-search-api'),

    # Admin parent-child link request review
    path('admin/link-requests/', views.AdminParentChildLinkRequestListView.as_view(), name='admin-link-request-list'),
    path('admin/link-requests/<int:pk>/action/', views.AdminParentChildLinkRequestActionView.as_view(), name='admin-link-request-action'),

    # Chat URLs
    path('chat/', views.ChatThreadListView.as_view(), name='chat-thread-list'),
    path('chat/start/', views.StartChatView.as_view(), name='start-chat'),
    path('chat/<int:pk>/', views.ChatThreadDetailView.as_view(), name='chat-thread-detail'),

    path('session-interrupted/', views.session_interrupted_view, name='session_interrupted'),

    path('mbti/quiz/', MBTIWizard.as_view([
        ("ei", MBTIEIForm),
        ("sn", MBTISNForm),
        ("tf", MBTITFForm),
        ("jp", MBTIJPForm),
    ]), name='mbti_quiz'),
    path('learning-style/', MBTIWizard.as_view([
        ("ei", MBTIEIForm),
        ("sn", MBTISNForm),
        ("tf", MBTITFForm),
        ("jp", MBTIJPForm),
    ]), name='learning-style'),
]