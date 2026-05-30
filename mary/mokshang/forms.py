from django import forms
from django.contrib.auth.models import User
from .models import UserProfile, Skill, Project, Experience, ContactMessage

class StyledModelForm(forms.ModelForm):
    """Base class to automatically apply CSS classes to form fields."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            # Add form-control class for styling
            existing_classes = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f"{existing_classes} form-control".strip()
            # Add placeholder if not set
            if not field.widget.attrs.get('placeholder'):
                field.widget.attrs['placeholder'] = field.label

class RegisterForm(StyledModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'}),
        help_text="Choose a strong password."
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password'}),
        label="Confirm Password"
    )
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'placeholder': 'Email Address'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        email = cleaned_data.get("email")

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")

        if email and User.objects.filter(email=email).exists():
            self.add_error('email', "A user with this email already exists.")

        return cleaned_data

class UserProfileForm(StyledModelForm):
    class Meta:
        model = UserProfile
        fields = ['title', 'bio', 'profile_picture', 'location', 'resume_url', 'github_url', 'linkedin_url', 'twitter_url']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Tell us about yourself...'}),
        }

class SkillForm(StyledModelForm):
    class Meta:
        model = Skill
        fields = ['name', 'category', 'percentage']
        widgets = {
            'percentage': forms.NumberInput(attrs={'min': 0, 'max': 100, 'placeholder': 'Percentage (e.g. 80)'}),
        }

class ProjectForm(StyledModelForm):
    class Meta:
        model = Project
        fields = ['title', 'description', 'image', 'technologies', 'github_link', 'live_link']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Project details...'}),
            'technologies': forms.TextInput(attrs={'placeholder': 'e.g. Python, Django, Tailwind'}),
        }

class ExperienceForm(StyledModelForm):
    class Meta:
        model = Experience
        fields = ['company', 'role', 'start_date', 'end_date', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Role description and achievements...'}),
            'start_date': forms.TextInput(attrs={'placeholder': 'e.g. Jan 2023'}),
            'end_date': forms.TextInput(attrs={'placeholder': 'e.g. Dec 2024 or Present'}),
        }

class ContactForm(StyledModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Write your message here...'}),
            'name': forms.TextInput(attrs={'placeholder': 'Your Name'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Your Email'}),
            'subject': forms.TextInput(attrs={'placeholder': 'Subject'}),
        }