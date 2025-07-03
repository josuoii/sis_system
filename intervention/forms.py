# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from .models import *
from django.utils import timezone
from django.db.models import Q

User = get_user_model()

class InterventionForm(forms.ModelForm):
    class Meta:
        model = InterventionPlan
        fields = [
            'title', 'student', 'start_date', 'end_date', 
            'status', 'collaborating_teachers', 'description', 
            'goals', 'strategies'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter intervention title'
            }),
            'student': forms.Select(attrs={
                'class': 'form-select'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'collaborating_teachers': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': '5'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe the student\'s needs and intervention purpose...'
            }),
            'goals': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'List specific, measurable goals...'
            }),
            'strategies': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe intervention strategies and methods...'
            })
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user and hasattr(user, 'userprofile'):
            profile = user.userprofile
            
            # Filter students based on user type
            if profile.user_type == 'TEACHER':
                # Teachers can only select students from their classes
                teacher = profile.teacher
                student_ids = Student.objects.filter(
                    classes__teacher=teacher
                ).values_list('id', flat=True)
                self.fields['student'].queryset = Student.objects.filter(
                    id__in=student_ids
                )
                
                # Exclude self from collaborating teachers
                self.fields['collaborating_teachers'].queryset = Teacher.objects.exclude(
                    id=teacher.id
                )
            elif profile.user_type == 'ADMIN':
                # Admins can see all students and teachers
                self.fields['student'].queryset = Student.objects.all()
                self.fields['collaborating_teachers'].queryset = Teacher.objects.all()

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and end_date <= start_date:
            raise ValidationError("End date must be after start date.")
            
        return cleaned_data

class ProgressUpdateForm(forms.ModelForm):
    class Meta:
        model = ProgressUpdate
        fields = ['date', 'improvement_score', 'notes', 'evidence']
        widgets = {
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'improvement_score': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 10,
                'step': 1
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Describe the student\'s progress, observations, and any notable achievements or challenges...'
            }),
            'evidence': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png,.xlsx,.xls'
            })
        }

    def clean_improvement_score(self):
        score = self.cleaned_data.get('improvement_score')
        if score and (score < 1 or score > 10):
            raise ValidationError("Improvement score must be between 1 and 10.")
        return score

class DocumentForm(forms.ModelForm):
    class Meta:
        model = InterventionDocument
        fields = ['file', 'description']
        widgets = {
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png,.xlsx,.xls'
            }),
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Brief description of the document...'
            })
        }

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Check file size (10MB limit)
            if file.size > 10 * 1024 * 1024:
                raise ValidationError("File size cannot exceed 10MB.")
            
            # Check file extension
            allowed_extensions = [
                '.pdf', '.doc', '.docx', '.jpg', '.jpeg', 
                '.png', '.xlsx', '.xls'
            ]
            file_extension = '.' + file.name.split('.')[-1].lower()
            if file_extension not in allowed_extensions:
                raise ValidationError(
                    "File type not supported. Please upload PDF, DOC, DOCX, "
                    "JPG, PNG, or Excel files."
                )
        return file

# forms.py - Fixed GoalForm with proper student loading

class GoalForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        student_queryset = kwargs.pop('student_queryset', None)
        super().__init__(*args, **kwargs)
        
        if student_queryset is not None:
            self.fields['student'].queryset = student_queryset
        
        # Set date widget attributes
        self.fields['target_date'].widget = forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'min': timezone.now().date().isoformat()
        })

    class Meta:
        model = Goal
        fields = ['student', 'description', 'target_date', 'completed', 'intervention_plan']

class MilestoneForm(forms.ModelForm):
    class Meta:
        model = Milestone
        fields = ['description', 'target_date', 'completion', 'notes']
        widgets = {
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Milestone description...'
            }),
            'target_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'completion': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 100,
                'step': 5
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes...'
            })
        }

