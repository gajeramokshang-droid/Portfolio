from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from django.contrib import messages

from .forms import (
    RegisterForm, UserProfileForm, SkillForm, 
    ProjectForm, ExperienceForm, ContactForm
)
from .models import UserProfile, Skill, Project, Experience, ContactMessage

def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Deactivate until verified
            user.set_password(form.cleaned_data['password'])
            user.save()
            
            # Send Email Logic
            current_site = get_current_site(request)
            subject = 'Activate Your Account - Portfolio Hub'
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Verification URL
            activation_link = f"http://{current_site.domain}/activate/{uid}/{token}/"
            
            # Email body
            message = render_to_string('acc_active_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': uid,
                'token': token,
            })
            
            # Send the email (will output to console in dev settings)
            send_mail(subject, message, settings.EMAIL_HOST_USER or 'noreply@portfoliohub.com', [user.email])
            
            # Render activation_sent.html directly so we can pass helper link in DEBUG mode
            return render(request, 'activation_sent.html', {
                'email': user.email,
                'debug_mode': settings.DEBUG,
                'activation_link': activation_link
            })
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})

def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        messages.success(request, 'Your account has been successfully verified! Welcome to your dashboard.')
        return redirect('dashboard')
    else:
        return render(request, 'activation_invalid.html')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Check if the user exists and is inactive
        user_exists = User.objects.filter(username=username).first()
        if user_exists and not user_exists.is_active:
            messages.error(request, 'Your account is registered but not active. Please click the activation link sent to your email.')
            return render(request, 'login.html')
            
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')

@login_required
def dashboard(request):
    # Handle deletes or marking read via GET query parameters
    if 'delete_project' in request.GET:
        proj_id = request.GET.get('delete_project')
        proj = get_object_or_404(Project, id=proj_id, user=request.user)
        proj.delete()
        messages.success(request, 'Project deleted successfully.')
        return redirect('dashboard')
        
    if 'delete_skill' in request.GET:
        skill_id = request.GET.get('delete_skill')
        skill = get_object_or_404(Skill, id=skill_id, user=request.user)
        skill.delete()
        messages.success(request, 'Skill deleted successfully.')
        return redirect('dashboard')
        
    if 'delete_experience' in request.GET:
        exp_id = request.GET.get('delete_experience')
        exp = get_object_or_404(Experience, id=exp_id, user=request.user)
        exp.delete()
        messages.success(request, 'Experience deleted successfully.')
        return redirect('dashboard')
        
    if 'mark_read' in request.GET:
        msg_id = request.GET.get('mark_read')
        msg = get_object_or_404(ContactMessage, id=msg_id, user=request.user)
        msg.is_read = True
        msg.save()
        messages.success(request, 'Message marked as read.')
        return redirect('dashboard')

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_profile':
            profile_form = UserProfileForm(request.POST, request.FILES, instance=request.user.profile)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Profile updated successfully.')
            else:
                messages.error(request, 'Error updating profile.')
                
        elif action == 'add_project':
            project_form = ProjectForm(request.POST, request.FILES)
            if project_form.is_valid():
                project = project_form.save(commit=False)
                project.user = request.user
                project.save()
                messages.success(request, 'Project added successfully.')
            else:
                messages.error(request, 'Error adding project.')
                
        elif action == 'add_skill':
            skill_form = SkillForm(request.POST)
            if skill_form.is_valid():
                skill = skill_form.save(commit=False)
                skill.user = request.user
                skill.save()
                messages.success(request, 'Skill added successfully.')
            else:
                messages.error(request, 'Error adding skill.')
                
        elif action == 'add_experience':
            experience_form = ExperienceForm(request.POST)
            if experience_form.is_valid():
                exp = experience_form.save(commit=False)
                exp.user = request.user
                exp.save()
                messages.success(request, 'Experience added successfully.')
            else:
                messages.error(request, 'Error adding experience.')
                
        return redirect('dashboard')

    # GET requests: fetch all info and prepare forms
    profile_form = UserProfileForm(instance=request.user.profile)
    project_form = ProjectForm()
    skill_form = SkillForm()
    experience_form = ExperienceForm()
    
    projects = request.user.projects.all()
    skills = request.user.skills.all()
    experiences = request.user.experiences.all()
    contact_messages = request.user.contact_messages.all().order_by('-created_at')

    # Active tab helper (to return user to the tab they were on)
    active_tab = request.GET.get('tab', 'profile')

    context = {
        'profile_form': profile_form,
        'project_form': project_form,
        'skill_form': skill_form,
        'experience_form': experience_form,
        'projects': projects,
        'skills': skills,
        'experiences': experiences,
        'contact_messages': contact_messages,
        'active_tab': active_tab,
    }
    return render(request, 'dashboard.html', context)

def portfolio(request, username=None):
    if username:
        user = get_object_or_404(User, username=username)
    else:
        if request.user.is_authenticated:
            user = request.user
        else:
            # If guest visits base URL and is not logged in, redirect to login
            return redirect('login')
            
    profile = get_object_or_404(UserProfile, user=user)
    skills = user.skills.all()
    projects = user.projects.all()
    experiences = user.experiences.all()

    if request.method == 'POST':
        contact_form = ContactForm(request.POST)
        if contact_form.is_valid():
            msg = contact_form.save(commit=False)
            msg.user = user
            msg.save()
            messages.success(request, 'Your message has been sent successfully!')
            if username:
                return redirect('portfolio_public', username=username)
            else:
                return redirect('portfolio')
    else:
        contact_form = ContactForm()

    # Categorize skills for beautiful tab/grid styling
    skills_by_category = {
        'Frontend': skills.filter(category='Frontend'),
        'Backend': skills.filter(category='Backend'),
        'Database': skills.filter(category='Database'),
        'Tools': skills.filter(category='Tools'),
    }

    context = {
        'portfolio_user': user,
        'profile': profile,
        'skills_by_category': skills_by_category,
        'has_skills': skills.exists(),
        'projects': projects,
        'experiences': experiences,
        'contact_form': contact_form,
        'is_owner': (request.user == user)
    }
    return render(request, 'portfolio.html', context)
