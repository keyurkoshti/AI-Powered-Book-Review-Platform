from django.urls import path 
from rest_framework_simplejwt.views import TokenRefreshView
from book_review import views
from .api_views import RegisterApiview, LoginApiview, HomepageApiview, ProfileAPIView, LogoutAPIView, CookieTokenRefreshView, CategoryListAPIView, BookListAPIView, CreateReviewAPIView, AddBookAPIView, CreateCheckoutSessionAPIView, StripeWebhookAPIView, AiReviewAPIView

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
    # authentication
    path('api/register', RegisterApiview.as_view(), name='users-register'),
    path('api/login', LoginApiview.as_view(), name='users-login'),
    path('api/logout', LogoutAPIView.as_view(), name='logout-api'),
    path('api/token/refresh', TokenRefreshView.as_view(), name='token-refresh'),
    path('api/token/cookie-refresh', CookieTokenRefreshView.as_view(), name='cookie-token-refresh'),

    # user profile
    path('api/profile', ProfileAPIView.as_view(), name='user-profile'),

    # home
    path('api/home', HomepageApiview.as_view(), name='home'),
    
    # books
    path('api/books', BookListAPIView.as_view(), name='books-list'),
    path('api/books/add', AddBookAPIView.as_view(), name='add-book'),

    # categories
    path('api/categories', CategoryListAPIView.as_view(), name='books-categories'),
    
    # reviews
    path('api/reviews', CreateReviewAPIView.as_view(), name='book-review'),
    path('api/review/improve', AiReviewAPIView.as_view(), name="ai-regenerate-review"),
    
    # payments
    path('api/payments/checkout/<int:book_id>', CreateCheckoutSessionAPIView.as_view(), name='payment-session'),
    path('api/payments/webhook', StripeWebhookAPIView.as_view(), name='payment-event')
]

