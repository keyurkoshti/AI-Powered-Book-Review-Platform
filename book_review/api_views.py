from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from .serializers import RegisterSerializer, HomepageSerializer, ProfileSerializer, CreateReviewSerializer, AddBookSerializer, BookListSerializer, CategorySerializer
from django.contrib.auth import authenticate, logout, get_user_model
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from django.core.cache import cache
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import UserProfile, Book_Review_forms, Book, Category, RefreshTokenStore, BookSubScription, StripeWebHookEvent
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.utils import timezone
from django.db import transaction, IntegrityError
from dotenv import load_dotenv
from dateutil import relativedelta
import stripe


stripe.api_key = settings.STRIPE_SECRET_KEY
SUBSCRIPTION_PRICES = {1: 1, 3: 1, 6: 1, 12: 1} 

User = get_user_model()

ACCESS_COOKIE_MAX_AGE = int(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds())
REFRESH_COOKIE_MAX_AGE = int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds())


def store_refresh_token(user, refresh_token):
    expires_at = timezone.now() + settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"]
    RefreshTokenStore.objects.update_or_create(
        user=user,
        defaults={
            "refresh_token": refresh_token,
            "expires_at": expires_at,
        }
    )


def get_user_from_refresh_token(refresh_token):
    try:
        store = RefreshTokenStore.objects.get(refresh_token=refresh_token)
    except RefreshTokenStore.DoesNotExist:
        return None

    if not store.is_valid():
        return None

    return store.user


