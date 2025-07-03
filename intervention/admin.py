# admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import *

# Unregister the default User admin
admin.site.unregister(User)

# Custom User admin with profile inline
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_user_type', 'is_staff', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'userprofile__user_type')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    
    def get_user_type(self, obj):
        try:
            return obj.userprofile.get_user_type_display()
        except UserProfile.DoesNotExist:
            return "No Profile"
    get_user_type.short_description = 'User Type'

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_type', 'phone', 'created_at')
    list_filter = ('user_type', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'phone')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'qualification', 'subjects', 'join_date', 'is_active')
    list_filter = ('is_active', 'join_date')
    search_fields = ('user_profile__user__first_name', 'user_profile__user__last_name', 'qualification', 'subjects')
    date_hierarchy = 'join_date'
    
    def get_full_name(self, obj):
        return obj.user_profile.user.get_full_name()
    get_full_name.short_description = 'Full Name'

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'grade_level', 'enrollment_date', 'iep', 'ell')
    list_filter = ('grade_level', 'iep', 'ell', 'enrollment_date')
    search_fields = ('user_profile__user__first_name', 'user_profile__user__last_name')
    date_hierarchy = 'enrollment_date'
    
    def get_full_name(self, obj):
        return obj.user_profile.user.get_full_name()
    get_full_name.short_description = 'Full Name'

@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'get_children_count', 'occupation', 'employer')
    search_fields = ('user_profile__user__first_name', 'user_profile__user__last_name', 'occupation')
    filter_horizontal = ('children',)
    
    def get_full_name(self, obj):
        return obj.user_profile.user.get_full_name()
    get_full_name.short_description = 'Full Name'
    
    def get_children_count(self, obj):
        return obj.children.count()
    get_children_count.short_description = 'Children Count'

@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'teacher', 'academic_year')
    filter_horizontal = ('students',)  # Makes it easier to assign multiple students
    list_filter = ('teacher', 'academic_year')
    
    def get_student_count(self, obj):
        return obj.students.count()
    get_student_count.short_description = 'Students'

class ProgressUpdateInline(admin.TabularInline):
    model = ProgressUpdate
    extra = 0
    readonly_fields = ('recorded_by',)

class InterventionDocumentInline(admin.TabularInline):
    model = InterventionDocument
    extra = 0
    readonly_fields = ('uploaded_by', 'uploaded_at')

class GoalInline(admin.TabularInline):
    model = Goal
    extra = 0

