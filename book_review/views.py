from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Book_Review_forms, Book, Category, UserProfile
from .forms import RegisterForm, LoginForm, BookForm, user_form
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from django.conf import settings
from .api_views import store_refresh_token, ACCESS_COOKIE_MAX_AGE, REFRESH_COOKIE_MAX_AGE

# ---------------- Helper Functions ----------------

def set_jwt_cookies(response, user):
    """Helper to set JWT cookies on a response, matching api_views logic."""
    access = AccessToken.for_user(user)
    refresh = RefreshToken.for_user(user)
    
    access_token = str(access)
    refresh_token = str(refresh)
    
    store_refresh_token(user, refresh_token)
    
    response.set_cookie(
        key='access_token',
        value=access_token,
        httponly=True,
        secure=False, 
        samesite='Lax',
        max_age=ACCESS_COOKIE_MAX_AGE
    )
    response.set_cookie(
        key='refresh_token',
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite='Lax',
        max_age=REFRESH_COOKIE_MAX_AGE
    )
    return response

# ---------------- HTML Template Views ----------------

@login_required(login_url='login')
def home_view(request):
    """Render the Home page template with reviews data."""
    reviews = Book_Review_forms.objects.select_related("user", "book").order_by("-id")
    return render(request, 'home.html', {'reviews': reviews})


def login_view(request):
    """Handle user login and render the Login page template."""
    if request.user.is_authenticated:
        return redirect('home')
        
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username_or_email = form.cleaned_data['username_or_email']
            password = form.cleaned_data['password']
            
            user = authenticate(request=request, email=username_or_email, password=password)
            
            if user is None:
                user_obj = UserProfile.objects.filter(user_name=username_or_email).first()
                if user_obj:
                    user = authenticate(request=request, email=user_obj.email, password=password)
            
            if user is not None:
                login(request, user)
                response = redirect('home')
                return set_jwt_cookies(response, user)
            else:
                messages.error(request, "Invalid username/email or password.")
    else:
        form = LoginForm()
        
    return render(request, 'login.html', {'form': form})


def register_view(request):
    """Handle user registration and render the Register page template."""
    if request.user.is_authenticated:
        return redirect('home')
        
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            
            messages.success(request, "Registration successful. Please login.")
            return redirect('login')
    else:
        form = RegisterForm()
        
    return render(request, 'register.html', {'form': form})


@login_required(login_url='login')
def profile_view(request):
    """Render the User Profile page template with user data."""
    user = request.user
    user.reviews_count = Book_Review_forms.objects.filter(user=user).count()
    return render(request, 'profile.html', {'user': user})


@login_required(login_url='login')
def book_info_view(request):
    """Handle adding a new book and render the Add Book page template."""
    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            category_name = form.cleaned_data['category_name']
            category, created = Category.objects.get_or_create(name=category_name)
            
            book = form.save(commit=False)
            book.category = category
            book.added_by = request.user
            book.save()
            
            messages.success(request, "Book added successfully!")
            return redirect('form_view')
    else:
        form = BookForm()
        
    return render(request, 'book.html', {'form': form})


@login_required(login_url='login')
def review_form_view(request):
    """Handle adding a new review and render the Add Review Form page template."""
    if request.method == 'POST':
        form = user_form(request.POST, request.FILES)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.save()
            
            messages.success(request, "Review submitted successfully!")
            return redirect('home')
    else:
        form = user_form()
        
    return render(request, 'book_review_form.html', {'form': form})

def logout_user(request):
    """Handle user logout."""
    logout(request)
    response = redirect('login')
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')
    return response


home = home_view
login_user = login_view
register_user = register_view
register_page = register_view
book_info = book_info_view
form_view = review_form_view
