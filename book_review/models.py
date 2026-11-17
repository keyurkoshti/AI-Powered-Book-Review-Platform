from django.db import models 
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone 
from django.core.validators import MinValueValidator, MaxValueValidator
import time
import uuid
# Create your models here.


class UserProfileManager(BaseUserManager):

    def create_user(self, email, user_name, password, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        if not password:
            raise ValueError("Password is required")

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
    
# ---------------------------------Book Subscription Model--------------------------------------
class BookSubScription(models.Model):

    STATUS_PENDING = "pending"
    STATUS_ACTIVE = "active"
    STATUS_EXPIRED = "expired"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_ACTIVE, "Active"),
        (STATUS_EXPIRED, "Expired"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    SUBSCRIPTION_CHOICES = [
        (1, "1 month"),
        (3, "3 months"),
        (6, "6 months"),
        (12, "12 months"),
    ]

    user = models.ForeignKey(UserProfile,on_delete=models.PROTECT,related_name="subscriptions")
    book = models.ForeignKey(Book,on_delete=models.PROTECT,null=True,blank=True,related_name="subscribed")

    # Internal MySQL uniqueness guards.
    pending_draft_user = models.OneToOneField(UserProfile,on_delete=models.PROTECT,null=True,blank=True,related_name="+")
    reserved_book = models.OneToOneField(Book,on_delete=models.PROTECT,null=True,blank=True,related_name="+")

    # Draft book information.
    pending_title = models.CharField(max_length=255, blank=True)
    pending_author = models.CharField(max_length=255, blank=True)
    pending_category_name = models.CharField(max_length=255, blank=True)
    pending_description = models.TextField(blank=True)
    pending_book_url = models.URLField(blank=True)

    subscription_duration = models.PositiveIntegerField(choices=SUBSCRIPTION_CHOICES)

    price = models.DecimalField(max_digits=10,decimal_places=2)
    currency = models.CharField(max_length=3,default="INR")

    status = models.CharField(max_length=20,choices=STATUS_CHOICES,default=STATUS_PENDING,db_index=True)

    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(
                fields=["user", "status"],
                name="subscription_user_status_idx",
            ),
        ]

    def is_active(self):
        return (
            self.status == self.STATUS_ACTIVE
            and self.end_date is not None
            and self.end_date > timezone.now()
        )

    def __str__(self):
        return f"Subscription {self.pk} - {self.status}"


# ---------------------------------------Payment Model-------------------------------------------
class Payment(models.Model):

    STATUS_PENDING = "pending"
    STATUS_PROCESSING = "processing"
    STATUS_SUCCEEDED = "succeeded"
    STATUS_FAILED = "failed"
    STATUS_CANCELLED = "cancelled"
    STATUS_EXPIRED = "expired"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PROCESSING, "Processing"),
        (STATUS_SUCCEEDED, "Succeeded"),
        (STATUS_FAILED, "Failed"),
        (STATUS_CANCELLED, "Cancelled"),
        (STATUS_EXPIRED, "Expired"),
    ]

    PROVIDER_STRIPE = "stripe"

    PROVIDER_CHOICES = [(PROVIDER_STRIPE, "Stripe")]

    subscription = models.ForeignKey(BookSubScription,on_delete=models.PROTECT,related_name="payments")
    provider = models.CharField(max_length=20,choices=PROVIDER_CHOICES,default=PROVIDER_STRIPE)
    amount = models.DecimalField(max_digits=10,decimal_places=2)
    currency = models.CharField(max_length=3,default="INR")
    status = models.CharField(max_length=20,choices=STATUS_CHOICES,default=STATUS_PENDING,db_index=True)
    stripe_checkout_session_id = models.CharField(max_length=255,unique=True,null=True,blank=True)
    stripe_payment_intent_id = models.CharField(max_length=255,unique=True,null=True,blank=True)

    # Unique key for one logical Stripe API operation.
    idempotency_key = models.CharField(max_length=255,unique=True,default=uuid.uuid4,editable=False)
    attempt_number = models.PositiveIntegerField()

    # Database-level protection against multiple successful payments.
    successful_subscription = models.OneToOneField(BookSubScription,on_delete=models.PROTECT,null=True,blank=True,related_name="+")

    failure_code = models.CharField(max_length=100,blank=True)
    failure_message = models.TextField(blank=True)

    paid_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["subscription", "attempt_number"],
                name="unique_subscription_payment_attempt",
            ),
        ]

        indexes = [
            models.Index(
                fields=["subscription", "status"],
                name="payment_subscription_status_idx",
            ),
        ]

    def __str__(self):
        return (
            f"Payment {self.pk} | "
            f"{self.amount} {self.currency} | "
            f"{self.status}"
        )

# ------------------------------------------Stripe Webhook Event Model--------------------------------------------
class StripeWebHookEvent(models.Model):

    STATUS_RECEIVED = "received"
    STATUS_PROCESSING = "processing"
    STATUS_PROCESSED = "processed"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = [
        (STATUS_RECEIVED, "Received"),
        (STATUS_PROCESSING, "Processing"),
        (STATUS_PROCESSED, "Processed"),
        (STATUS_FAILED, "Failed"),
    ]

    event_id = models.CharField(max_length=255,unique=True)
    event_type = models.CharField(max_length=150)

    payment = models.ForeignKey(Payment,on_delete=models.SET_NULL,null=True,blank=True,related_name="webhook_events")
    processing_status = models.CharField(max_length=20,choices=STATUS_CHOICES,default=STATUS_RECEIVED,db_index=True)

    attempt_count = models.PositiveIntegerField(default=0)
    last_error = models.TextField(blank=True)

    event_created_at = models.DateTimeField(null=True,blank=True,)
    processed_at = models.DateTimeField(null=True,blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.event_id} - {self.processing_status}"