@admin.register(InterventionPlan)
class InterventionPlanAdmin(admin.ModelAdmin):
    list_display = ('title', 'student', 'created_by', 'status', 'start_date', 'get_progress_count')
    list_filter = ('status', 'start_date', 'created_by')
    search_fields = ('title', 'student__user_profile__user__first_name', 'student__user_profile__user__last_name')
    date_hierarchy = 'start_date'
    filter_horizontal = ('collaborating_teachers',)
    readonly_fields = ('created_at', 'updated_at')
    inlines = [GoalInline, ProgressUpdateInline, InterventionDocumentInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'student', 'created_by', 'collaborating_teachers')
        }),
        ('Timeline', {
            'fields': ('start_date', 'end_date', 'status')
        }),
        ('Details', {
            'fields': ('description', 'goals', 'strategies')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_progress_count(self, obj):
        count = obj.progressupdate_set.count()
        if count > 0:
            url = reverse('admin:intervention_progressupdate_changelist') + f'?intervention={obj.id}'
            return format_html('<a href="{}">{} updates</a>', url, count)
        return '0 updates'
    get_progress_count.short_description = 'Progress Updates'

@admin.register(ProgressUpdate)
class ProgressUpdateAdmin(admin.ModelAdmin):
    list_display = ('intervention', 'date', 'improvement_score', 'recorded_by')
    list_filter = ('date', 'improvement_score', 'recorded_by')
    search_fields = ('intervention__title', 'notes')
    date_hierarchy = 'date'
    readonly_fields = ('recorded_by',)

@admin.register(InterventionDocument)
class InterventionDocumentAdmin(admin.ModelAdmin):
    list_display = ('description', 'intervention', 'uploaded_by', 'uploaded_at', 'get_file_size')
    list_filter = ('uploaded_at', 'uploaded_by')
    search_fields = ('description', 'intervention__title')
    readonly_fields = ('uploaded_by', 'uploaded_at')
    
    def get_file_size(self, obj):
        if obj.file:
            size = obj.file.size
            if size < 1024:
                return f"{size} B"
            elif size < 1024 * 1024:
                return f"{size / 1024:.1f} KB"
            else:
                return f"{size / (1024 * 1024):.1f} MB"
        return "No file"
    get_file_size.short_description = 'File Size'

class MilestoneInline(admin.TabularInline):
    model = Milestone
    extra = 0

@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ('get_description_short', 'student', 'target_date', 'completed', 'get_completion_percentage')
    list_filter = ('completed', 'target_date', 'student')
    search_fields = ('description', 'student__user_profile__user__first_name', 'student__user_profile__user__last_name')
    date_hierarchy = 'target_date'
    inlines = [MilestoneInline]
    
    def get_description_short(self, obj):
        return obj.description[:50] + "..." if len(obj.description) > 50 else obj.description
    get_description_short.short_description = 'Description'
    
    def get_completion_percentage(self, obj):
        percentage = obj.completion_percentage()
        if percentage is not None:
            return f"{percentage:.1f}%"
        return "No milestones"
    get_completion_percentage.short_description = 'Completion %'

@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    list_display = ('description', 'goal', 'target_date', 'completion', 'completed')
    list_filter = ('completed', 'target_date', 'completion')
    search_fields = ('description', 'goal__description')

@admin.register(AcademicRecord)
class AcademicRecordAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'score', 'term', 'date_recorded')
    list_filter = ('term', 'subject', 'date_recorded')
    search_fields = ('student__user_profile__user__first_name', 'student__user_profile__user__last_name', 'subject')
    date_hierarchy = 'date_recorded'

@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ('student', 'date', 'status')
    list_filter = ('status', 'date')
    search_fields = ('student__user_profile__user__first_name', 'student__user_profile__user__last_name')
    date_hierarchy = 'date'

@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ('student', 'teacher', 'parent', 'scheduled_time', 'completed')
    list_filter = ('completed', 'scheduled_time', 'teacher')
    search_fields = ('student__user_profile__user__first_name', 'agenda')
    date_hierarchy = 'scheduled_time'

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('subject', 'sender', 'recipient', 'sent_at', 'read', 'important')
    list_filter = ('read', 'important', 'sent_at')
    search_fields = ('subject', 'sender__user__username', 'recipient__user__username')
    date_hierarchy = 'sent_at'
    readonly_fields = ('sent_at', 'read_at')

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'action_type', 'timestamp', 'ip_address')
    list_filter = ('action_type', 'timestamp')
    search_fields = ('user__username', 'action', 'details')
    date_hierarchy = 'timestamp'
    readonly_fields = ('timestamp',)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'get_message_short', 'read', 'created_at')
    list_filter = ('read', 'created_at')
    search_fields = ('recipient__user__username', 'message')
    date_hierarchy = 'created_at'
    
    def get_message_short(self, obj):
        return obj.message[:50] + "..." if len(obj.message) > 50 else obj.message
    get_message_short.short_description = 'Message'

@admin.register(ParentChildLinkRequest)
class ParentChildLinkRequestAdmin(admin.ModelAdmin):
    list_display = ('parent', 'student', 'status', 'created_at', 'reviewed_at', 'reviewed_by')
    list_filter = ('status', 'created_at')
    search_fields = ('parent__user_profile__user__first_name', 'parent__user_profile__user__last_name', 'student__user_profile__user__first_name', 'student__user_profile__user__last_name')
    readonly_fields = ('created_at', 'reviewed_at')

from django.contrib import admin
from .models import Class, Student, Teacher

# Customize admin site
admin.site.site_header = "PDIE System Administration"
admin.site.site_title = "PDIE Admin"
admin.site.index_title = "Welcome to PDIE System Administration"