# --------------------Register API------------------------
class RegisterApiview(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        user = serializer.save()

        try:
            email = EmailMultiAlternatives(
                subject="Welcome to Book Review",
                body=f"""
                    Hi {user.user_name},

                    Welcome to Book Review! Your account has been created successfully.

                    Here's what you can do next:

                    1. LOGIN TO YOUR ACCOUNT
                    Go to the login page and enter your credentials:
                    Username: {user.user_name}
                    Password: (the password you created during registration)

                    2. EXPLORE BOOKS
                    Browse reviews from other readers to discover your next great read.

                    3. WRITE A REVIEW
                    Share your thoughts on books you've read and help others make informed choices.

                    4. BUILD YOUR PROFILE
                    Track your reading journey by managing your reviews and profile.

                    Login link: http://localhost:8000/login/

                    Need help? Reply to this email and we'll assist you.

                    Happy reading!
                    The Book Review Team
                    """,
                from_email="Book Review <{}>".format(settings.EMAIL_HOST_USER),
                to=[user.email],
            )

            html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                </head>
                <body style="margin:0; padding:0; background-color:#f4f4f4; font-family:Arial, Helvetica, sans-serif;">
                    <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                        <tr>
                            <td style="padding:40px 20px;">
                                <table role="presentation" cellpadding="0" cellspacing="0" width="600" align="center" style="background-color:#ffffff; border-radius:12px; overflow:hidden; box-shadow:0 4px 15px rgba(0,0,0,0.1);">
                                    <!-- Header -->
                                    <tr>
                                        <td style="background:linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding:30px 40px; text-align:center;">
                                            <h1 style="color:#ffffff; font-size:28px; margin:0;">Welcome to Book Review</h1>
                                        </td>
                                    </tr>
                                    <!-- Body -->
                                    <tr>
                                        <td style="padding:40px;">
                                            <p style="font-size:16px; color:#333333; margin:0 0 10px 0;">Hi <strong>{user.user_name}</strong>,</p>
                                            <p style="font-size:16px; color:#333333; margin:0 0 20px 0;">Welcome to <strong>Book Review</strong>! Your account has been created successfully.</p>

                                            <h3 style="color:#667eea; font-size:18px; margin:30px 0 15px 0;">📚 What's Next?</h3>

                                            <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                                                <tr>
                                                    <td style="padding:12px 0; border-bottom:1px solid #eeeeee;">
                                                        <p style="font-size:15px; color:#333333; margin:0;"><strong>1. Login to Your Account</strong></p>
                                                        <p style="font-size:14px; color:#666666; margin:5px 0 0 0;">Use your username and password to sign in.</p>
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td style="padding:12px 0; border-bottom:1px solid #eeeeee;">
                                                        <p style="font-size:15px; color:#333333; margin:0;"><strong>2. Explore Books</strong></p>
                                                        <p style="font-size:14px; color:#666666; margin:5px 0 0 0;">Browse reviews from other readers and discover new books.</p>
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td style="padding:12px 0; border-bottom:1px solid #eeeeee;">
                                                        <p style="font-size:15px; color:#333333; margin:0;"><strong>3. Write a Review</strong></p>
                                                        <p style="font-size:14px; color:#666666; margin:5px 0 0 0;">Share your thoughts and help others find great reads.</p>
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td style="padding:12px 0;">
                                                        <p style="font-size:15px; color:#333333; margin:0;"><strong>4. Build Your Profile</strong></p>
                                                        <p style="font-size:14px; color:#666666; margin:5px 0 0 0;">Track your reading journey and manage your reviews.</p>
                                                    </td>
                                                </tr>
                                            </table>

                                            <!-- CTA Button -->
                                            <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin:30px 0;">
                                                <tr>
                                                    <td align="center">
                                                        <a href="http://localhost:8000/login/" style="display:inline-block; background:linear-gradient(135deg, #667eea 0%, #764ba2 100%); color:#ffffff; text-decoration:none; font-size:16px; font-weight:bold; padding:14px 40px; border-radius:6px;">Login to Your Account</a>
                                                    </td>
                                                </tr>
                                            </table>

                                            <hr style="border:none; border-top:1px solid #eeeeee; margin:20px 0;">

                                            <p style="font-size:14px; color:#999999; margin:0 0 5px 0;">Need help? Reply to this email and we'll assist you.</p>
                                            <p style="font-size:14px; color:#999999; margin:0;">Happy reading!</p>
                                            <p style="font-size:14px; color:#999999; margin:10px 0 0 0;"><strong>The Book Review Team</strong></p>
                                        </td>
                                    </tr>
                                    <!-- Footer -->
                                    <tr>
                                        <td style="background-color:#f8f8f8; padding:20px 40px; text-align:center;">
                                            <p style="font-size:12px; color:#bbbbbb; margin:0;">You received this email because you registered on Book Review.</p>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                    </table>
                </body>
                </html>
            """
            email.extra_headers = {
                'Reply-To': settings.EMAIL_HOST_USER,
                'X-Mailer': 'Django',
            }
            email.attach_alternative(html, "text/html")
            email.send()
        except Exception:
            pass

    def create(self, request, *args, **kwargs):
        super().create(request, *args, **kwargs)
        return Response(
            {"message": "User created successfully"},
            status=status.HTTP_201_CREATED
        )


# ------------------------Login Api (sets HttpOnly cookies)--------------------------------
class LoginApiview(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email") or request.data.get("username")
        password = request.data.get("password")

        if not email or not password:
            return Response(
                {"error": "Email/Username and Password are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(request=request, email=email, password=password)

        if user is None:
            try:
                user_obj = UserProfile.objects.filter(user_name=email).first()
                if user_obj:
                    user = authenticate(request=request, email=user_obj.email, password=password)
            except Exception:
                pass

        if user is None:
            return Response(
                {"error": "Invalid username/email or password."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        access = AccessToken.for_user(user)
        refresh = RefreshToken.for_user(user)
        access_token = str(access)
        refresh_token = str(refresh)

        store_refresh_token(user, refresh_token)

        response = Response(
            {
                "message": "Login successful.",
                "user": {
                    "id": user.id,
                    "user_name": user.user_name,
                    "email": user.email,
                }
            },
            status=status.HTTP_200_OK
        )

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


# ------------------------Home-page Api--------------------------
class HomepageApiview(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = HomepageSerializer
    queryset = Book_Review_forms.objects.select_related("user", "book").order_by("-id")


# ------------------------Profile-page Api--------------------------
class ProfileAPIView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProfileSerializer

    def get_object(self):
        user = self.request.user
        user.reviews_count = Book_Review_forms.objects.filter(user=user).count()
        return user


# ------------------------Cookie Token Refresh (reads refresh_token from cookie)--------------------------
class CookieTokenRefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')

        if not refresh_token:
            return Response(
                {"error": "Refresh token not found in cookie."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            user = get_user_from_refresh_token(refresh_token)
            if user is None:
                return Response(
                    {"error": "Invalid or expired refresh token."},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            refresh = RefreshToken(refresh_token)
            refresh.blacklist()

            new_refresh = RefreshToken.for_user(user)
            access_token = str(new_refresh.access_token)
            new_refresh_token = str(new_refresh)

            store_refresh_token(user, new_refresh_token)

            response = Response(
                {"message": "Token refreshed successfully."},
                status=status.HTTP_200_OK
            )

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
                value=new_refresh_token,
                httponly=True,
                secure=False,
                samesite='Lax',
                max_age=REFRESH_COOKIE_MAX_AGE
            )

            return response

        except Exception:
            return Response(
                {"error": "Invalid or expired refresh token."},
                status=status.HTTP_401_UNAUTHORIZED
            )


# ------------------------Logout Api (clears cookies + blacklists refresh token)--------------------------
class LogoutAPIView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):    
        refresh_token = request.COOKIES.get('refresh_token')
        if refresh_token:
            try:
                refresh = RefreshToken(refresh_token)
                refresh.blacklist()
            except Exception:
                pass

            RefreshTokenStore.objects.filter(refresh_token=refresh_token).delete()

        logout(request)
        response = Response(
            {"message": "Logged out successfully"},
            status=status.HTTP_200_OK
        )
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        return response


# ------------------------Category List API--------------------------
class CategoryListAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CategorySerializer
    queryset = Category.objects.all()


# ------------------------Book List API (for dropdown)--------------------------
class BookListAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BookListSerializer
    queryset = Book.objects.all().select_related('category')


# ------------------------Create Review API--------------------------
class CreateReviewAPIView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CreateReviewSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        super().create(request, *args, **kwargs)
        return Response(
            {"message": "Review created successfully."},
            status=status.HTTP_201_CREATED
        )


# ------------------------Add Book API (Admin only)--------------------------
class AddBookAPIView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AddBookSerializer

    def perform_create(self, serializer):
        serializer.save(added_by=self.request.user)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return Response(
            {
                "message": "Book added successfully.",
                "book": response.data
            },
            status=status.HTTP_201_CREATED
        )

# -----------------------Stripe Integration----------------------------
class CreateCheckoutSessionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, book_id):
        duration = request.data.get("subscription_duration")

        if duration not in SUBSCRIPTION_PRICES:
            return Response({"error":"enter valid subscription duration"}, status=400)
        

        try:
            with transaction.atomic():
                book = Book.objects.select_for_update().get(id=book_id)
                already_taken = BookSubScription.objects.filter(book=book, status__in=['pending', 'active']).exists()
                if already_taken:
                    return Response({"error":"This book already has a payment in progress or an active subscription."})
                price = SUBSCRIPTION_PRICES[duration]
                subscription = BookSubScription.objects.create(
                    user = request.user,
                    book = book,
                    subscription_duration = duration,
                    price = price,
                    status = BookSubScription.STATUS_PENDING
                )

        except book.DoesNotExist:
            return Response({"error":"book not found"}, status=404)
        except IntegrityError:
            return Response({"error":"This book was just taken by another user."}, status=409)
        
        try:
            session = stripe.checkout.Session.create(
                mode="payment",
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": "inr",
                        "unit_amount": int(price * 100),
                        "product_data": {"name": f"Subscription: {book.title}"},
                    },
                    "quantity": 1,
                }],
                metadata={
                    "subscription_id": str(subscription.id),
                    "book_id": str(book.id),
                    "user_id": str(request.user.id),
                },
                success_url="http://localhost:8000/payment/success?session_id={CHECKOUT_SESSION_ID}",
                cancel_url="http://localhost:8000/payment/cancel",
            )
        except Exception as e:
            subscription.status = BookSubScription.STATUS_FAILED
            subscription.save(update_fields=["status"])
            return Response({"error": "Could not start payment.", "detail": str(e)}, status=502)

        subscription.stripe_checkout_session_id = session.id
        subscription.save(update_fields=["stripe_checkout_session_id"])

        return Response({"checkout_url": session.url}, status=200)
    
class StripeWebhookAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

        try:
            event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
        except (ValueError, stripe.error.SignatureVerificationError):
            return Response(status=400)

        # idempotency
        if StripeWebHookEvent.objects.filter(event_id=event["id"]).exists():
            return Response(status=200)

        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            sub_id = session["metadata"].get("subscription_id")

            with transaction.atomic():
                try:
                    subscription = BookSubScription.objects.select_for_update().get(id=sub_id)
                except BookSubScription.DoesNotExist:
                    subscription = None

                if subscription and subscription.status == BookSubScription.STATUS_PENDING:
                    now = timezone.now()
                    subscription.status = BookSubScription.STATUS_ACTIVE
                    subscription.stripe_payment_intent_id = session.get("payment_intent")
                    subscription.start_date = now
                    subscription.end_date = now + relativedelta(months=subscription.subscription_duration)
                    subscription.save()

                    subscription.book.is_available = True
                    subscription.book.save(update_fields=["is_available"])

        elif event["type"] in ("checkout.session.expired", "payment_intent.payment_failed"):
            session = event["data"]["object"]
            sub_id = session.get("metadata", {}).get("subscription_id")
            if sub_id:
                BookSubScription.objects.filter(
                    id=sub_id, status=BookSubScription.STATUS_PENDING
                ).update(status=BookSubScription.STATUS_FAILED)

        StripeWebHookEvent.objects.create(event_id=event["id"], event_type=event["type"])
        return Response(status=200)