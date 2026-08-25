from django.test import TestCase 
import pytest
from rest_framework.test import APIClient
from book_review.models import UserProfile, Book, Category, Book_Review_forms
from django.urls import reverse

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def authenticated_client(api_client, db):
    user = UserProfile.objects.create_user(
        user_name="testuser",
        email="test@example.com",
        password="TestPassword123"
    )
    api_client.force_login(user)
    # Also set JWT cookies if needed for API tests
    api_client.post(
        "/api/login/",
        {"email": "test@example.com", "password": "TestPassword123"},
        format="json"
    )
    return api_client, user

@pytest.mark.django_db
def test_register_user(api_client):
    response = api_client.post(
        "/api/register",
        {
            "user_name": "newuser",
            "email": "new@example.com",
            "password": "NewPassword123"
        },
        format="json"
    )
    assert response.status_code == 201
    assert response.data["message"] == "User created successfully"
    assert UserProfile.objects.filter(email="new@example.com").exists()

@pytest.mark.django_db
def test_login_and_get_books(authenticated_client):
    client, user = authenticated_client
    response = client.get("/api/books/")
    assert response.status_code == 200

@pytest.mark.django_db
def test_homepage_reviews(authenticated_client):
    client, user = authenticated_client
    # Create a category and book
    cat = Category.objects.create(name="Fiction")
    book = Book.objects.create(title="Test Book", author="Author", category=cat)
    # Create a review
    Book_Review_forms.objects.create(
        user=user,
        book=book,
        rating=5,
        book_review="Great!",
        book_url="http://example.com"
    )
    
    response = client.get("/api/home/")
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]["book_review"] == "Great!"

@pytest.mark.django_db
def test_profile_api(authenticated_client):
    client, user = authenticated_client
    response = client.get("/api/profile/")
    assert response.status_code == 200
    assert response.data["email"] == "test@example.com"
    assert "reviews_count" in response.data

@pytest.mark.django_db
def test_category_list(authenticated_client):
    client, user = authenticated_client
    Category.objects.create(name="Science")
    response = client.get("/api/categories/")
    assert response.status_code == 200
    assert any(cat["name"] == "Science" for cat in response.data)

@pytest.mark.django_db
def test_create_review(authenticated_client):
    client, user = authenticated_client
    cat = Category.objects.create(name="Fiction")
    book = Book.objects.create(title="Test Book", author="Author", category=cat)
    
    response = client.post(
        "/api/reviews/",
        {
            "book": book.id,
            "rating": 4,
            "book_review": "Pretty good.",
            "book_url": "http://example.com"
        },
        format="json"
    )
    assert response.status_code == 201
    assert response.data["message"] == "Review created successfully."
    assert Book_Review_forms.objects.filter(book=book, user=user).exists()

@pytest.mark.django_db
def test_add_book(authenticated_client):
    client, user = authenticated_client
    response = client.post(
        "/api/add-book/",
        {
            "title": "New Book",
            "author": "New Author",
            "category_name": "New Category",
            "description": "Interesting book."
        },
        format="json"
    )
    assert response.status_code == 201
    assert response.data["message"] == "Book added successfully."
    assert Book.objects.filter(title="New Book").exists()
    assert Category.objects.filter(name="New Category").exists()

@pytest.mark.django_db
def test_template_views(authenticated_client):
    """Test that all HTML template views render successfully (HTTP 200)."""
    client, user = authenticated_client
    
    # Protected views (should be 200 when authenticated)
    assert client.get("/").status_code == 200
    assert client.get("/home/").status_code == 200
    assert client.get("/profile/").status_code == 200
    assert client.get("/book_info/").status_code == 200
    assert client.get("/form/").status_code == 200

    # Public views (use a fresh anonymous client)
    anon_client = APIClient()
    assert anon_client.get("/login/").status_code == 200
    assert anon_client.get("/register/").status_code == 200
    
    # Protected views (should be 302 when NOT authenticated)
    assert anon_client.get("/").status_code == 302
    assert anon_client.get("/home/").status_code == 302