class MeetingForm(forms.ModelForm):
    teacher = forms.ModelChoiceField(
        queryset=Teacher.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    class Meta:
        model = Meeting
        fields = [
            'teacher', 'student', 'parent', 'scheduled_time', 
            'agenda', 'intervention'
        ]
        widgets = {
            'student': forms.Select(attrs={
                'class': 'form-select'
            }),
            'parent': forms.Select(attrs={
                'class': 'form-select'
            }),
            'scheduled_time': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'agenda': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Meeting agenda and topics to discuss...'
            }),
            'intervention': forms.Select(attrs={
                'class': 'form-select'
            })
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and hasattr(user, 'userprofile'):
            profile = user.userprofile
            if profile.user_type == 'TEACHER':
                teacher = profile.teacher
                self.fields['teacher'].queryset = Teacher.objects.all()
                self.fields['teacher'].initial = teacher
                student_ids = Student.objects.filter(
                    classes__teacher=teacher
                ).values_list('id', flat=True)
                self.fields['student'].queryset = Student.objects.filter(
                    id__in=student_ids
                )
                parent_ids = Parent.objects.filter(
                    children__in=student_ids
                ).values_list('user_profile_id', flat=True)
                self.fields['parent'].queryset = UserProfile.objects.filter(
                    id__in=parent_ids
                )
                self.fields['intervention'].queryset = InterventionPlan.objects.filter(
                    Q(created_by=teacher) | Q(collaborating_teachers=teacher)
                ).distinct()
            elif profile.user_type == 'ADMIN':
                self.fields['teacher'].queryset = Teacher.objects.all()
                self.fields['teacher'].required = True
                self.fields['student'].queryset = Student.objects.all()
                self.fields['parent'].queryset = UserProfile.objects.filter(user_type='PARENT')
                self.fields['intervention'].queryset = InterventionPlan.objects.all()
            else:
                del self.fields['teacher']

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['recipient', 'subject', 'body', 'important']
        widgets = {
            'recipient': forms.Select(attrs={
                'class': 'form-select'
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Message subject...'
            }),
            'body': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Type your message here...'
            }),
            'important': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user and hasattr(user, 'userprofile'):
            # Exclude self from recipient list
            self.fields['recipient'].queryset = UserProfile.objects.exclude(
                user=user
            )

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['phone', 'address', 'profile_picture']
        widgets = {
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phone number...'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Address...'
            }),
            'profile_picture': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }

class CustomUserCreationForm(UserCreationForm):
    USER_TYPE_CHOICES = [
        ('ADMIN', 'Administrator'),
        ('TEACHER', 'Teacher'),
        ('STUDENT', 'Student'),
        ('PARENT', 'Parent'),
    ]
    
    user_type = forms.ChoiceField(choices=USER_TYPE_CHOICES)
    profile_picture = forms.ImageField(required=False)
    
    # Teacher fields
    qualification = forms.CharField(required=False)
    subjects = forms.CharField(required=False)
    
    # Student fields
    grade_level = forms.ChoiceField(
        choices=Student.GRADE_LEVELS,
        required=False
    )
    enrollment_date = forms.DateField(required=False)
    
    # Parent fields
    occupation = forms.CharField(required=False)
    emergency_contact = forms.CharField(required=False)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 
                 'password1', 'password2', 'user_type', 'profile_picture')
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        # Make email required
        self.fields['email'].required = True
        # Make username not required and read-only (auto-assigned)
        self.fields['username'].required = False
        self.fields['username'].widget.attrs['readonly'] = True
        self.fields['username'].widget.attrs['placeholder'] = 'Will be auto-assigned'
    
    def clean(self):
        cleaned_data = super().clean()
        user_type = cleaned_data.get('user_type')
        if user_type == 'STUDENT':
            enrollment_date = cleaned_data.get('enrollment_date')
            if not enrollment_date:
                self.add_error('enrollment_date', 'Enrollment date is required for students.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user_type = self.cleaned_data['user_type']
        # Generate user_id prefix
        prefix_map = {
            'ADMIN': 'ADM',
            'TEACHER': 'T',
            'STUDENT': 'S',
            'PARENT': 'P',
        }
        prefix = prefix_map.get(user_type, 'U')
        # Find next available number for this user type
        from .models import UserProfile
        last_profile = UserProfile.objects.filter(user_type=user_type, login_id__startswith=prefix).order_by('-login_id').first()
        if last_profile and last_profile.login_id and last_profile.login_id[len(prefix):].isdigit():
            next_num = int(last_profile.login_id[len(prefix):]) + 1
        else:
            next_num = 1
        login_id = f"{prefix}{next_num:03d}"
        user.username = login_id  # Set as login ID
        if commit:
            user.save()
            # Create UserProfile with login_id
            profile = UserProfile.objects.create(
                user=user,
                user_type=user_type,
                login_id=login_id
            )
            # Create specific profile based on user type
            if user_type == 'TEACHER':
                Teacher.objects.create(
                    user_profile=profile,
                    qualification=self.cleaned_data.get('qualification', ''),
                    subjects=self.cleaned_data.get('subjects', ''),
                    join_date=timezone.now().date()
                )
            elif user_type == 'STUDENT':
                Student.objects.create(
                    user_profile=profile,
                    grade_level=self.cleaned_data.get('grade_level', ''),
                    enrollment_date=self.cleaned_data.get('enrollment_date')
                )
            elif user_type == 'PARENT':
                Parent.objects.create(
                    user_profile=profile,
                    occupation=self.cleaned_data.get('occupation', ''),
                    emergency_contact=self.cleaned_data.get('emergency_contact', '')
                )
        return user

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = AttendanceRecord
        fields = ['student', 'date', 'status', 'notes']
        widgets = {
            'student': forms.Select(attrs={
                'class': 'form-select'
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes...'
            })
        }

    def __init__(self, *args, **kwargs):
        student_queryset = kwargs.pop('student_queryset', None)
        super().__init__(*args, **kwargs)
        if student_queryset is not None:
            self.fields['student'].queryset = student_queryset

class AcademicRecordForm(forms.ModelForm):
    class Meta:
        model = AcademicRecord
        fields = ['student', 'subject', 'score', 'term', 'notes']
        widgets = {
            'student': forms.Select(attrs={
                'class': 'form-select'
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Subject name...'
            }),
            'score': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100'
            }),
            'term': forms.Select(attrs={
                'class': 'form-select'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes...'
            })
        }

