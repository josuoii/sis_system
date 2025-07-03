# Complete views.py with authentication views integrated

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView, LogoutView, PasswordResetView as BasePasswordResetView
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, View, FormView
)
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.http import HttpResponse, JsonResponse, Http404, FileResponse, HttpResponseForbidden
from django.db.models import Avg, Q, Count, Prefetch, F, Sum
from django.utils import timezone
from datetime import timedelta
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet
import pandas as pd
from io import BytesIO
import logging
import os
from .models import *
from .forms import *
from datetime import timedelta
from .models import Class  # Add this if missing
from .forms import ClassForm, AssignStudentsForm  # Add these if missing
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.template.loader import get_template
from formtools.wizard.views import SessionWizardView
from .forms import MBTIEIForm, MBTISNForm, MBTITFForm, MBTIJPForm
from .models import MBTIQuestion, MBTIAnswer
from django.shortcuts import render, redirect

logger = logging.getLogger(__name__)

# ====================== AUTHENTICATION VIEWS ======================

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        """Redirect users based on their role after successful login"""
        try:
            profile = self.request.user.userprofile
            
            # Create audit log for successful login
            create_audit_log(
                user=self.request.user,
                action="User logged in",
                details=f"Login from {self.get_client_ip()}",
                action_type="LOGIN",
                ip_address=self.get_client_ip()
            )
            
            # Redirect based on user type
            if profile.user_type == 'ADMIN':
                messages.success(self.request, f"Welcome back, Administrator {self.request.user.get_full_name()}!")
                return reverse('intervention:admin-dashboard')
            elif profile.user_type == 'TEACHER':
                messages.success(self.request, f"Welcome back, {self.request.user.get_full_name()}!")
                return reverse('intervention:dashboard')
            elif profile.user_type == 'STUDENT':
                messages.success(self.request, f"Welcome, {self.request.user.get_full_name()}!")
                return reverse('intervention:dashboard')
            elif profile.user_type == 'PARENT':
                messages.success(self.request, f"Welcome, {self.request.user.get_full_name()}!")
                return reverse('intervention:dashboard')
            else:
                messages.warning(self.request, "Your account type is not recognized. Please contact support.")
                return reverse('intervention:dashboard')
                
        except UserProfile.DoesNotExist:
            messages.error(self.request, "User profile not found. Please contact support.")
            return reverse('intervention:dashboard')
        except Exception as e:
            logger.error(f"Login redirect error: {str(e)}")
            messages.error(self.request, "An error occurred during login. Please try again.")
            return reverse('intervention:dashboard')
    
    def form_invalid(self, form):
        """Handle failed login attempts"""
        username = form.cleaned_data.get('username', 'Unknown')
        
        # Log failed login attempt
        try:
            create_audit_log(
                user=None,
                action=f"Failed login attempt for username: {username}",
                details=f"Failed login from {self.get_client_ip()}",
                action_type="LOGIN",
                ip_address=self.get_client_ip()
            )
        except:
            pass
            
        messages.error(self.request, "Invalid username or password. Please try again.")
        return super().form_invalid(form)
    
    def get_client_ip(self):
        """Get client IP address"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip
    
    def dispatch(self, request, *args, **kwargs):
        """Check if user is already authenticated"""
        if request.user.is_authenticated:
            try:
                user_profile = request.user.userprofile
                if user_profile.user_type == 'ADMIN':
                    return redirect('intervention:admin-dashboard')
                else:
                    return redirect('intervention:dashboard')
            except UserProfile.DoesNotExist:
                return redirect('intervention:dashboard')
        return super().dispatch(request, *args, **kwargs)

from django.contrib.auth.views import LogoutView

class CustomLogoutView(LogoutView):
    next_page = 'intervention:login'
    
    def dispatch(self, request, *args, **kwargs):
        """Log the logout action"""
        if request.user.is_authenticated:
            try:
                create_audit_log(
                    user=request.user,
                    action="User logged out",
                    details=f"Logout from session",
                    action_type="LOGOUT"
                )
                messages.success(request, "You have been successfully logged out.")
            except Exception as e:
                logger.error(f"Logout logging error: {str(e)}")
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_client_ip(self):
        """Get the client's IP address"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip

class PasswordResetView(BasePasswordResetView):
    template_name = 'registration/password_reset.html'
    email_template_name = 'registration/password_reset_email.html'
    subject_template_name = 'registration/password_reset_subject.txt'
    success_url = reverse_lazy('intervention:password_reset_done')
    
    def form_valid(self, form):
        """Handle successful password reset request"""
        email = form.cleaned_data.get('email')
        
        # Log the password reset request
        try:
            from django.contrib.auth.models import User
            user = User.objects.get(email=email)
            AuditLog.objects.create(
                user=user,
                action=f"Password reset requested",
                action_type='OTHER',
                details=f"Reset link sent to {email}",
                ip_address=self.get_client_ip()
            )
        except User.DoesNotExist:
            # Log attempt even if user doesn't exist (for security monitoring)
            AuditLog.objects.create(
                user=None,
                action=f"Password reset requested for non-existent email",
                action_type='OTHER',
                details=f"Email: {email}",
                ip_address=self.get_client_ip()
            )
        
        messages.success(
            self.request,
            "If an account with that email exists, we've sent you password reset instructions."
        )
        
        return super().form_valid(form)
    
    def get_client_ip(self):
        """Get the client's IP address"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip

# ====================== UTILITY FUNCTIONS ======================
def get_user_role(user):
    """Get the user's role from their profile"""
    try:
        return user.userprofile.user_type if hasattr(user, 'userprofile') else None
    except UserProfile.DoesNotExist:
        return None

def check_intervention_permission(user, intervention):
    """Check if user has permission to access the intervention"""
    try:
        profile = user.userprofile
        if profile.user_type == 'TEACHER':
            return (intervention.created_by == profile.teacher or 
                    profile.teacher in intervention.collaborating_teachers.all())
        elif profile.user_type == 'PARENT':
            return intervention.student in profile.parent.children.all()
        elif profile.user_type == 'STUDENT':
            return intervention.student == profile.student
        return profile.user_type == 'ADMIN'
    except (UserProfile.DoesNotExist, AttributeError):
        return False

def create_audit_log(user, action, details="", action_type="OTHER", ip_address=None):
    """Create an audit log entry"""
    try:
        # Limit details length to avoid database errors
        if len(details) > 512:
            details = details[:509] + '...'
        
        AuditLog.objects.create(
            user=user, 
            action=action, 
            details=details, 
            action_type=action_type,
            ip_address=ip_address
        )
    except Exception as e:
        logger.error(f"Failed to create audit log: {e}")

