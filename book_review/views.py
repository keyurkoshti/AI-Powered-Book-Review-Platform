from django.shortcuts import render

# ---------------- HTML Template Views ----------------
# views.py is dedicated solely to rendering HTML template pages.
# All data operations, authentication, and mutations are handled via API calls to api_views.py.

def home_view(request):
    """Render the Home page template."""
    return render(request, 'home.html')


def login_view(request):
    """Render the Login page template."""
    return render(request, 'login.html')


def register_view(request):
    """Render the Register page template."""
    return render(request, 'register.html')


def profile_view(request):
    """Render the User Profile page template."""
    return render(request, 'profile.html')


def book_info_view(request):
    """Render the Add Book page template."""
    return render(request, 'book.html')


def review_form_view(request):
    """Render the Add Review Form page template."""
    return render(request, 'book_review_form.html')


# Backward-compatible aliases for existing references
home = home_view
login_user = login_view
register_user = register_view
register_page = register_view
book_info = book_info_view
form_view = review_form_view