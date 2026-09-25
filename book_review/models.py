from django.db import models 
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone 
from django.core.validators import MinValueValidator, MaxValueValidator
import time
# Create your models here.


class UserProfileManager(BaseUserManager):

    def create_user(self, email, user_name, password, **extra_fields):
        if not email:
            raise ValueError("Email is required")

        email = self.normalize_email(email)
        user = self.model(email=email,user_name=user_name,**extra_fields)
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

        return self.create_user(email=email,user_name=user_name,password=password,**extra_fields)


# ------------------User Model----------------------
class UserProfile(AbstractUser):
    username = None

    user_name = models.CharField(max_length=50, null=False, unique=False, db_index=True)
    email = models.EmailField(max_length=254, null=False, unique=True)
    is_active = models.BooleanField(default=True, db_index=True)
    date_joined = models.DateTimeField(auto_now_add=True, db_index=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['user_name']

    objects = UserProfileManager()

    def __str__(self):
        return f"{self.user_name} - {self.email}"
    

# --------------------Background Email task-------------------------
class OutboxEvent(models.Model):
    EVENT_TYPES = [("WELCOME_EMAIL", "Welcome Email")]
    
    event_type = models.CharField(max_length=100,choices=EVENT_TYPES,)
    payload = models.JSONField()
    status = models.CharField(max_length=20,default="PENDING")
    attempts = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
# ----------------Book Category-----------------
class Category(models.Model):
    name = models.CharField(max_length=100)
    added_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name="category_added")

    def __str__(self):
        return f"{self.name}"

# ---------------------Book Model--------------------------------
class Book(models.Model):
    title = models.CharField(max_length=100, unique=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="books")
    author = models.CharField(max_length=100)
    description = models.TextField()
    added_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name="book_added")
    is_available = models.BooleanField(default=False)
    date_added = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.title}"

# -----------------book review model------------------------------
class Book_Review_forms(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, null=True, blank=True)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, null=True, blank=True)
    book_photo=models.ImageField(upload_to='book_photos/', null=True, blank=True)
    book_url=models.URLField()
    rating = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(5)], null=True, blank=True)
    book_review=models.TextField(max_length=500)
    created_at = models.DateTimeField(default=timezone.now)  

    def __str__(self):
        return f"{self.book} - {self.user}"

# -----------------Refresh Token Store Model------------------------------
class RefreshTokenStore(models.Model):
    user = models.OneToOneField(UserProfile,on_delete=models.CASCADE,related_name="refresh_token_store",db_index=True)
    refresh_token = models.CharField(max_length=511, db_index=True)
    expires_at = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.user_name}"

    def is_valid(self):
        return timezone.now() < self.expires_at
    
# -----------------Book Subscription Model------------------------------
class BookSubScription(models.Model):
    STATUS_PENDING   = 'pending'
    STATUS_ACTIVE    = 'active'
    STATUS_FAILED    = 'failed'
    STATUS_EXPIRED   = 'expired'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_ACTIVE, 'Active'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_EXPIRED, 'Expired'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    subscription_choices = [(1, "1 month"), (3, "3 month"), (6, "6 month"), (12, "12 month")]

    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="subscriptions")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="subscribed")
    subscription_duration = models.PositiveIntegerField(choices=subscription_choices)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='inr')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    stripe_checkout_session_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    stripe_payment_intent_id = models.CharField(max_length=255, null=True, blank=True)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['book'],
                condition=models.Q(status__in = ['pending','active']),
                name = 'unique_active_or_pending_subscrption_per_book',
            )
        ]

    def is_active(self):
        return self.status == self.STATUS_ACTIVE and self.end_date and self.end_date > timezone.now()

# -----------------Stripe Webhook Event Model------------------------------
class StripeWebHookEvent(models.Model):
    event_id = models.CharField(max_length=255, unique=True)
    event_type = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.event_id} - {self.created_at}"

# -----------------User AI Credit Model------------------------------
class UserAiCredit(models.Model):
    user = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name="ai_credit")
    total_credits = models.PositiveBigIntegerField(default=10)
    remaining_credits = models.PositiveBigIntegerField(default=10)
    total_used_credits = models.PositiveBigIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.remaining_credits} credits"
    
# -----------------AI Usage Log Model------------------------------
class AiUsageLog(models.Model):
    status_choices = (("success", "Success"),("failed", "Failed"))
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="ai_usage_logs")
    feature = models.CharField(max_length=100)
    model_name = models.CharField(max_length=150)
    credits_used = models.PositiveIntegerField(default=1)
    input_tokens = models.PositiveIntegerField(default=0)
    output_tokens = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20,choices=status_choices)
    response_time_ms = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.email} - {self.feature}"