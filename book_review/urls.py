from django.urls import path 
from rest_framework_simplejwt.views import TokenRefreshView
from .views import form_view, home, register_user, profile_view, register_page
from .api_views import (
    RegisterApiview, LoginApiview, HomepageApiview, ProfileAPIView,
    LogoutAPIView, CookieTokenRefreshView, CategoryListAPIView,
    BookListAPIView, CreateReviewAPIView, AddBookAPIView
)
from book_review import views

urlpatterns = [
    path('register/', views.register_user, name='register'),
    path('profile/', views.profile_view, name="profile"),
    path("book_info/", views.book_info, name="book-info"),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('form/', form_view, name='form_view'),
    path('home/', views.home, name='home'),
    path('api/register', RegisterApiview.as_view(), name='api-register'),
    path('api/login/', LoginApiview.as_view(), name='login_api'),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/token/cookie-refresh/", CookieTokenRefreshView.as_view(), name="cookie_token_refresh"),
    path('api/home/', HomepageApiview.as_view(), name='api_home'),
    path("api/logout/", LogoutAPIView.as_view(), name="logout_api"),
    path('api/categories/', CategoryListAPIView.as_view(), name='api-category-list'),
    path('api/books/', BookListAPIView.as_view(), name='api-book-list'),
    path('api/reviews/', CreateReviewAPIView.as_view(), name='api-create-review'),
    path('api/add-book/', AddBookAPIView.as_view(), name='api-add-book'),
    path("api/profile/", ProfileAPIView.as_view(), name="profile_api"),
]