# ====================== CORE VIEWS ======================

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'intervention/dashboard.html'
    login_url = 'intervention:login'

    def get_template_names(self):
        """Return different templates based on user role"""
        try:
            profile = self.request.user.userprofile
            if profile.user_type == 'ADMIN':
                return ['intervention/admin_dashboard.html']
            elif profile.user_type == 'TEACHER':
                return ['intervention/teacher_dashboard.html']
            elif profile.user_type == 'STUDENT':
                return ['intervention/student_dashboard.html']
            elif profile.user_type == 'PARENT':
                return ['intervention/parent_dashboard.html']
        except (UserProfile.DoesNotExist, AttributeError):
            pass
        return ['intervention/dashboard.html']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            profile = self.request.user.userprofile
            
            # Common context for all users
            context.update({
                'user_profile': profile,
                'current_date': timezone.now().date(),
                'unread_messages': Message.objects.filter(
                    recipient=profile, 
                    read=False
                ).count(),
                'notifications': Notification.objects.filter(
                    recipient=profile,
                    read=False
                )[:5]
            })
            
            # Role-specific context
            if profile.user_type == 'TEACHER':
                context.update(self.get_teacher_context(profile))
            elif profile.user_type == 'STUDENT':
                context.update(self.get_student_context(profile))
            elif profile.user_type == 'PARENT':
                context.update(self.get_parent_context(profile))
            elif profile.user_type == 'ADMIN':
                context.update(self.get_admin_context())
                
        except UserProfile.DoesNotExist:
            messages.error(self.request, "User profile not found. Please contact support.")
            context['error'] = "Profile not found"
        except Exception as e:
            logger.error(f"Dashboard context error: {str(e)}")
            messages.error(self.request, "Error loading dashboard data.")
            context['error'] = "Data loading error"
            
        return context
    
    def get_teacher_context(self, profile):
        """Get context data for teacher dashboard"""
        try:
            teacher = profile.teacher
            
            # Get teacher's classes and students
            classes = teacher.class_set.all().prefetch_related('students')
            student_ids = Student.objects.filter(
                classes__teacher=teacher
            ).values_list('id', flat=True).distinct()
            
            # Get interventions
            interventions = InterventionPlan.objects.filter(
                Q(created_by=teacher) | Q(collaborating_teachers=teacher)
            ).distinct().select_related('student', 'created_by')
            
            # Get recent progress updates
            recent_progress = ProgressUpdate.objects.filter(
                intervention__in=interventions
            ).select_related('intervention', 'recorded_by').order_by('-date')[:10]
            
            # Get upcoming meetings
            upcoming_meetings = Meeting.objects.filter(
                teacher=teacher,
                completed=False,
                scheduled_time__gte=timezone.now()
            ).select_related('student', 'parent').order_by('scheduled_time')[:5]
            
            # Calculate statistics
            stats = self.calculate_teacher_stats(teacher, student_ids, interventions)
            
            return {
                'teacher': teacher,
                'classes': classes,
                'interventions': interventions.order_by('-start_date')[:5],
                'recent_progress': recent_progress,
                'upcoming_meetings': upcoming_meetings,
                'stats': stats,
                'pending_goals': Goal.objects.filter(
                    student__in=student_ids,
                    completed=False
                ).count()
            }
        except Exception as e:
            logger.error(f"Teacher context error: {str(e)}")
            return {'error': 'Failed to load teacher data'}
    
    def get_student_context(self, profile):
        """Get context data for student dashboard"""
        try:
            student = profile.student
            
            # Get student's interventions
            interventions = InterventionPlan.objects.filter(
                student=student
            ).select_related('created_by').order_by('-start_date')
            
            # Get student's goals
            goals = Goal.objects.filter(
                student=student,
                completed=False
            ).annotate(
                completion=Avg('milestone__completion')
            ).order_by('target_date')
            
            # Get recent progress updates
            recent_progress = ProgressUpdate.objects.filter(
                intervention__student=student
            ).select_related('intervention', 'recorded_by').order_by('-date')[:5]
            
            # Get upcoming meetings
            upcoming_meetings = Meeting.objects.filter(
                student=student,
                completed=False,
                scheduled_time__gte=timezone.now()
            ).select_related('teacher').order_by('scheduled_time')[:3]
            
            # Get recent academic records
            academic_records = AcademicRecord.objects.filter(
                student=student
            ).order_by('-date_recorded')[:5]
            
            return {
                'student': student,
                'interventions': interventions[:5],
                'goals': goals,
                'recent_progress': recent_progress,
                'upcoming_meetings': upcoming_meetings,
                'academic_records': academic_records,
                'total_interventions': interventions.count(),
                'active_interventions': interventions.filter(status='ACTIVE').count(),
                'completed_goals': Goal.objects.filter(
                    student=student, 
                    completed=True
                ).count()
            }
        except Exception as e:
            logger.error(f"Student context error: {str(e)}")
            return {'error': 'Failed to load student data'}
    
    def get_parent_context(self, profile):
        """Get context data for parent dashboard"""
        try:
            parent = profile.parent
            children = parent.children.all()
            
            # Get interventions for all children
            interventions = InterventionPlan.objects.filter(
                student__in=children
            ).select_related('student', 'created_by').order_by('-start_date')
            
            # Get upcoming meetings
            upcoming_meetings = Meeting.objects.filter(
                parent=profile,
                completed=False,
                scheduled_time__gte=timezone.now()
            ).select_related('student', 'teacher').order_by('scheduled_time')
            
            # Get recent progress for children
            recent_progress = ProgressUpdate.objects.filter(
                intervention__student__in=children
            ).select_related(
                'intervention__student', 
                'recorded_by'
            ).order_by('-date')[:10]
            
            # Calculate stats per child
            child_stats = []
            for child in children:
                child_interventions = interventions.filter(student=child)
                child_goals = Goal.objects.filter(student=child, completed=False)
                
                child_stats.append({
                    'child': child,
                    'active_interventions': child_interventions.filter(status='ACTIVE').count(),
                    'total_interventions': child_interventions.count(),
                    'active_goals': child_goals.count(),
                    'latest_progress': ProgressUpdate.objects.filter(
                        intervention__student=child
                    ).order_by('-date').first()
                })
            
            return {
                'parent': parent,
                'children': children,
                'child_stats': child_stats,
                'interventions': interventions[:5],
                'upcoming_meetings': upcoming_meetings,
                'recent_progress': recent_progress,
                'total_children': children.count(),
                'total_interventions': interventions.count(),
                'active_interventions': interventions.filter(status='ACTIVE').count()
            }
        except Exception as e:
            logger.error(f"Parent context error: {str(e)}")
            return {'error': 'Failed to load parent data'}
    
    def get_admin_context(self):
        """Get context data for admin dashboard"""
        try:
            # System-wide statistics
            total_users = UserProfile.objects.count()
            total_students = Student.objects.count()
            total_teachers = Teacher.objects.count()
            total_parents = Parent.objects.count()
            
            # Intervention statistics
            total_interventions = InterventionPlan.objects.count()
            active_interventions = InterventionPlan.objects.filter(status='ACTIVE').count()
            completed_interventions = InterventionPlan.objects.filter(status='COMPLETED').count()
            
            # Recent activity
            recent_users = UserProfile.objects.select_related('user').order_by('-created_at')[:10]
            recent_interventions = InterventionPlan.objects.select_related(
                'student__user_profile__user', 
                'created_by__user_profile__user'
            ).order_by('-created_at')[:10]
            
            recent_activities = AuditLog.objects.select_related('user').order_by('-timestamp')[:15]
            
            # Monthly statistics
            current_month = timezone.now().replace(day=1)
            monthly_stats = {
                'new_users': UserProfile.objects.filter(created_at__gte=current_month).count(),
                'new_interventions': InterventionPlan.objects.filter(created_at__gte=current_month).count(),
                'completed_interventions': InterventionPlan.objects.filter(
                    updated_at__gte=current_month,
                    status='COMPLETED'
                ).count()
            }
            
            return {
                'system_stats': {
                    'total_users': total_users,
                    'total_students': total_students,
                    'total_teachers': total_teachers,
                    'total_parents': total_parents,
                    'total_interventions': total_interventions,
                    'active_interventions': active_interventions,
                    'completed_interventions': completed_interventions
                },
                'recent_users': recent_users,
                'recent_interventions': recent_interventions,
                'recent_activities': recent_activities,
                'monthly_stats': monthly_stats,
                'pending_approvals': InterventionPlan.objects.filter(status='DRAFT').count()
            }
        except Exception as e:
            logger.error(f"Admin context error: {str(e)}")
            return {'error': 'Failed to load admin data'}
    
    def calculate_teacher_stats(self, teacher, student_ids, interventions):
        """Calculate teacher-specific statistics"""
        try:
            # Get date range for calculations
            thirty_days_ago = timezone.now() - timedelta(days=30)
            
            # Calculate attendance rate
            total_attendance = AttendanceRecord.objects.filter(
                student__in=student_ids,
                date__gte=thirty_days_ago
            )
            present_attendance = total_attendance.filter(status='PRESENT')
            
            attendance_rate = 0
            if total_attendance.exists():
                attendance_rate = (present_attendance.count() / total_attendance.count()) * 100
            
            # Calculate average improvement score
            avg_improvement = ProgressUpdate.objects.filter(
                intervention__in=interventions,
                date__gte=thirty_days_ago
            ).aggregate(avg_score=Avg('improvement_score'))['avg_score'] or 0
            
            return {
                'total_students': len(student_ids),
                'active_interventions': interventions.filter(status='ACTIVE').count(),
                'completed_interventions': interventions.filter(status='COMPLETED').count(),
                'attendance_rate': round(attendance_rate, 1),
                'avg_improvement': round(avg_improvement, 1),
                'recent_progress_updates': ProgressUpdate.objects.filter(
                    intervention__in=interventions,
                    date__gte=thirty_days_ago
                ).count()
            }
        except Exception as e:
            logger.error(f"Teacher stats calculation error: {str(e)}")
            return {
                'total_students': 0,
                'active_interventions': 0,
                'completed_interventions': 0,
                'attendance_rate': 0,
                'avg_improvement': 0,
                'recent_progress_updates': 0
            }

class ProfileSetupView(LoginRequiredMixin, TemplateView):
    """View for users who don't have a complete profile"""
    template_name = 'intervention/profile_setup.html'
    
    def dispatch(self, request, *args, **kwargs):
        """Check if user needs profile setup"""
        try:
            profile = request.user.userprofile
            # If profile exists and is complete, redirect to dashboard
            if profile and profile.user_type:
                return redirect('intervention:dashboard')
        except UserProfile.DoesNotExist:
            # Create a basic profile
            UserProfile.objects.create(
                user=request.user,
                user_type='STUDENT'  # Default, can be changed
            )
        
        return super().dispatch(request, *args, **kwargs)

# ====================== INTERVENTION VIEWS ======================
class InterventionDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = InterventionPlan
    template_name = 'intervention/intervention_detail.html'
    context_object_name = 'intervention'
    
    def test_func(self):
        return check_intervention_permission(self.request.user, self.get_object())
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        intervention = self.object
        
        try:
            # Prefetch related data
            documents = InterventionDocument.objects.filter(
                intervention=intervention
            ).select_related('uploaded_by')
            
            progress_updates = ProgressUpdate.objects.filter(
                intervention=intervention
            ).select_related('recorded_by').order_by('-date')
            
            meetings = Meeting.objects.filter(
                Q(intervention=intervention) | 
                Q(student=intervention.student)
            ).select_related('teacher', 'parent').order_by('-scheduled_time')
            
            goals = Goal.objects.filter(
                student=intervention.student,
                intervention_plan=intervention
            ).annotate(
                completion=Avg('milestone__completion')
            )
            
            # Calculate statistics
            total_updates = progress_updates.count()
            avg_improvement = progress_updates.aggregate(
                Avg('improvement_score')
            )['improvement_score__avg'] or 0
            
            context.update({
                'documents': documents,
                'progress_updates': progress_updates,
                'meetings': meetings[:5],
                'goals': goals,
                'total_updates': total_updates,
                'avg_improvement': round(avg_improvement, 1),
                'timeline_events': self.get_timeline_events(intervention),
                'can_edit': self.can_edit_intervention(intervention),
                'can_upload': self.can_upload_documents(intervention),
                'can_add_progress': self.can_add_progress(intervention),
                'progress_chart_data': self.get_progress_chart_data(progress_updates),
            })
            
        except Exception as e:
            logger.error(f"Error loading intervention details: {str(e)}")
            messages.error(self.request, "Error loading intervention details.")
            
        return context
    
    def get_timeline_events(self, intervention):
        """Combine all timeline events in chronological order"""
        events = []
        
        # Add creation event
        events.append({
            'type': 'created',
            'date': intervention.created_at,
            'user': intervention.created_by.user_profile,
            'description': 'Intervention created'
        })
        
        # Add progress updates
        events.extend({
            'type': 'progress',
            'date': update.date,
            'user': update.recorded_by,
            'description': update.notes,
            'score': update.improvement_score
        } for update in ProgressUpdate.objects.filter(intervention=intervention))
        
        # Add document uploads
        events.extend({
            'type': 'document',
            'date': doc.uploaded_at,
            'user': doc.uploaded_by,
            'description': f"Document uploaded: {doc.description}",
            'file': doc.file
        } for doc in InterventionDocument.objects.filter(intervention=intervention))
        
        # Add meetings
        events.extend({
            'type': 'meeting',
            'date': meeting.scheduled_time,
            'users': [meeting.teacher.user_profile, meeting.parent],
            'description': f"Meeting: {meeting.agenda}"
        } for meeting in Meeting.objects.filter(intervention=intervention))
        
        return sorted(events, key=lambda x: x['date'], reverse=True)
    
    def get_progress_chart_data(self, progress_updates):
        """Prepare data for progress chart visualization"""
        if not progress_updates:
            return None
            
        dates = [update.date.strftime('%Y-%m-%d') for update in progress_updates]
        scores = [update.improvement_score for update in progress_updates]
        
        return {
            'labels': dates,
            'data': scores,
            'min_score': min(scores) if scores else 0,
            'max_score': max(scores) if scores else 10
        }
    
    def can_edit_intervention(self, intervention):
        profile = self.request.user.userprofile
        return (profile.user_type == 'TEACHER' and 
                intervention.created_by == profile.teacher)
    
    def can_upload_documents(self, intervention):
        profile = self.request.user.userprofile
        return profile.user_type in ['TEACHER', 'ADMIN']
    
    def can_add_progress(self, intervention):
        profile = self.request.user.userprofile
        return profile.user_type in ['TEACHER', 'ADMIN']

