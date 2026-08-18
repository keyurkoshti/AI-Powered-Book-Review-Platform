from django.db import models 
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone 
from django.core.validators import MinValueValidator, MaxValueValidator
# Create your models here.

class UserProfileManager(BaseUserManager):

    def create_user(self, email, user_name, password=None, **extra_fields):

        if not email:
            raise ValueError("Email is required")

        email = self.normalize_email(email)

        user = self.model(
            email=email,
            user_name=user_name,
            **extra_fields
        )

        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, user_name, password=None, **extra_fields):

        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError("Superuser must have is_staff=True")

        if extra_fields.get('is_superuser') is not True:
            raise ValueError("Superuser must have is_superuser=True")

        return self.create_user(
            email=email,
            user_name=user_name,
            password=password,
            **extra_fields
        )


# ------------------User Model----------------------
class UserProfile(AbstractUser):
    username = None

    user_name = models.CharField(max_length=50, null=False, unique=False)
    email = models.EmailField(max_length=100, null=False, unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['user_name']

    objects = UserProfileManager()

    def __str__(self):
        return f"{self.user_name} - {self.email}"
    
# ----------------Book Category-----------------
class Category(models.Model):
    name = models.CharField(max_length=100)
    added_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name="category_added")

    def __str__(self):
        return f"{self.name}"



# ---------------------Book Model--------------------------------
class Book(models.Model):
    title = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    author = models.CharField(max_length=100)
    description = models.TextField()
    added_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name="book_added")

    def __str__(self):
        return f"{self.title}"
    


# -----------------book review model------------------------------
class Book_Review_forms(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, null=True, blank=True)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, null=True, blank=True)
    book_photo=models.ImageField(upload_to='book_photos/')
    book_url=models.URLField()
    rating = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(5)], null=True, blank=True)
    book_review=models.CharField(max_length=500)
    created_at = models.DateTimeField(default=timezone.now)  

    def __str__(self):
        return f"{self.book} - {self.user}"


class RefreshTokenStore(models.Model):
    user = models.OneToOneField(
        UserProfile,
        on_delete=models.CASCADE,
        related_name="refresh_token_store"
    )
    refresh_token = models.TextField()
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.user_name}"

    def is_valid(self):
        return timezone.now() < self.expires_at
    