# Form sets for bulk operations
from django.forms import modelformset_factory

MilestoneFormSet = modelformset_factory(
    Milestone,
    form=MilestoneForm,
    extra=1,
    can_delete=True
)

AttendanceFormSet = modelformset_factory(
    AttendanceRecord,
    form=AttendanceForm,
    extra=5,
    can_delete=False
)

from .models import UserProfile

class UserUpdateForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'username')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop('password')  # Remove password field

from .models import Class, Student

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


class StudentForm(forms.ModelForm):
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    email = forms.EmailField(required=True)
    
    class Meta:
        model = Student
        fields = ['first_name', 'last_name', 'email', 'grade_level', 'enrollment_date', 'iep', 'ell', 'special_notes']
        widgets = {
            'grade_level': forms.Select(attrs={'class': 'form-select'}),
            'enrollment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'iep': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ell': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'special_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower()
        if not email:
            return email

        # For a new student, check if username (which will be email) already exists
        if not self.instance.pk:
            if User.objects.filter(username__iexact=email).exists():
                raise ValidationError("A user with this email address already exists as a username.")
        
        # For existing students, check if another user has this email
        else:
            if User.objects.filter(email__iexact=email).exclude(pk=self.instance.user_profile.user.pk).exists():
                raise ValidationError("This email address is already in use by another user.")
        
        return email

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['first_name'].initial = self.instance.user_profile.user.first_name
            self.fields['last_name'].initial = self.instance.user_profile.user.last_name
            self.fields['email'].initial = self.instance.user_profile.user.email
    
    def save(self, commit=True):
        student = super().save(commit=False)
        
        # Get or create User
        if not student.pk:
            user = User.objects.create_user(
                username=self.cleaned_data['email'].lower(),
                email=self.cleaned_data['email'].lower(),
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name'],
                password=User.objects.make_random_password()
            )
            profile = UserProfile.objects.create(
                user=user,
                user_type='STUDENT'
            )
            student.user_profile = profile
        else:
            user = student.user_profile.user
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.email = self.cleaned_data['email'].lower()
            user.save()
        
        if commit:
            student.save()
        
        return student

class ParentChildLinkRequestForm(forms.ModelForm):
    student_query = forms.CharField(
        label="Student Name or ID",
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter student name or ID...'
        })
    )
    message = forms.CharField(
        label="Message (optional)",
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Add a message for the admin (optional)'
        })
    )

    class Meta:
        model = ParentChildLinkRequest
        fields = ['student', 'message']
        widgets = {
            'student': forms.HiddenInput(),
        }

from .models import MBTIQuestion

class MBTIEIForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for q in MBTIQuestion.objects.filter(dichotomy='EI'):
            self.fields[f'q_{q.id}'] = forms.ChoiceField(
                label=q.text,
                choices=[('A', q.dichotomy[0]), ('B', q.dichotomy[1])],
                widget=forms.RadioSelect,
                required=True
            )

class MBTISNForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for q in MBTIQuestion.objects.filter(dichotomy='SN'):
            self.fields[f'q_{q.id}'] = forms.ChoiceField(
                label=q.text,
                choices=[('A', q.dichotomy[0]), ('B', q.dichotomy[1])],
                widget=forms.RadioSelect,
                required=True
            )

class MBTITFForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for q in MBTIQuestion.objects.filter(dichotomy='TF'):
            self.fields[f'q_{q.id}'] = forms.ChoiceField(
                label=q.text,
                choices=[('A', q.dichotomy[0]), ('B', q.dichotomy[1])],
                widget=forms.RadioSelect,
                required=True
            )

class MBTIJPForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for q in MBTIQuestion.objects.filter(dichotomy='JP'):
            self.fields[f'q_{q.id}'] = forms.ChoiceField(
                label=q.text,
                choices=[('A', q.dichotomy[0]), ('B', q.dichotomy[1])],
                widget=forms.RadioSelect,
                required=True
            )