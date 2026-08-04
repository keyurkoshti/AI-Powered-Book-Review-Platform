from django.db import models 
from django.contrib.auth.models import User  
from django.utils import timezone 
from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.


# ----------------Book Category-----------------
class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name}"



# ---------------------Book Model--------------------------------
class Book(models.Model):
    title = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    author = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return f"{self.title}"
    


# -----------------book review model------------------------------
class Book_Review_forms(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, null=True, blank=True)
    # book_name=models.CharField(max_length=50)
    book_photo=models.ImageField(upload_to='book_photos/')
    book_url=models.URLField()
    rating = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(5)], null=True, blank=True)
    book_review=models.CharField(max_length=500)
    created_at = models.DateTimeField(default=timezone.now) 

    def __str__(self):
        return f"{self.book} - {self.user}"


class RefreshTokenStore(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="refresh_token_store"
    )
    refresh_token = models.TextField()
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username}"

    def is_valid(self):
        return timezone.now() < self.expires_at
    

    