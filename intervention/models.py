from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import os
from django.db.models import Avg
from django.conf import settings

class UserProfile(models.Model):
    USER_TYPE_CHOICES = [
        ('ADMIN', 'Administrator'),
        ('TEACHER', 'Teacher'),
        ('STUDENT', 'Student'),
        ('PARENT', 'Parent'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    login_id = models.CharField(max_length=10, null=True, blank=True, db_index=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.get_user_type_display()}) [{self.login_id}]"

class Teacher(models.Model):
    user_profile = models.OneToOneField(
        UserProfile, 
        on_delete=models.CASCADE,
        limit_choices_to={'user_type': 'TEACHER'}
    )
    qualification = models.CharField(max_length=100)
    subjects = models.CharField(max_length=200)
    join_date = models.DateField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.user_profile.user.get_full_name()

class Student(models.Model):
    GRADE_LEVELS = [
        ('K', 'Kindergarten'),
        ('1', '1st Grade'),
        ('2', '2nd Grade'),
        ('3', '3rd Grade'),
        ('4', '4th Grade'),
        ('5', '5th Grade'),
        ('6', '6th Grade'),
        ('7', '7th Grade'),
        ('8', '8th Grade'),
        ('9', '9th Grade'),
        ('10', '10th Grade'),
        ('11', '11th Grade'),
        ('12', '12th Grade'),
    ]
    
    user_profile = models.OneToOneField(
        UserProfile, 
        on_delete=models.CASCADE,
        limit_choices_to={'user_type': 'STUDENT'}
    )
    grade_level = models.CharField(max_length=2, choices=GRADE_LEVELS)
    enrollment_date = models.DateField()
    iep = models.BooleanField(default=False, verbose_name='IEP')
    ell = models.BooleanField(default=False, verbose_name='ELL')
    special_notes = models.TextField(blank=True)

    def __str__(self):
        return self.user_profile.user.get_full_name()

class Parent(models.Model):
    user_profile = models.OneToOneField(
        UserProfile, 
        on_delete=models.CASCADE,
        limit_choices_to={'user_type': 'PARENT'}
    )
    children = models.ManyToManyField(Student, related_name='parents')
    occupation = models.CharField(max_length=100, blank=True)
    employer = models.CharField(max_length=100, blank=True)
    emergency_contact = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.user_profile.user.get_full_name()

class Class(models.Model):
    name = models.CharField(max_length=100)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    students = models.ManyToManyField(Student, related_name='classes')
    subject = models.CharField(max_length=100)
    academic_year = models.CharField(max_length=20)
    room_number = models.CharField(max_length=10)
    schedule = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.academic_year})"

class InterventionPlan(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('ARCHIVED', 'Archived'),
    ]
    
    title = models.CharField(max_length=200)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    created_by = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_interventions')
    collaborating_teachers = models.ManyToManyField(
        Teacher, 
        related_name='collaborating_interventions',
        blank=True
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='DRAFT'
    )
    description = models.TextField()
    goals = models.TextField(blank=True)
    strategies = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.student}"

    def get_absolute_url(self):
        return reverse('intervention-detail', kwargs={'pk': self.pk})

    def progress_score(self):
        avg = self.progressupdate_set.aggregate(
            Avg('improvement_score')
        )['improvement_score__avg']
        return round(avg, 1) if avg else None

class InterventionDocument(models.Model):
    intervention = models.ForeignKey(
        InterventionPlan, 
        on_delete=models.CASCADE
    )
    uploaded_by = models.ForeignKey(
        UserProfile, 
        on_delete=models.SET_NULL, 
        null=True
    )
    file = models.FileField(upload_to='intervention_docs/')
    description = models.CharField(max_length=200)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.description} - {self.intervention.title}"

    def filename(self):
        return os.path.basename(self.file.name)

    def extension(self):
        name, extension = os.path.splitext(self.file.name)
        return extension[1:].upper()

class ProgressUpdate(models.Model):
    intervention = models.ForeignKey(InterventionPlan, on_delete=models.CASCADE)
    recorded_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    improvement_score = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    notes = models.TextField()
    evidence = models.FileField(
        upload_to='progress_evidence/', 
        blank=True, 
        null=True
    )

    def __str__(self):
        return f"Progress Update - {self.intervention.title} - {self.date}"

    class Meta:
        ordering = ['-date']

class Goal(models.Model):
    intervention_plan = models.ForeignKey(
        InterventionPlan, 
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    description = models.TextField()
    target_date = models.DateField()
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.description[:50]}... - {self.student}"

    def completion_percentage(self):
        if not self.milestone_set.exists():
            return 0
        return self.milestone_set.aggregate(
            models.Avg('completion')
        )['completion__avg']