class InterventionListView(LoginRequiredMixin, ListView):
    model = InterventionPlan
    template_name = 'intervention/intervention_list.html'
    paginate_by = 20
    context_object_name = 'interventions'
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'student', 'created_by'
        ).prefetch_related('collaborating_teachers')
        
        profile = self.request.user.userprofile
        status_filter = self.request.GET.get('status')
        search_query = self.request.GET.get('search')
        
        if profile.user_type == 'TEACHER':
            queryset = queryset.filter(
                Q(created_by=profile.teacher) |
                Q(collaborating_teachers=profile.teacher)
            ).distinct()
        elif profile.user_type == 'PARENT':
            queryset = queryset.filter(
                student__in=profile.parent.children.all()
            )
        elif profile.user_type == 'STUDENT':
            if hasattr(profile, 'student'):
                queryset = queryset.filter(student=profile.student)
            else:
                queryset = queryset.none()
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(student__user_profile__user__first_name__icontains=search_query) |
                Q(student__user_profile__user__last_name__icontains=search_query)
            )
            
        return queryset.order_by('-start_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = InterventionPlan.STATUS_CHOICES
        return context

import logging

logger = logging.getLogger(__name__)

# ... (rest of your views.py content)

class CreateInterventionView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = InterventionPlan
    form_class = InterventionForm
    template_name = 'intervention/intervention_form.html'

    def test_func(self):
        return self.request.user.userprofile.user_type in ['TEACHER', 'ADMIN']

    def form_valid(self, form):
        try:
            user_profile = self.request.user.userprofile
            if user_profile.user_type == 'TEACHER':
                form.instance.created_by = user_profile.teacher
            elif user_profile.user_type == 'ADMIN':
                # Admins can create interventions, but they might not have a 'teacher' profile.
                # We need to ensure that 'created_by' is set to a valid Teacher instance.
                # Option 1: If an admin is also a teacher, use their teacher profile.
                # Option 2: If an admin is not a teacher, assign a default teacher or make 'created_by' nullable.
                # For this fix, we'll try to get the teacher profile. If it doesn't exist, it means
                # the admin user doesn't have a linked teacher profile, which is causing the error.
                # We will set created_by to None and let the model handle nullability or require a default.
                try:
                    form.instance.created_by = user_profile.teacher
                except Teacher.DoesNotExist:
                    # If the admin user does not have a linked Teacher profile, set created_by to None.
                    # This assumes that the 'created_by' field in your InterventionPlan model is nullable (null=True).
                    # If 'created_by' is not nullable, you would need to assign a default teacher here.
                    form.instance.created_by = None
            
            if 'student_id' in self.kwargs:
                form.instance.student = get_object_or_404(Student, pk=self.kwargs['student_id'])
            response = super().form_valid(form)
            messages.success(
                self.request,
                'Intervention plan created successfully!'
            )
            AuditLog.objects.create(
                user=self.request.user,
                action=f"Created intervention {self.object.title}",
                details=f"For student {self.object.student}"
            )
            return response
        except Exception as e:
            logger.error(f"Error creating intervention: {str(e)}", exc_info=True)
            messages.error(
                self.request,
                f'Error creating intervention plan: {str(e)}. Please try again.'
            )
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse('intervention:intervention-detail', kwargs={'pk': self.object.pk})



class UpdateInterventionView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = InterventionPlan
    form_class = InterventionForm
    template_name = 'intervention/intervention_form.html'
    
    def test_func(self):
        intervention = self.get_object()
        profile = self.request.user.userprofile
        try:
            if profile.user_type == 'ADMIN':
                return True
            if profile.user_type == 'TEACHER':
                teacher = getattr(profile, 'teacher', None)
                if not teacher:
                    return False
                return (
                    intervention.created_by == teacher or 
                    teacher in intervention.collaborating_teachers.all()
                )
            return False
        except Exception:
            return False
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        messages.success(
            self.request, 
            'Intervention plan updated successfully!'
        )
        
        # Log the update
        AuditLog.objects.create(
            user=self.request.user,
            action=f"Updated intervention {self.object.title}",
            details=f"Changed status to {self.object.status}"
        )
        
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('intervention:intervention-detail', kwargs={'pk': self.object.pk})

class DeleteInterventionView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = InterventionPlan
    template_name = 'intervention/intervention_confirm_delete.html'
    
    def test_func(self):
        intervention = self.get_object()
        profile = self.request.user.userprofile
        try:
            if profile.user_type == 'ADMIN':
                return True
            if profile.user_type == 'TEACHER':
                teacher = getattr(profile, 'teacher', None)
                if not teacher:
                    return False
                return intervention.created_by == teacher
            return False
        except Exception:
            return False
    
    def get_success_url(self):
        messages.success(
            self.request, 
            'Intervention plan deleted successfully!'
        )
        
        # Log the deletion
        AuditLog.objects.create(
            user=self.request.user,
            action=f"Deleted intervention {self.object.title}",
            details=f"For student {self.object.student}"
        )
        
        return reverse('intervention:intervention-list')

class DocumentUploadView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = InterventionDocument
    form_class = DocumentForm
    template_name = 'intervention/document_upload.html'
    
    def test_func(self):
        intervention = get_object_or_404(InterventionPlan, pk=self.kwargs['intervention_id'])
        return check_intervention_permission(self.request.user, intervention)
    
    def form_valid(self, form):
        form.instance.intervention = get_object_or_404(
            InterventionPlan, 
            pk=self.kwargs['intervention_id']
        )
        form.instance.uploaded_by = self.request.user.userprofile
        messages.success(self.request, 'Document uploaded successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('intervention:intervention-detail', kwargs={'pk': self.kwargs['intervention_id']})

class DocumentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = InterventionDocument
    template_name = 'intervention/document_confirm_delete.html'
    
    def test_func(self):
        document = self.get_object()
        profile = self.request.user.userprofile
        return (profile.user_type in ['TEACHER', 'ADMIN'] or
                document.uploaded_by == profile)
    
    def get_success_url(self):
        messages.success(self.request, 'Document deleted successfully!')
        return reverse('intervention:intervention-detail', kwargs={'pk': self.object.intervention.pk})

# ====================== PROGRESS VIEWS ======================
class ProgressUpdateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = ProgressUpdate
    form_class = ProgressUpdateForm
    template_name = 'intervention/progress_update.html'
    
    def test_func(self):
        intervention = get_object_or_404(InterventionPlan, pk=self.kwargs['intervention_id'])
        return check_intervention_permission(self.request.user, intervention)
    
    def form_valid(self, form):
        form.instance.intervention = get_object_or_404(
            InterventionPlan, 
            pk=self.kwargs['intervention_id']
        )
        form.instance.recorded_by = self.request.user.userprofile
        messages.success(self.request, 'Progress updated successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('intervention:intervention-detail', kwargs={'pk': self.kwargs['intervention_id']})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['intervention'] = get_object_or_404(InterventionPlan, pk=self.kwargs['intervention_id'])
        return context

class ProgressHistoryView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = ProgressUpdate
    template_name = 'intervention/progress_history.html'
    paginate_by = 10
    
    def test_func(self):
        self.intervention = get_object_or_404(InterventionPlan, pk=self.kwargs['pk'])
        return check_intervention_permission(self.request.user, self.intervention)
    
    def get_queryset(self):
        return ProgressUpdate.objects.filter(
            intervention=self.intervention
        ).select_related('recorded_by').order_by('-date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['intervention'] = self.intervention
        return context

# ====================== REPORT GENERATION VIEWS ======================
class GenerateInterventionPDF(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        intervention = get_object_or_404(InterventionPlan, pk=self.kwargs['pk'])
        return check_intervention_permission(self.request.user, intervention)
    
    def get(self, request, *args, **kwargs):
        intervention = get_object_or_404(InterventionPlan, pk=self.kwargs['pk'])
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'intervention_{intervention.id}.pdf'
        
        doc = SimpleDocDocument(response, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []
        
        # Title
        elements.append(Paragraph(
            f"Intervention Plan: {intervention.title}",
            styles['Title']
        ))
        elements.append(Spacer(1, 12))
        
        # Basic Info
        info_data = [
            ['Student:', intervention.student],
            ['Created By:', intervention.created_by],
            ['Start Date:', intervention.start_date.strftime('%Y-%m-%d')],
            ['Status:', intervention.get_status_display()]
        ]
        
        elements.append(Table(info_data))
        elements.append(Spacer(1, 12))
        
        # Description
        elements.append(Paragraph("Description:", styles['Heading2']))
        elements.append(Paragraph(intervention.description, styles['Normal']))
        elements.append(Spacer(1, 12))
        
        # Goals
        goals = Goal.objects.filter(intervention_plan=intervention)
        if goals.exists():
            elements.append(Paragraph("Goals:", styles['Heading2']))
            goal_data = [['Goal', 'Target Date', 'Completion']]
            for goal in goals:
                completion = goal.milestone_set.aggregate(
                    avg=Avg('completion')
                )['avg'] or 0
                goal_data.append([
                    goal.description,
                    goal.target_date.strftime('%Y-%m-%d'),
                    f"{completion}%"
                ])
            elements.append(Table(goal_data))
            elements.append(Spacer(1, 12))
        
        # Progress Updates
        updates = ProgressUpdate.objects.filter(intervention=intervention)
        if updates.exists():
            elements.append(Paragraph("Progress Updates:", styles['Heading2']))
            update_data = [['Date', 'Score', 'Notes']]
            for update in updates:
                update_data.append([
                    update.date.strftime('%Y-%m-%d'),
                    update.improvement_score,
                    update.notes[:50] + '...' if len(update.notes) > 50 else update.notes
                ])
            elements.append(Table(update_data))
        
        doc.build(elements)
        return response

# ====================== PROFILE MANAGEMENT VIEWS ======================

class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'intervention/profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        try:
            profile = user.userprofile
            context['profile'] = profile
            
            # Add role-specific data
            if profile.user_type == 'TEACHER':
                context['teacher'] = profile.teacher
                context['classes'] = profile.teacher.class_set.all()
                context['interventions_created'] = InterventionPlan.objects.filter(
                    created_by=profile.teacher
                ).count()
                
            elif profile.user_type == 'STUDENT':
                context['student'] = profile.student
                context['interventions'] = InterventionPlan.objects.filter(
                    student=profile.student
                )
                context['goals'] = Goal.objects.filter(
                    student=profile.student,
                    completed=False
                )
                
            elif profile.user_type == 'PARENT':
                context['parent'] = profile.parent
                context['children'] = profile.parent.children.all()
                context['interventions'] = InterventionPlan.objects.filter(
                    student__in=profile.parent.children.all()
                )
                
        except UserProfile.DoesNotExist:
            messages.error(
                self.request,
                "Profile not found. Please contact an administrator."
            )
        
        return context

class UpdateProfileView(LoginRequiredMixin, UpdateView):
    model = UserProfile
    form_class = UserProfileForm
    template_name = 'intervention/profile_update.html'
    
    def get_object(self):
        return self.request.user.userprofile
    
    def form_valid(self, form):
        messages.success(
            self.request,
            "Your profile has been updated successfully!"
        )
        
        # Log the profile update
        AuditLog.objects.create(
            user=self.request.user,
            action="Profile updated",
            action_type='UPDATE',
            details="User profile information modified"
        )
        
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('intervention:profile')

# ====================== USER MANAGEMENT VIEWS (Admin Only) ======================

class UserManagementView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = UserProfile
    template_name = 'intervention/user_management.html'
    paginate_by = 10
    context_object_name = 'user_profiles'
    
    def test_func(self):
        return (hasattr(self.request.user, 'userprofile') and 
                self.request.user.userprofile.user_type == 'ADMIN')
    
    def get_queryset(self):
        queryset = UserProfile.objects.select_related('user').all()
        
        # Filter by user type if specified
        user_type = self.request.GET.get('type')
        if user_type:
            queryset = queryset.filter(user_type=user_type)
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(user__username__icontains=search) |
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(user__email__icontains=search)
            )
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_types'] = UserProfile.USER_TYPE_CHOICES
        total_users = UserProfile.objects.count()
        context['total_users'] = total_users
        context['user_stats'] = {
            'teachers': UserProfile.objects.filter(user_type='TEACHER').count(),
            'students': UserProfile.objects.filter(user_type='STUDENT').count(),
            'parents': UserProfile.objects.filter(user_type='PARENT').count(),
            'admins': UserProfile.objects.filter(user_type='ADMIN').count(),
            'total_users': total_users,
        }
        return context

from django.contrib.auth import get_user_model
from django.contrib import messages
from django.views.generic import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from .models import AuditLog
from .forms import CustomUserCreationForm

User = get_user_model()

class CreateUserView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = User
    form_class = CustomUserCreationForm
    template_name = 'intervention/create_user.html'
    success_url = reverse_lazy('intervention:user-management')
    
    def test_func(self):
        """Only allow admin users to access this view"""
        return (hasattr(self.request.user, 'userprofile') and 
                self.request.user.userprofile.user_type == 'ADMIN')
    
    def get_form_kwargs(self):
        """Pass the request to the form"""
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
    
    def form_valid(self, form):
        """Handle successful form submission"""
        response = super().form_valid(form)
        
        # Create audit log
        AuditLog.objects.create(
            user=self.request.user,
            action=f"Created new user: {self.object.username}",
            action_type='CREATE',
            details=f"User type: {form.cleaned_data['user_type']}"
        )
        
        messages.success(
            self.request,
            f"User {self.object.username} has been created successfully!"
        )
        
        return response
    
    def form_invalid(self, form):
        """Handle invalid form submission"""
        messages.error(
            self.request,
            "Please correct the errors below."
        )
        return super().form_invalid(form)
    

from django.contrib.auth import get_user_model
from django.contrib import messages
from django.views.generic import DetailView, UpdateView, DeleteView
from django.shortcuts import get_object_or_404, redirect

User = get_user_model()

class UserDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = User
    template_name = 'intervention/user_detail.html'
    context_object_name = 'user_obj'

    def test_func(self):
        return self.request.user.userprofile.user_type == 'ADMIN'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.object.userprofile
        return context

class UserUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = 'intervention/user_form.html'
    
    def test_func(self):
        return self.request.user.userprofile.user_type == 'ADMIN'

    def get_success_url(self):
        messages.success(self.request, 'User updated successfully!')
        return reverse('intervention:user-profile', kwargs={'pk': self.object.pk})

def activate_user(request, pk):
    if not request.user.userprofile.user_type == 'ADMIN':
        raise PermissionDenied
    
    user = get_object_or_404(User, pk=pk)
    user.is_active = True
    user.save()
    
    messages.success(request, f'User {user.username} has been activated.')
    return redirect('intervention:user-management')

def deactivate_user(request, pk):
    if not request.user.userprofile.user_type == 'ADMIN':
        raise PermissionDenied
    
    user = get_object_or_404(User, pk=pk)
    user.is_active = False
    user.save()
    
    messages.success(request, f'User {user.username} has been deactivated.')
    return redirect('intervention:user-management')

class UserDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = User
    template_name = 'intervention/user_confirm_delete.html'
    
    def test_func(self):
        return self.request.user.userprofile.user_type == 'ADMIN'

    def post(self, request, *args, **kwargs):
        # If coming from the user management table, delete directly
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('from_table') == '1':
            self.object = self.get_object()
            self.object.delete()
            messages.success(request, 'User deleted successfully!')
            return redirect('intervention:user-management')
        # Otherwise, show confirmation page
        return super().post(request, *args, **kwargs)

    def get_success_url(self):
        messages.success(self.request, 'User deleted successfully!')
        return reverse('intervention:user-management')

# ====================== HELPER FUNCTIONS ======================

def check_user_setup(user):
    """Check if user has completed their profile setup"""
    try:
        profile = user.userprofile
        
        # Check if profile is complete based on user type
        if profile.user_type == 'TEACHER':
            try:
                teacher = profile.teacher
                return teacher.qualification and teacher.subjects
            except Teacher.DoesNotExist:
                return False
                
        elif profile.user_type == 'STUDENT':
            try:
                student = profile.student
                return student.grade_level and student.enrollment_date
            except Student.DoesNotExist:
                return False
                
        elif profile.user_type == 'PARENT':
            try:
                parent = profile.parent
                return parent.children.exists()
            except Parent.DoesNotExist:
                return False
        
        return True
        
    except UserProfile.DoesNotExist:
        return False

class SetupWizardView(LoginRequiredMixin, TemplateView):
    template_name = 'intervention/setup_wizard.html'
    
    def dispatch(self, request, *args, **kwargs):
        """Redirect if user setup is already complete"""
        if check_user_setup(request.user):
            return redirect('intervention:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['profile'] = self.request.user.userprofile
        except UserProfile.DoesNotExist:
            messages.error(
                self.request,
                "No profile found. Please contact an administrator."
            )
        return context

# ====================== GOAL MANAGEMENT VIEWS ======================

class GoalListView(LoginRequiredMixin, ListView):
    model = Goal
    template_name = 'intervention/goal_list.html'
    paginate_by = 15
    context_object_name = 'goals'
    
    def get_queryset(self):
        profile = self.request.user.userprofile
        
        if profile.user_type == 'TEACHER':
            teacher = profile.teacher
            students = Student.objects.filter(classes__teacher=teacher).distinct()
            return Goal.objects.filter(student__in=students).select_related('student', 'intervention_plan')
        
        elif profile.user_type == 'STUDENT':
            return Goal.objects.filter(
                student=profile.student
            ).select_related('intervention_plan')
        
        elif profile.user_type == 'PARENT':
            return Goal.objects.filter(
                student__in=profile.parent.children.all()
            ).select_related('student', 'intervention_plan')
        
        elif profile.user_type == 'ADMIN':
            return Goal.objects.all().select_related('student', 'intervention_plan')
        
        return Goal.objects.none()

class GoalDetailView(LoginRequiredMixin, DetailView):
    model = Goal
    template_name = 'intervention/goal_detail.html'
    context_object_name = 'goal'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        goal = self.object
        
        context.update({
            'milestones': goal.milestone_set.all().order_by('target_date'),
            'completion_percentage': goal.completion_percentage(),
            'can_edit': self.can_edit_goal(goal)
        })
        
        return context
    
    def can_edit_goal(self, goal):
        profile = self.request.user.userprofile
        if profile.user_type == 'TEACHER':
            teacher = profile.teacher
            # Teacher can edit if the goal's student is in their classes
            return goal.student.classes.filter(teacher=teacher).exists()
        return profile.user_type == 'ADMIN'



# ====================== MEETING MANAGEMENT VIEWS ======================

class MeetingListView(LoginRequiredMixin, ListView):
    model = Meeting
    template_name = 'intervention/meeting_list.html'
    paginate_by = 20
    context_object_name = 'meetings'
    
    def get_queryset(self):
        profile = self.request.user.userprofile
        
        if profile.user_type == 'TEACHER':
            teacher = getattr(profile, 'teacher', None)
            if teacher:
                return Meeting.objects.filter(
                    teacher=teacher
                ).select_related('student', 'parent').order_by('-scheduled_time')
            else:
                return Meeting.objects.none()
        
        elif profile.user_type == 'PARENT':
            # Parent is the UserProfile itself
            return Meeting.objects.filter(
                parent=profile
            ).select_related('teacher', 'student').order_by('-scheduled_time')
        
        elif profile.user_type == 'STUDENT':
            student = getattr(profile, 'student', None)
            if student:
                return Meeting.objects.filter(
                    student=student
                ).select_related('teacher', 'parent').order_by('-scheduled_time')
            else:
                return Meeting.objects.none()
        
        elif profile.user_type == 'ADMIN':
            return Meeting.objects.all().select_related(
                'teacher', 'parent', 'student'
            ).order_by('-scheduled_time')
        
        return Meeting.objects.none()

class CreateMeetingView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Meeting
    form_class = MeetingForm
    template_name = 'intervention/meeting_form.html'
    success_url = reverse_lazy('intervention:meeting-list')
    
    def test_func(self):
        return get_user_role(self.request.user) in ['TEACHER', 'ADMIN']
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        profile = self.request.user.userprofile
        if hasattr(profile, 'teacher'):
            form.instance.teacher = profile.teacher
        # For admin, teacher must be selected in the form
        messages.success(self.request, 'Meeting scheduled successfully!')
        return super().form_valid(form)

# ====================== MESSAGE SYSTEM VIEWS ======================

class MessageListView(LoginRequiredMixin, ListView):
    model = Message
    template_name = 'intervention/message_list.html'
    paginate_by = 20
    context_object_name = 'messages'
    
    def get_queryset(self):
        profile = self.request.user.userprofile
        return Message.objects.filter(
            recipient=profile
        ).select_related('sender').order_by('-sent_at')

class SendMessageView(LoginRequiredMixin, CreateView):
    model = Message
    form_class = MessageForm
    template_name = 'intervention/send_message.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.sender = self.request.user.userprofile
        messages.success(self.request, 'Message sent successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('intervention:message-list')

# ====================== AJAX AND API VIEWS ======================

class MarkMessageReadView(LoginRequiredMixin, View):
    def post(self, request, pk):
        try:
            message = Message.objects.get(
                pk=pk, 
                recipient=request.user.userprofile
            )
            message.read = True
            message.read_at = timezone.now()
            message.save()
            
            return JsonResponse({'success': True})
        except Message.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Message not found'})

class InterventionStatsView(LoginRequiredMixin, View):
    def get(self, request, pk):
        try:
            intervention = get_object_or_404(InterventionPlan, pk=pk)
            
            if not check_intervention_permission(request.user, intervention):
                return JsonResponse({'error': 'Permission denied'}, status=403)
            
            # Calculate statistics
            progress_updates = ProgressUpdate.objects.filter(intervention=intervention)
            
            stats = {
                'total_updates': progress_updates.count(),
                'avg_score': progress_updates.aggregate(
                    Avg('improvement_score')
                )['improvement_score__avg'] or 0,
                'latest_score': progress_updates.first().improvement_score if progress_updates.exists() else None,
                'documents_count': InterventionDocument.objects.filter(
                    intervention=intervention
                ).count(),
                'goals_count': Goal.objects.filter(
                    intervention_plan=intervention
                ).count(),
                'meetings_count': Meeting.objects.filter(
                    intervention=intervention
                ).count()
            }
            
            return JsonResponse(stats)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

# ====================== SEARCH AND FILTER VIEWS ======================

class SearchView(LoginRequiredMixin, TemplateView):
    template_name = 'intervention/search_results.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('q', '')
        
        if query:
            profile = self.request.user.userprofile
            
            # Search interventions
            interventions = InterventionPlan.objects.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(strategies__icontains=query)
            )
            
            # Filter based on user permissions
            if profile.user_type == 'TEACHER':
                interventions = interventions.filter(
                    Q(created_by=profile.teacher) |
                    Q(collaborating_teachers=profile.teacher)
                ).distinct()
            elif profile.user_type == 'PARENT':
                interventions = interventions.filter(
                    student__in=profile.parent.children.all()
                )
            elif profile.user_type == 'STUDENT':
                if hasattr(profile, 'student'):
                    interventions = interventions.filter(
                        student=profile.student
                    )
                else:
                    interventions = interventions.none()
            
            # Search students (for teachers and admins)
            students = []
            if profile.user_type in ['TEACHER', 'ADMIN']:
                students = Student.objects.filter(
                    Q(user_profile__user__first_name__icontains=query) |
                    Q(user_profile__user__last_name__icontains=query)
                )
                
                if profile.user_type == 'TEACHER':
                    # Filter to teacher's students
                    students = students.filter(
                        classes__teacher=profile.teacher
                    ).distinct()
            
            context.update({
                'query': query,
                'interventions': interventions[:10],
                'students': students[:10],
                'total_results': interventions.count() + len(students)
            })
        
        return context

# ====================== NOTIFICATION VIEWS ======================

class NotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = 'intervention/notification_list.html'
    paginate_by = 20
    context_object_name = 'notifications'
    
    def get_queryset(self):
        return Notification.objects.filter(
            recipient=self.request.user.userprofile
        ).order_by('-created_at')

class MarkNotificationReadView(LoginRequiredMixin, View):
    def post(self, request, pk):
        try:
            notification = Notification.objects.get(
                pk=pk,
                recipient=request.user.userprofile
            )
            notification.read = True
            notification.save()
            
            return JsonResponse({'success': True})
        except Notification.DoesNotExist:
            return JsonResponse({'success': False})

# ====================== REPORTING VIEWS ======================

class ReportsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'intervention/reports.html'
    
    def test_func(self):
        return get_user_role(self.request.user) in ['TEACHER', 'ADMIN']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = self.request.user.userprofile
        
        if profile.user_type == 'TEACHER':
            # Teacher-specific reports
            teacher = profile.teacher
            interventions = InterventionPlan.objects.filter(
                Q(created_by=teacher) | Q(collaborating_teachers=teacher)
            ).distinct()
            
            context.update({
                'interventions_count': interventions.count(),
                'active_interventions': interventions.filter(status='ACTIVE').count(),
                'completed_interventions': interventions.filter(status='COMPLETED').count(),
                'students_served': interventions.values('student').distinct().count(),
                'avg_progress': ProgressUpdate.objects.filter(
                    intervention__in=interventions
                ).aggregate(Avg('improvement_score'))['improvement_score__avg'] or 0
            })
            
        elif profile.user_type == 'ADMIN':
            # System-wide reports
            context.update({
                'total_interventions': InterventionPlan.objects.count(),
                'total_students': Student.objects.count(),
                'total_teachers': Teacher.objects.count(),
                'total_parents': Parent.objects.count(),
                'recent_activity': AuditLog.objects.order_by('-timestamp')[:10]
            })
        
        return context

# ====================== ATTENDANCE VIEWS ======================

class AttendanceListView(LoginRequiredMixin, ListView):
    model = AttendanceRecord
    template_name = 'intervention/attendance_list.html'
    paginate_by = 20
    context_object_name = 'object_list'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        profile = self.request.user.userprofile
        
        # Apply user-specific filters
        if profile.user_type == 'TEACHER':
            teacher = getattr(profile, 'teacher', None)
            if teacher:
                queryset = queryset.filter(
                    student__classes__teacher=teacher
                ).distinct()
            else:
                # If no teacher relation, show all records (like admin)
                queryset = queryset.all()
        elif profile.user_type == 'PARENT':
            queryset = queryset.filter(
                student__in=profile.parent.children.all()
            )
        elif profile.user_type == 'STUDENT':
            if hasattr(profile, 'student'):
                queryset = queryset.filter(
                    student=profile.student
                )
            else:
                queryset = queryset.none()
        
        # Apply search filters
        student_id = self.request.GET.get('student')
        if student_id:
            queryset = queryset.filter(student_id=student_id)
            
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
            
        date = self.request.GET.get('date')
        if date:
            queryset = queryset.filter(date=date)
            
        return queryset.select_related(
            'student__user_profile__user'
        ).order_by('-date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = self.request.user.userprofile
        
        # Get available students for filter dropdown
        if profile.user_type == 'TEACHER':
            teacher = getattr(profile, 'teacher', None)
            if teacher:
                context['students'] = Student.objects.filter(
                    classes__teacher=teacher
                ).distinct()
            else:
                # If no teacher relation, show all students (like admin)
                context['students'] = Student.objects.all()
        elif profile.user_type == 'ADMIN':
            context['students'] = Student.objects.all()
        else:
            context['students'] = Student.objects.none()
        
        context['status_choices'] = AttendanceRecord.STATUS_CHOICES
        return context

class CreateAttendanceView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = AttendanceRecord
    form_class = AttendanceForm
    template_name = 'intervention/attendance_form.html'

    def test_func(self):
        return get_user_role(self.request.user) in ['TEACHER', 'ADMIN']

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Attendance record created successfully!')
        return response

    def get_success_url(self):
        # Redirect to the attendance list view after successful submission
        return reverse('intervention:attendance-list')

# ====================== ACADEMIC RECORD VIEWS ======================

class AcademicRecordListView(LoginRequiredMixin, ListView):
    model = AcademicRecord
    template_name = 'intervention/academic_record_list.html'
    paginate_by = 30
    context_object_name = 'academic_records'
    
    def get_queryset(self):
        profile = self.request.user.userprofile
        
        if profile.user_type == 'TEACHER':
            # Teachers see records for their students
            students = Student.objects.filter(classes__teacher=profile.teacher)
            return AcademicRecord.objects.filter(
                student__in=students
            ).select_related('student').order_by('-date_recorded')
            
        elif profile.user_type == 'STUDENT':
            if hasattr(profile, 'student'):
                return AcademicRecord.objects.filter(
                    student=profile.student
                ).order_by('-date_recorded')
            else:
                return AcademicRecord.objects.none()
            
        elif profile.user_type == 'PARENT':
            return AcademicRecord.objects.filter(
                student__in=profile.parent.children.all()
            ).select_related('student').order_by('-date_recorded')
            
        elif profile.user_type == 'ADMIN':
            return AcademicRecord.objects.all().select_related('student').order_by('-date_recorded')
        
        return AcademicRecord.objects.none()

class CreateAcademicRecordView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = AcademicRecord
    form_class = AcademicRecordForm
    template_name = 'intervention/academic_record_form.html'
    
    def test_func(self):
        return get_user_role(self.request.user) in ['TEACHER', 'ADMIN']
    
    def form_valid(self, form):
        messages.success(self.request, 'Academic record created successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('intervention:academic-record-list')

# ====================== DATA EXPORT VIEWS ======================

class ExportInterventionDataView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return get_user_role(self.request.user) in ['TEACHER', 'ADMIN']
    
    def get(self, request, *args, **kwargs):
        profile = request.user.userprofile
        
        # Get interventions based on user role
        if profile.user_type == 'TEACHER':
            interventions = InterventionPlan.objects.filter(
                Q(created_by=profile.teacher) | Q(collaborating_teachers=profile.teacher)
            ).distinct()
        else:  # ADMIN
            interventions = InterventionPlan.objects.all()
        
        # Create response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="interventions_export.csv"'
        
        import csv
        writer = csv.writer(response)
        
        # Write header
        writer.writerow([
            'Title', 'Student', 'Teacher', 'Status', 'Start Date', 
            'End Date', 'Description', 'Goals', 'Strategies'
        ])
        
        # Write data
        for intervention in interventions:
            writer.writerow([
                intervention.title,
                str(intervention.student),
                str(intervention.created_by),
                intervention.get_status_display(),
                intervention.start_date,
                intervention.end_date or '',
                intervention.description,
                intervention.goals,
                intervention.strategies
            ])
        
        return response
    


class TeacherRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin to require teacher or admin access"""
    
    def test_func(self):
        try:
            return self.request.user.userprofile.user_type in ['TEACHER', 'ADMIN']
        except (AttributeError, UserProfile.DoesNotExist):
            return False

class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin to require admin access"""
    
    def test_func(self):
        try:
            return self.request.user.userprofile.user_type == 'ADMIN'
        except (AttributeError, UserProfile.DoesNotExist):
            return False

class ParentRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin to require parent access"""
    
    def test_func(self):
        try:
            return self.request.user.userprofile.user_type == 'PARENT'
        except (AttributeError, UserProfile.DoesNotExist):
            return False

# ====================== API ENDPOINTS FOR DASHBOARD DATA ======================
class DashboardDataAPIView(LoginRequiredMixin, View):
    """API endpoint for dashboard data updates"""
    
    def get(self, request, *args, **kwargs):
        """Return JSON data for dashboard updates"""
        try:
            profile = request.user.userprofile
            data = {
                'user_type': profile.user_type,
                'unread_messages': Message.objects.filter(
                    recipient=profile, 
                    read=False
                ).count(),
                'notifications': Notification.objects.filter(
                    recipient=profile,
                    read=False
                ).count(),
                'timestamp': timezone.now().isoformat()
            }
            
            # Add role-specific data
            if profile.user_type == 'TEACHER':
                teacher = profile.teacher
                data['active_interventions'] = InterventionPlan.objects.filter(
                    Q(created_by=teacher) | Q(collaborating_teachers=teacher),
                    status='ACTIVE'
                ).count()
                
            elif profile.user_type == 'ADMIN':
                data['pending_approvals'] = InterventionPlan.objects.filter(
                    status='DRAFT'
                ).count()
            
            return JsonResponse(data)
            
        except Exception as e:
            logger.error(f"Dashboard API error: {str(e)}")
            return JsonResponse({'error': 'Failed to load data'}, status=500)

# Add the remaining views from the original file...
# (InterventionDetailView, InterventionListView, etc. remain the same)

# ====================== PASSWORD RESET VIEWS ======================
class CustomPasswordResetView(PasswordResetView):
    template_name = 'registration/password_reset.html'
    email_template_name = 'registration/password_reset_email.html'
    success_url = reverse_lazy('intervention:password_reset_done')
    
    def form_valid(self, form):
        """Log password reset request"""
        email = form.cleaned_data.get('email')
        try:
            create_audit_log(
                user=None,
                action=f"Password reset requested for email: {email}",
                details=f"Reset request from {self.get_client_ip()}",
                action_type="OTHER",
                ip_address=self.get_client_ip()
            )
        except:
            pass
        
        return super().form_valid(form)
    
    def get_client_ip(self):
        """Get client IP address"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip

# ====================== ERROR HANDLING VIEWS ======================

def custom_404_view(request, exception):
    """Custom 404 error page"""
    return render(request, 'errors/404.html', status=404)

def custom_500_view(request):
    """Custom 500 error page"""
    return render(request, 'errors/500.html', status=500)

def custom_403_view(request, exception):
    """Custom 403 error page"""
    return render(request, 'errors/403.html', status=403)

def session_interrupted_view(request, exception=None):
    from django.shortcuts import render
    return render(request, 'errors/session_interrupted.html', status=440)

# Add these views to your views.py file

# ====================== MISSING GOAL VIEWS ======================

class UpdateGoalView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Goal
    form_class = GoalForm
    template_name = 'intervention/goal_form.html'
    
    def test_func(self):
        goal = self.get_object()
        profile = self.request.user.userprofile
        if profile.user_type == 'TEACHER':
            # Teachers can edit goals for their students or intervention plans they created
            return (goal.intervention_plan and 
                    goal.intervention_plan.created_by == profile.teacher) or \
                   goal.student.classes.filter(teacher=profile.teacher).exists()
        return profile.user_type == 'ADMIN'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Goal updated successfully!')
        
        # Log the update
        create_audit_log(
            user=self.request.user,
            action=f"Updated goal: {self.object.description[:50]}",
            details=f"For student: {self.object.student}",
            action_type="UPDATE"
        )
        
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('intervention:goal-detail', kwargs={'pk': self.object.pk})

class DeleteGoalView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Goal
    template_name = 'intervention/goal_confirm_delete.html'
    
    def test_func(self):
        goal = self.get_object()
        profile = self.request.user.userprofile
        if profile.user_type == 'TEACHER':
            return (goal.intervention_plan and 
                    goal.intervention_plan.created_by == profile.teacher) or \
                   goal.student.classes.filter(teacher=profile.teacher).exists()
        return profile.user_type == 'ADMIN'
    
    def delete(self, request, *args, **kwargs):
        goal = self.get_object()
        
        # Log the deletion before deleting
        create_audit_log(
            user=request.user,
            action=f"Deleted goal: {goal.description[:50]}",
            details=f"For student: {goal.student}",
            action_type="DELETE"
        )
        
        messages.success(request, 'Goal deleted successfully!')
        return super().delete(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse('intervention:goal-list')

# ====================== MILESTONE VIEWS ======================

class CreateMilestoneView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Milestone
    form_class = MilestoneForm
    template_name = 'intervention/milestone_form.html'
    
    def test_func(self):
        goal = get_object_or_404(Goal, pk=self.kwargs['goal_id'])
        profile = self.request.user.userprofile
        if profile.user_type == 'TEACHER':
            return (goal.intervention_plan and 
                    goal.intervention_plan.created_by == profile.teacher) or \
                   goal.student.classes.filter(teacher=profile.teacher).exists()
        return profile.user_type == 'ADMIN'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['goal'] = get_object_or_404(Goal, pk=self.kwargs['goal_id'])
        return context
    
    def form_valid(self, form):
        form.instance.goal = get_object_or_404(Goal, pk=self.kwargs['goal_id'])
        
        # Log the creation
        create_audit_log(
            user=self.request.user,
            action=f"Created milestone: {form.instance.description}",
            details=f"For goal: {form.instance.goal.description[:50]}",
            action_type="CREATE"
        )
        
        messages.success(self.request, 'Milestone created successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('intervention:goal-detail', kwargs={'pk': self.kwargs['goal_id']})

class UpdateMilestoneView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Milestone
    form_class = MilestoneForm
    template_name = 'intervention/milestone_form.html'
    
    def test_func(self):
        milestone = self.get_object()
        goal = milestone.goal
        profile = self.request.user.userprofile
        if profile.user_type == 'TEACHER':
            return (goal.intervention_plan and 
                    goal.intervention_plan.created_by == profile.teacher) or \
                   goal.student.classes.filter(teacher=profile.teacher).exists()
        return profile.user_type == 'ADMIN'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['goal'] = self.object.goal
        return context
    
    def form_valid(self, form):
        # Log the update
        create_audit_log(
            user=self.request.user,
            action=f"Updated milestone: {self.object.description}",
            details=f"Completion: {form.instance.completion}%",
            action_type="UPDATE"
        )
        
        messages.success(self.request, 'Milestone updated successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('intervention:goal-detail', kwargs={'pk': self.object.goal.pk})

class DeleteMilestoneView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Milestone
    template_name = 'intervention/milestone_confirm_delete.html'
    
    def test_func(self):
        milestone = self.get_object()
        goal = milestone.goal
        profile = self.request.user.userprofile
        if profile.user_type == 'TEACHER':
            return (goal.intervention_plan and 
                    goal.intervention_plan.created_by == profile.teacher) or \
                   goal.student.classes.filter(teacher=profile.teacher).exists()
        return profile.user_type == 'ADMIN'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['goal'] = self.object.goal
        return context
    
    def delete(self, request, *args, **kwargs):
        milestone = self.get_object()
        goal = milestone.goal
        
        # Log the deletion
        create_audit_log(
            user=request.user,
            action=f"Deleted milestone: {milestone.description}",
            details=f"From goal: {goal.description[:50]}",
            action_type="DELETE"
        )
        
        messages.success(request, 'Milestone deleted successfully!')
        return super().delete(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse('intervention:goal-detail', kwargs={'pk': self.object.goal.pk})

# ====================== FIXED CREATE GOAL VIEW ======================

# views.py - Improved CreateGoalView

class CreateGoalView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Goal
    form_class = GoalForm
    template_name = 'intervention/goal_form.html'
    
    def test_func(self):
        return get_user_role(self.request.user) in ['TEACHER', 'ADMIN']
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        
        # For teachers, only show their students
        if self.request.user.userprofile.user_type == 'TEACHER':
            teacher = self.request.user.userprofile.teacher
            kwargs['student_queryset'] = Student.objects.filter(
                classes__teacher=teacher
            ).distinct()
        
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add debug info if needed
        if self.request.user.userprofile.user_type == 'TEACHER':
            teacher = self.request.user.userprofile.teacher
            context['debug_student_count'] = Student.objects.filter(
                classes__teacher=teacher
            ).count()
            context['debug_students'] = Student.objects.filter(
                classes__teacher=teacher
            )[:5]
        
        return context
    
    def form_valid(self, form):
        try:
            # Ensure student is set if coming from URL parameter
            if 'student_id' in self.kwargs and not form.instance.student_id:
                try:
                    student = Student.objects.get(pk=self.kwargs['student_id'])
                    form.instance.student = student
                except Student.DoesNotExist:
                    messages.error(self.request, 'Student not found.')
                    return self.form_invalid(form)
            
            # Double-check that student is set
            if not form.instance.student_id:
                messages.error(self.request, 'A student must be selected for the goal.')
                return self.form_invalid(form)
            
            # Check if user has permission for this student
            profile = self.request.user.userprofile
            if profile.user_type == 'TEACHER':
                teacher = profile.teacher
                if not form.instance.student.classes.filter(teacher=teacher).exists():
                    messages.error(
                        self.request, 
                        'You can only create goals for students in your classes.'
                    )
                    return self.form_invalid(form)
            
            # Save the goal
            response = super().form_valid(form)
            
            # Log the creation
            create_audit_log(
                user=self.request.user,
                action=f"Created goal: {self.object.description[:50]}",
                details=f"For student: {self.object.student}",
                action_type="CREATE"
            )
            
            messages.success(self.request, 'Goal created successfully!')
            return response
            
        except Exception as e:
            logger.error(f"Error creating goal: {str(e)}")
            messages.error(self.request, 'Error creating goal. Please try again.')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        """Handle form validation errors"""
        # Add specific error messages for common issues
        if 'student' in form.errors:
            messages.error(
                self.request,
                'Please select a student for the goal. If no students are available, '
                'contact an administrator to assign students to your classes.'
            )
        
        return super().form_invalid(form)
    
    def get_success_url(self):
        return reverse('intervention:goal-detail', kwargs={'pk': self.object.pk})
    
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect
from .models import Class, Student
from .forms import AssignStudentsForm

@login_required
def assign_students(request, class_id):
    class_obj = get_object_or_404(Class, pk=class_id)
    profile = request.user.userprofile
    # Only allow admin or the assigned teacher
    if not (profile.user_type == 'ADMIN' or (profile.user_type == 'TEACHER' and class_obj.teacher == profile.teacher)):
        return redirect('intervention:dashboard')
    
    if request.method == 'POST':
        form = AssignStudentsForm(request.POST, instance=class_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Students assigned successfully!')
            return redirect('intervention:class-list')
    else:
        form = AssignStudentsForm(instance=class_obj)
    
    return render(request, 'intervention/assign_students.html', {
        'form': form,
        'class_obj': class_obj
    })


# Add these views to your views.py file

# ====================== CLASS MANAGEMENT VIEWS ======================

class ClassListView(LoginRequiredMixin, ListView):
    model = Class
    template_name = 'intervention/class_list.html'
    paginate_by = 12
    context_object_name = 'classes'
    
    def get_queryset(self):
        queryset = Class.objects.select_related('teacher__user_profile__user').prefetch_related('students')
        
        # Filter by teacher if specified
        teacher_id = self.request.GET.get('teacher')
        if teacher_id:
            queryset = queryset.filter(teacher_id=teacher_id)
        
        # Filter by academic year if specified
        academic_year = self.request.GET.get('academic_year')
        if academic_year:
            queryset = queryset.filter(academic_year=academic_year)
        
        # Filter by subject if specified
        subject = self.request.GET.get('subject')
        if subject:
            queryset = queryset.filter(subject__icontains=subject)
        
        # For teachers, only show their classes unless they're admin
        profile = self.request.user.userprofile
        if profile.user_type == 'TEACHER':
            queryset = queryset.filter(teacher=profile.teacher)
        elif profile.user_type == 'STUDENT':
            if hasattr(profile, 'student'):
                queryset = queryset.filter(students=profile.student)
            else:
                queryset = queryset.none()
        
        return queryset.order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all teachers for filter dropdown
        context['teachers'] = Teacher.objects.select_related('user_profile__user').all()
        
        # Get available academic years
        academic_years = Class.objects.values_list('academic_year', flat=True).distinct()
        context['academic_years'] = sorted(academic_years)
        
        return context

class ClassDetailView(LoginRequiredMixin, DetailView):
    model = Class
    template_name = 'intervention/class_detail.html'
    context_object_name = 'class'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        class_obj = self.object
        
        # Get students in this class
        students = class_obj.students.select_related('user_profile__user').all()
        context['students'] = students
        
        # Get recent interventions for students in this class
        recent_interventions = InterventionPlan.objects.filter(
            student__in=students
        ).select_related('student__user_profile__user').order_by('-created_at')[:5]
        context['recent_interventions'] = recent_interventions
        
        # Get attendance stats for this class
        if students:
            total_attendance = AttendanceRecord.objects.filter(
                student__in=students,
                date__gte=timezone.now().date() - timedelta(days=30)
            )
            present_count = total_attendance.filter(status='PRESENT').count()
            total_count = total_attendance.count()
            context['attendance_rate'] = (present_count / total_count * 100) if total_count > 0 else 0
        else:
            context['attendance_rate'] = 0
        
        # Check permissions
        profile = self.request.user.userprofile
        context['can_edit'] = (
            profile.user_type == 'ADMIN' or 
            (profile.user_type == 'TEACHER' and class_obj.teacher == profile.teacher)
        )
        context['can_assign_students'] = (
            profile.user_type == 'ADMIN' or 
            (profile.user_type == 'TEACHER' and class_obj.teacher == profile.teacher)
        )
        return context

class CreateClassView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Class
    form_class = ClassForm
    template_name = 'intervention/class_form.html'
    
    def test_func(self):
        return self.request.user.userprofile.user_type == 'ADMIN'
    
    def form_valid(self, form):
        messages.success(self.request, 'Class created successfully!')
        
        # Log the creation
        create_audit_log(
            user=self.request.user,
            action=f"Created class: {form.instance.name}",
            details=f"Teacher: {form.instance.teacher}, Subject: {form.instance.subject}",
            action_type="CREATE"
        )
        
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('intervention:class-detail', kwargs={'pk': self.object.pk})

class UpdateClassView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Class
    form_class = ClassForm
    template_name = 'intervention/class_form.html'
    
    def test_func(self):
        class_obj = self.get_object()
        profile = self.request.user.userprofile
        return (
            profile.user_type == 'ADMIN' or 
            (profile.user_type == 'TEACHER' and class_obj.teacher == profile.teacher)
        )
    
    def form_valid(self, form):
        messages.success(self.request, 'Class updated successfully!')
        
        # Log the update
        create_audit_log(
            user=self.request.user,
            action=f"Updated class: {self.object.name}",
            details=f"Teacher: {form.instance.teacher}, Subject: {form.instance.subject}",
            action_type="UPDATE"
        )
        
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('intervention:class-detail', kwargs={'pk': self.object.pk})

class DeleteClassView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Class
    template_name = 'intervention/class_confirm_delete.html'
    
    def test_func(self):
        profile = self.request.user.userprofile
        class_obj = self.get_object()
        return (
            profile.user_type == 'ADMIN' or 
            (profile.user_type == 'TEACHER' and class_obj.teacher == profile.teacher)
        )
    
    def post(self, request, *args, **kwargs):
        # Accept POST from the list page and delete directly
        return self.delete(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        class_obj = self.get_object()
        # Log the deletion
        create_audit_log(
            user=request.user,
            action=f"Deleted class: {class_obj.name}",
            details=f"Teacher: {class_obj.teacher}, Students: {class_obj.students.count()}",
            action_type="DELETE"
        )
        messages.success(request, 'Class deleted successfully!')
        return super().delete(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse('intervention:class-list')

# The assign_students view already exists in your project, so we'll use that
# Just make sure you have the URL pattern set up correctly

# Add this to your forms.py file if it doesn't exist:

class ClassForm(forms.ModelForm):
    class Meta:
        model = Class
        fields = ['name', 'teacher', 'subject', 'academic_year', 'room_number', 'schedule', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full bg-futuristic-dark border border-futuristic-light rounded-md px-3 py-2 text-white',
                'placeholder': 'Enter class name'
            }),
            'teacher': forms.Select(attrs={
                'class': 'w-full bg-futuristic-dark border border-futuristic-light rounded-md px-3 py-2 text-white'
            }),
            'subject': forms.TextInput(attrs={
                'class': 'w-full bg-futuristic-dark border border-futuristic-light rounded-md px-3 py-2 text-white',
                'placeholder': 'Enter subject'
            }),
            'academic_year': forms.TextInput(attrs={
                'class': 'w-full bg-futuristic-dark border border-futuristic-light rounded-md px-3 py-2 text-white',
                'placeholder': 'e.g., 2024-2025'
            }),
            'room_number': forms.TextInput(attrs={
                'class': 'w-full bg-futuristic-dark border border-futuristic-light rounded-md px-3 py-2 text-white',
                'placeholder': 'Enter room number'
            }),
            'schedule': forms.TextInput(attrs={
                'class': 'w-full bg-futuristic-dark border border-futuristic-light rounded-md px-3 py-2 text-white',
                'placeholder': 'e.g., Mon/Wed/Fri 9:00-10:00'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full bg-futuristic-dark border border-futuristic-light rounded-md px-3 py-2 text-white',
                'rows': 3,
                'placeholder': 'Enter class description'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active teachers
        self.fields['teacher'].queryset = Teacher.objects.select_related('user_profile__user').filter(
            user_profile__user__is_active=True
        )

# Also add the AssignStudentsForm if it doesn't exist:

class AssignStudentsForm(forms.ModelForm):
    students = forms.ModelMultipleChoiceField(
        queryset=Student.objects.select_related('user_profile__user').all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Select Students"
    )
    
    class Meta:
        model = Class
        fields = ['students']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Get all active students
        self.fields['students'].queryset = Student.objects.select_related(
            'user_profile__user'
        ).filter(user_profile__user__is_active=True).order_by(
            'user_profile__user__first_name', 'user_profile__user__last_name'
        )
        
        # Pre-select already assigned students
        if self.instance.pk:
            self.fields['students'].initial = self.instance.students.all()

# Add these missing view classes to your views.py file:

# ====================== MISSING ATTENDANCE VIEWS ======================

class UpdateAttendanceView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = AttendanceRecord
    form_class = AttendanceForm
    template_name = 'intervention/attendance_form.html'
    
    def test_func(self):
        return get_user_role(self.request.user) in ['TEACHER', 'ADMIN']

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Find all classes this attendance record's student is assigned to
        attendance = self.get_object()
        student = attendance.student
        # Get all classes for this student
        classes = student.classes.all()
        # Get all students assigned to these classes
        assigned_students = Student.objects.filter(classes__in=classes).distinct()
        kwargs['student_queryset'] = assigned_students
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Attendance record updated successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('intervention:attendance-list')

class DeleteAttendanceView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = AttendanceRecord
    # template_name = 'intervention/attendance_confirm_delete.html'  # Removed for SweetAlert2
    
    def test_func(self):
        return get_user_role(self.request.user) in ['TEACHER', 'ADMIN']
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Attendance record deleted successfully!')
        return super().delete(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('intervention:attendance-list')

# ====================== MISSING ACADEMIC RECORD VIEWS ======================

class UpdateAcademicRecordView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = AcademicRecord
    form_class = AcademicRecordForm
    template_name = 'intervention/academic_record_form.html'
    
    def test_func(self):
        return get_user_role(self.request.user) in ['TEACHER', 'ADMIN']
    
    def form_valid(self, form):
        messages.success(self.request, 'Academic record updated successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('intervention:academic-record-list')

class DeleteAcademicRecordView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = AcademicRecord
    template_name = 'intervention/academic_record_confirm_delete.html'
    
    def test_func(self):
        return get_user_role(self.request.user) in ['TEACHER', 'ADMIN']
    
    def post(self, request, *args, **kwargs):
        # Accept POST from the list page
        return self.delete(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Academic record deleted successfully!')
        return super().delete(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse('intervention:academic-record-list')

# ====================== MISSING STUDENT VIEWS ======================

class StudentListView(LoginRequiredMixin, ListView):
    model = Student
    template_name = 'intervention/student_list.html'
    paginate_by = 20
    context_object_name = 'students'
    
    def get_queryset(self):
        profile = self.request.user.userprofile
        queryset = Student.objects.none()

        if profile.user_type == 'TEACHER':
            queryset = Student.objects.filter(
                classes__teacher=profile.teacher
            ).distinct().select_related('user_profile__user')
        elif profile.user_type == 'PARENT':
            queryset = profile.parent.children.all().select_related('user_profile__user')
        elif profile.user_type == 'ADMIN':
            queryset = Student.objects.all().select_related('user_profile__user')

        search = self.request.GET.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(user_profile__user__first_name__icontains=search) |
                Q(user_profile__user__last_name__icontains=search)
            )

        return queryset

class StudentDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Student
    template_name = 'intervention/student_detail.html'
    context_object_name = 'student'
    
    def test_func(self):
        student = self.get_object()
        profile = self.request.user.userprofile
        
        if profile.user_type == 'ADMIN':
            return True
        elif profile.user_type == 'TEACHER':
            return student.classes.filter(teacher=profile.teacher).exists()
        elif profile.user_type == 'PARENT':
            return student in profile.parent.children.all()
        elif profile.user_type == 'STUDENT':
            return student == profile.student
        
        return False
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.object
        
        # Get student's interventions
        context['interventions'] = InterventionPlan.objects.filter(
            student=student
        ).order_by('-created_at')
        
        # Get recent attendance
        context['recent_attendance'] = AttendanceRecord.objects.filter(
            student=student
        ).order_by('-date')[:10]
        
        # Get academic records
        context['academic_records'] = AcademicRecord.objects.filter(
            student=student
        ).order_by('-date_recorded')[:10]
        
        # MBTI result for this student
        answers = MBTIAnswer.objects.filter(user=student.user_profile.user)
        scores = {'E': 0, 'I': 0, 'S': 0, 'N': 0, 'T': 0, 'F': 0, 'J': 0, 'P': 0}
        for ans in answers:
            if ans.answer == 'A':
                scores[ans.question.dichotomy[0]] += 1
            else:
                scores[ans.question.dichotomy[1]] += 1
        if answers.exists():
            mbti_type = (
                ('E' if scores['E'] >= scores['I'] else 'I') +
                ('S' if scores['S'] >= scores['N'] else 'N') +
                ('T' if scores['T'] >= scores['F'] else 'F') +
                ('J' if scores['J'] >= scores['P'] else 'P')
            )
        else:
            mbti_type = None
        context['mbti_type'] = mbti_type
        
        return context

# ====================== MISSING MEETING VIEWS ======================

class MeetingDetailView(LoginRequiredMixin, DetailView):
    model = Meeting
    template_name = 'intervention/meeting_detail.html'
    context_object_name = 'meeting'

class UpdateMeetingView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Meeting
    form_class = MeetingForm
    template_name = 'intervention/meeting_form.html'

    def test_func(self):
        user_role = self.request.user.userprofile.user_type
        return user_role in ['TEACHER', 'ADMIN']
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        # Log the update
        create_audit_log(
            self.request.user,
            f"Updated meeting: {form.instance.title}",
            action_type='UPDATE'
        )
        return super().form_valid(form)

class DeleteMeetingView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Meeting
    template_name = 'intervention/meeting_confirm_delete.html'
    success_url = reverse_lazy('intervention:meeting-list')

    def test_func(self):
        user_role = self.request.user.userprofile.user_type
        return user_role in ['TEACHER', 'ADMIN']

    def delete(self, request, *args, **kwargs):
        # Log the deletion
        create_audit_log(
            self.request.user,
            f"Deleted meeting: {self.get_object().title}",
            action_type='DELETE'
        )
        return super().delete(request, *args, **kwargs)

class StudentCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Student
    form_class = StudentForm  # You'll need to create this form
    template_name = 'intervention/student_form.html'
    
    def test_func(self):
        return self.request.user.userprofile.user_type == 'ADMIN'
    
    def form_valid(self, form):
        # Create UserProfile first
        user = form.cleaned_data['user']
        profile = UserProfile.objects.create(
            user=user,
            user_type='STUDENT'
        )
        
        # Then create Student
        form.instance.user_profile = profile
        messages.success(self.request, 'Student created successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('intervention:student-detail', kwargs={'pk': self.object.pk})

class StudentUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Student
    form_class = StudentForm
    template_name = 'intervention/student_form.html'
    
    def test_func(self):
        return self.request.user.userprofile.user_type == 'ADMIN'
    
    def get_success_url(self):
        return reverse('intervention:student-detail', kwargs={'pk': self.object.pk})

class StudentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Student
    template_name = 'intervention/student_confirm_delete.html'
    
    def test_func(self):
        return self.request.user.userprofile.user_type == 'ADMIN'
    
    def get_success_url(self):
        return reverse('intervention:student-list')

# ====================== PARENT CHILD LINK REQUEST VIEWS ======================

class ParentChildLinkRequestView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    template_name = 'intervention/parent_link_request.html'
    form_class = ParentChildLinkRequestForm
    success_url = '/parent/link-requests/'

    def test_func(self):
        return self.request.user.userprofile.user_type == 'PARENT'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['initial'] = {'student': None}
        return kwargs

    def form_valid(self, form):
        parent = self.request.user.userprofile.parent
        student_id = self.request.POST.get('student')
        if not student_id:
            form.add_error('student_query', 'Please select a student.')
            return self.form_invalid(form)
        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            form.add_error('student_query', 'Student not found.')
            return self.form_invalid(form)
        # Prevent duplicate requests (any status)
        if ParentChildLinkRequest.objects.filter(parent=parent, student=student).exists():
            form.add_error('student_query', 'A request for this student already exists.')
            return self.form_invalid(form)
        # Prevent linking if already linked
        if student in parent.children.all():
            form.add_error('student_query', 'This student is already linked to your account.')
            return self.form_invalid(form)
        # Save request
        ParentChildLinkRequest.objects.create(
            parent=parent,
            student=student,
            message=form.cleaned_data.get('message', '')
        )
        messages.success(self.request, 'Your request has been submitted for review.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['requests'] = ParentChildLinkRequest.objects.filter(parent=self.request.user.userprofile.parent)
        return context

class ParentChildLinkRequestListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = ParentChildLinkRequest
    template_name = 'intervention/parent_link_request_list.html'
    context_object_name = 'link_requests'

    def test_func(self):
        return self.request.user.userprofile.user_type == 'PARENT'

    def get_queryset(self):
        parent = self.request.user.userprofile.parent
        return ParentChildLinkRequest.objects.filter(parent=parent).select_related('student').order_by('-created_at')

from django.http import JsonResponse

class StudentSearchAPIView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        # Only allow parents to search for students
        return self.request.user.userprofile.user_type == 'PARENT'

    def get(self, request, *args, **kwargs):
        query = request.GET.get('search', '').strip()
        results = []
        if len(query) >= 2:
            students = Student.objects.filter(
                Q(user_profile__user__first_name__icontains=query) |
                Q(user_profile__user__last_name__icontains=query) |
                Q(user_profile__user__username__icontains=query) |
                Q(id__icontains=query)
            )[:10]
            for s in students:
                results.append({
                    'id': s.id,
                    'name': s.user_profile.user.get_full_name(),
                    'grade': s.get_grade_level_display(),
                })
        return JsonResponse({'results': results})

class AdminParentChildLinkRequestListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = ParentChildLinkRequest
    template_name = 'intervention/admin_link_request_list.html'
    context_object_name = 'link_requests'

    def test_func(self):
        return self.request.user.userprofile.user_type in ['ADMIN', 'TEACHER']

    def get_queryset(self):
        return ParentChildLinkRequest.objects.select_related('parent__user_profile__user', 'student__user_profile__user').order_by('-created_at')

class AdminParentChildLinkRequestActionView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.userprofile.user_type == 'ADMIN'

    def post(self, request, pk):
        action = request.POST.get('action')
        admin_note = request.POST.get('admin_note', '')
        req = get_object_or_404(ParentChildLinkRequest, pk=pk)
        if req.status != 'PENDING':
            messages.warning(request, 'This request has already been processed.')
            return redirect('intervention:admin-link-request-list')
        if action == 'approve':
            req.status = 'APPROVED'
            req.reviewed_by = request.user.userprofile
            req.reviewed_at = timezone.now()
            req.admin_note = admin_note
            req.save()
            # Link the student to the parent
            req.parent.children.add(req.student)
            messages.success(request, f'Request approved. {req.student} is now linked to {req.parent}.')
        elif action == 'deny':
            req.status = 'DENIED'
            req.reviewed_by = request.user.userprofile
            req.reviewed_at = timezone.now()
            req.admin_note = admin_note
            req.save()
            messages.info(request, 'Request denied.')
        else:
            messages.error(request, 'Invalid action.')
        return redirect('intervention:admin-link-request-list')

class ToggleMeetingStatusView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return get_user_role(self.request.user) in ['TEACHER', 'ADMIN']

    @method_decorator(require_POST)
    def post(self, request, pk):
        meeting = get_object_or_404(Meeting, pk=pk)
        meeting.completed = not meeting.completed
        meeting.save()
        return JsonResponse({'success': True, 'completed': meeting.completed})

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView
from .models import ChatThread, ChatMessage
from django.shortcuts import get_object_or_404

@method_decorator(login_required, name='dispatch')
class ChatThreadListView(ListView):
    model = ChatThread
    template_name = 'intervention/chat_thread_list.html'
    context_object_name = 'threads'

    def get_queryset(self):
        user = self.request.user
        return ChatThread.objects.filter(user1=user) | ChatThread.objects.filter(user2=user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        for thread in context['threads']:
            thread.other_participant = thread.user2 if thread.user1 == user else thread.user1
        return context

@method_decorator(login_required, name='dispatch')
class ChatThreadDetailView(DetailView):
    model = ChatThread
    template_name = 'intervention/chat_thread_detail.html'
    context_object_name = 'thread'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['messages'] = self.object.messages.select_related('sender', 'reply_to').order_by('timestamp')
        context['other_user'] = self.object.get_other_user(self.request.user)
        return context

from django.views import View
from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect
from django.urls import reverse
from django import forms

User = get_user_model()

class StartChatForm(forms.Form):
    user = forms.ModelChoiceField(queryset=User.objects.none(), label="Select User")
    def __init__(self, *args, **kwargs):
        current_user = kwargs.pop('current_user')
        super().__init__(*args, **kwargs)
        self.fields['user'].queryset = User.objects.exclude(id=current_user.id)

class StartChatView(View):
    def get(self, request):
        form = StartChatForm(current_user=request.user)
        return render(request, 'intervention/start_chat.html', {'form': form})

    def post(self, request):
        form = StartChatForm(request.POST, current_user=request.user)
        if form.is_valid():
            other_user = form.cleaned_data['user']
            user1, user2 = sorted([request.user, other_user], key=lambda u: u.id)
            thread, created = ChatThread.objects.get_or_create(user1=user1, user2=user2)
            return redirect(reverse('intervention:chat-thread-detail', args=[thread.pk]))
        return render(request, 'intervention/start_chat.html', {'form': form})

class StartChatView(LoginRequiredMixin, ListView):
    model = User
    template_name = 'intervention/start_chat.html'
    context_object_name = 'users'

    def get_queryset(self):
        # Exclude self and users already in a thread with the current user
        user = self.request.user
        existing_threads = ChatThread.objects.filter(user1=user) | ChatThread.objects.filter(user2=user)
        existing_user_ids = set()
        for thread in existing_threads:
            existing_user_ids.add(thread.user1.id)
            existing_user_ids.add(thread.user2.id)
        return User.objects.exclude(id__in=existing_user_ids).exclude(id=user.id)

    def post(self, request, *args, **kwargs):
        other_user_id = request.POST.get('user_id')
        if not other_user_id:
            return redirect('intervention:start-chat')
        other_user = User.objects.get(id=other_user_id)
        user = request.user
        # Get or create the thread
        thread, created = ChatThread.objects.get_or_create(
            user1=min(user, other_user, key=lambda u: u.id),
            user2=max(user, other_user, key=lambda u: u.id)
        )
        return redirect('intervention:chat-thread-detail', pk=thread.pk)

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView

class LandingPageView(TemplateView):
    template_name = 'home.html'

def reports_view(request):
    total_students = Student.objects.count()
    total_teachers = Teacher.objects.count()
    active_interventions = InterventionPlan.objects.filter(status='ACTIVE').count()

    # Average attendance (as % of PRESENT records over all attendance records)
    total_attendance = AttendanceRecord.objects.count()
    present_attendance = AttendanceRecord.objects.filter(status='PRESENT').count()
    avg_attendance = round((present_attendance / total_attendance) * 100, 1) if total_attendance else 0

    # Intervention status breakdown for chart
    status_counts = list(
        InterventionPlan.objects.values('status')
        .annotate(count=Count('id'))
        .order_by('status')
    )

    # Monthly attendance trend for chart (percentage of PRESENT per month)
    from django.db.models import Q
    attendance_trend_qs = (
        AttendanceRecord.objects
        .extra({'month': "strftime('%%Y-%%m', date)"})
        .values('month')
        .annotate(
            present=Count('id', filter=Q(status='PRESENT')),
            total=Count('id')
        )
        .order_by('month')
    )
    attendance_trend = [
        {'month': row['month'], 'rate': round((row['present'] / row['total']) * 100, 1) if row['total'] else 0}
        for row in attendance_trend_qs
    ]

    # Recent activity (last 10 logs)
    recent_activity = AuditLog.objects.order_by('-timestamp')[:10]

    return render(request, 'intervention/reports.html', {
        'total_students': total_students,
        'total_teachers': total_teachers,
        'active_interventions': active_interventions,
        'avg_attendance': avg_attendance,
        'recent_activity': recent_activity,
        'status_counts': status_counts,
        'attendance_trend': attendance_trend,
    })

from django.template.loader import render_to_string
from django.http import HttpResponse
from xhtml2pdf import pisa

def reports_pdf_view(request):
    total_students = Student.objects.count()
    total_teachers = Teacher.objects.count()
    active_interventions = InterventionPlan.objects.filter(status='ACTIVE').count()
    total_attendance = AttendanceRecord.objects.count()
    present_attendance = AttendanceRecord.objects.filter(status='PRESENT').count()
    avg_attendance = round((present_attendance / total_attendance) * 100, 1) if total_attendance else 0
    from django.db.models import Q
    attendance_trend_qs = (
        AttendanceRecord.objects
        .extra({'month': "strftime('%%Y-%%m', date)"})
        .values('month')
        .annotate(
            present=Count('id', filter=Q(status='PRESENT')),
            total=Count('id')
        )
        .order_by('month')
    )
    attendance_trend = [
        {'month': row['month'], 'rate': round((row['present'] / row['total']) * 100, 1) if row['total'] else 0}
        for row in attendance_trend_qs
    ]
    recent_activity = AuditLog.objects.order_by('-timestamp')[:10]

    context = {
        'total_students': total_students,
        'total_teachers': total_teachers,
        'active_interventions': active_interventions,
        'avg_attendance': avg_attendance,
        'recent_activity': recent_activity,
        'attendance_trend': attendance_trend,
        'pdf_export': True,
    }

    template = get_template('intervention/reports_pdf.html')
    html = template.render(context, request)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="school_report.pdf"'
    pisa.CreatePDF(html, dest=response)
    return response

MBTI_FORMS = [
    ("ei", MBTIEIForm),
    ("sn", MBTISNForm),
    ("tf", MBTITFForm),
    ("jp", MBTIJPForm),
]

MBTI_TEMPLATES = {
    "ei": "intervention/mbti_step.html",
    "sn": "intervention/mbti_step.html",
    "tf": "intervention/mbti_step.html",
    "jp": "intervention/mbti_step.html",
}

class MBTIWizard(SessionWizardView):
    form_list = [MBTIEIForm, MBTISNForm, MBTITFForm, MBTIJPForm]

    def get_template_names(self):
        return [MBTI_TEMPLATES[self.steps.current]]

    def done(self, form_list, **kwargs):
        user = self.request.user
        answers = {}
        for form in form_list:
            answers.update(form.cleaned_data)
        # Save answers
        for field, value in answers.items():
            qid = field.split('_')[1]
            question = MBTIQuestion.objects.get(id=qid)
            MBTIAnswer.objects.update_or_create(
                user=user, question=question,
                defaults={"answer": value}
            )
        # Scoring
        scores = {'E': 0, 'I': 0, 'S': 0, 'N': 0, 'T': 0, 'F': 0, 'J': 0, 'P': 0}
        for field, value in answers.items():
            qid = field.split('_')[1]
            question = MBTIQuestion.objects.get(id=qid)
            if value == 'A':
                scores[question.dichotomy[0]] += 1
            else:
                scores[question.dichotomy[1]] += 1
        mbti_type = (
            ('E' if scores['E'] >= scores['I'] else 'I') +
            ('S' if scores['S'] >= scores['N'] else 'N') +
            ('T' if scores['T'] >= scores['F'] else 'F') +
            ('J' if scores['J'] >= scores['P'] else 'P')
        )
        return render(self.request, 'intervention/mbti_result.html', {'mbti_type': mbti_type})