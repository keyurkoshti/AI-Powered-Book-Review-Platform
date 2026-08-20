from django.urls import path 
from rest_framework_simplejwt.views import TokenRefreshView
from book_review import views
from .api_views import RegisterApiview, LoginApiview, HomepageApiview, ProfileAPIView, LogoutAPIView, CookieTokenRefreshView, CategoryListAPIView, BookListAPIView, CreateReviewAPIView, AddBookAPIView

urlpatterns = [
    # ---------------- HTML Template Pages (Rendered by views.py) ----------------
    path('', views.home_view, name='index'),
    path('home/', views.home_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('profile/', views.profile_view, name='profile'),
    path('book_info/', views.book_info_view, name='book-info'),
    path('form/', views.review_form_view, name='form_view'),

    # ---------------- REST API Endpoints (Handled by api_views.py) ----------------
    path('api/register/', RegisterApiview.as_view(), name='api-register'),
    path('api/register', RegisterApiview.as_view(), name='api-register-no-slash'),
    path('api/login/', LoginApiview.as_view(), name='login_api'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/cookie-refresh/', CookieTokenRefreshView.as_view(), name='cookie_token_refresh'),
    path('api/home/', HomepageApiview.as_view(), name='api_home'),
    path('api/logout/', LogoutAPIView.as_view(), name='logout_api'),
    path('api/categories/', CategoryListAPIView.as_view(), name='api-category-list'),
    path('api/books/', BookListAPIView.as_view(), name='api-book-list'),
    path('api/reviews/', CreateReviewAPIView.as_view(), name='api-create-review'),
    path('api/add-book/', AddBookAPIView.as_view(), name='api-add-book'),
    path('api/profile/', ProfileAPIView.as_view(), name='profile_api'),
]