class Milestone(models.Model):
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE)
    description = models.CharField(max_length=200)
    target_date = models.DateField()
    completion = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    notes = models.TextField(blank=True)
    completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.description[:50]}... - {self.completion}%"

class AcademicRecord(models.Model):
    TERM_CHOICES = [
        ('1', 'First Term'),
        ('2', 'Second Term'),
        ('3', 'Third Term'),
        ('S', 'Summer'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.CharField(max_length=100)
    score = models.DecimalField(max_digits=5, decimal_places=2)
    term = models.CharField(max_length=1, choices=TERM_CHOICES)
    date_recorded = models.DateField(auto_now_add=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.student} - {self.subject}: {self.score}"

    class Meta:
        ordering = ['-date_recorded']

class AttendanceRecord(models.Model):
    STATUS_CHOICES = [
        ('PRESENT', 'Present'),
        ('ABSENT', 'Absent'),
        ('TARDY', 'Tardy'),
        ('EXCUSED', 'Excused Absence'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.student} - {self.date}: {self.status}"

    class Meta:
        ordering = ['-date']
        unique_together = ['student', 'date']

class Meeting(models.Model):
    intervention = models.ForeignKey(
        InterventionPlan, 
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    parent = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    scheduled_time = models.DateTimeField()
    agenda = models.TextField()
    completed = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    follow_up_required = models.BooleanField(default=False)
    follow_up_notes = models.TextField(blank=True)

    def __str__(self):
        return f"Meeting - {self.student} - {self.scheduled_time}"

    class Meta:
        ordering = ['-scheduled_time']

class Message(models.Model):
    sender = models.ForeignKey(
        UserProfile, 
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    recipient = models.ForeignKey(
        UserProfile, 
        on_delete=models.CASCADE,
        related_name='received_messages'
    )
    subject = models.CharField(max_length=200)
    body = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    important = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.subject} - {self.sender} to {self.recipient}"

    class Meta:
        ordering = ['-sent_at']

class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('OTHER', 'Other'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=50)
    details = models.TextField(blank=True)
    action_type = models.CharField(
        max_length=10, 
        choices=ACTION_CHOICES, 
        default='OTHER'
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    def __str__(self):
        return f"{self.user} - {self.action} - {self.timestamp}"

    class Meta:
        ordering = ['-timestamp']

class Notification(models.Model):
    recipient = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    message = models.TextField()
    link = models.URLField(blank=True)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    related_content_type = models.ForeignKey(
        'contenttypes.ContentType', 
        on_delete=models.SET_NULL, 
        null=True,
        blank=True
    )
    related_object_id = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return f"Notification for {self.recipient}"

    class Meta:
        ordering = ['-created_at']

class ParentChildLinkRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('DENIED', 'Denied'),
    ]
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE, related_name='link_requests')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='parent_link_requests')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(UserProfile, null=True, blank=True, on_delete=models.SET_NULL, related_name='reviewed_link_requests')
    admin_note = models.TextField(blank=True)

    class Meta:
        unique_together = ('parent', 'student')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.parent} requests link to {self.student} ({self.status})"

class ChatThread(models.Model):
    user1 = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='chat_threads1', on_delete=models.CASCADE)
    user2 = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='chat_threads2', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user1', 'user2')

    def __str__(self):
        return f"Chat between {self.user1} and {self.user2}"

    def get_other_user(self, user):
        return self.user2 if self.user1 == user else self.user1

class ChatMessage(models.Model):
    thread = models.ForeignKey(ChatThread, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='chat_sent_messages', on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    reply_to = models.ForeignKey('self', null=True, blank=True, related_name='replies', on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.sender}: {self.content[:30]}..."

class MBTIQuestion(models.Model):
    QUESTION_DICHOTOMY_CHOICES = [
        ('EI', 'Extraversion/Introversion'),
        ('SN', 'Sensing/Intuition'),
        ('TF', 'Thinking/Feeling'),
        ('JP', 'Judging/Perceiving'),
    ]
    text = models.CharField(max_length=255)
    dichotomy = models.CharField(max_length=2, choices=QUESTION_DICHOTOMY_CHOICES)

    def __str__(self):
        return self.text

class MBTIAnswer(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    question = models.ForeignKey(MBTIQuestion, on_delete=models.CASCADE)
    answer = models.CharField(max_length=1, choices=[('A', 'First option'), ('B', 'Second option')])
    answered_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'question')

    def __str__(self):
        return f"{self.user} - {self.question} ({self.answer})"