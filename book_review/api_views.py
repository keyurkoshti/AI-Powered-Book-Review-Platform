from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from rest_framework.throttling import AnonRateThrottle
from rest_framework.pagination import PageNumberPagination
from .serializers import RegisterSerializer, LoginSerializer, HomepageSerializer, ProfileSerializer, CreateReviewSerializer, AddBookSerializer, BookListSerializer, CategorySerializer, ReviewImproveSerializer
from django.contrib.auth import authenticate, logout, get_user_model
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from .authentication import CookieJWTAuthentication
from django.core.cache import cache
from django.db.models import Q
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import UserProfile, Book_Review_forms, Book, Category, RefreshTokenStore, BookSubScription, StripeWebHookEvent, UserAiCredit, AiUsageLog
from django.conf import settings
from django.utils import timezone
from django.db import transaction, IntegrityError
from dotenv import load_dotenv
from dateutil import relativedelta
from .tasks import send_email_task
from project_3.celery import app as celery_app
from redis import Redis
from openai import OpenAI
import stripe
import threading
import json
import time
import os

# golbal redis connection pool
redis_client = Redis(host='127.0.0.1', port=6379, db=0)


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

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            user = serializer.save()
            transaction.on_commit(lambda: send_email_task.delay(user.id))
        
        # 4. Return response instantly back to the client
        return Response(
            {"message": "User created successfully"},
            status=status.HTTP_201_CREATED
        )


# ------------------------Login Api (sets HttpOnly cookies)--------------------------------
class LoginRateLimit(AnonRateThrottle):
    scope = "login_limit"

class LoginApiview(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [LoginRateLimit]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data

        access = AccessToken.for_user(user)
        refresh = RefreshToken.for_user(user)
        access_token = str(access)
        refresh_token = str(refresh)

        with transaction.atomic():
            transaction.on_commit(lambda: store_refresh_token(user, refresh_token))

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
class HomePagePagination(PageNumberPagination):
    page_size = 10
    max_page_size = 50
    page_query_param = "page"

class HomepageApiview(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    serializer_class = HomepageSerializer
    pagination_class = HomePagePagination
    
    def get_queryset(self):
        queryset = Book_Review_forms.objects.select_related("user", "book").order_by("-id")
        search = self.request.query_params.get("search")

        if search:
            queryset = queryset.filter(
                Q(book__title__icontains=search) | 
                Q(book__category__name__icontains=search) |
                Q(book__author__icontains=search)
            )

        return queryset


# ------------------------Profile-page Api--------------------------
class ProfileAPIView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]
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
    authentication_classes = [CookieJWTAuthentication]
    serializer_class = CategorySerializer
    queryset = Category.objects.all()


# ------------------------Book List API (for dropdown)--------------------------
class BookListAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]
    serializer_class = BookListSerializer
    queryset = Book.objects.all().select_related('category')


# ------------------------Create Review API--------------------------
class CreateReviewAPIView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]
    serializer_class = CreateReviewSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        super().create(request, *args, **kwargs)
        return Response(
            {"message": "Review created successfully."},
            status=status.HTTP_201_CREATED
        )


# ------------------------Add Book API--------------------------------
class AddBookAPIView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]
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
    authentication_classes = [CookieJWTAuthentication]

    def post(self, request, book_id):
        duration = request.data.get("subscription_duration")

        if duration not in SUBSCRIPTION_PRICES:
            return Response({"error":"enter valid subscription duration"}, status=400)
        

        try:
            with transaction.atomic():
                book = Book.objects.select_for_update().get(id=book_id)

                already_taken = BookSubScription.objects.filter(book=book, status__in=[BookSubScription.STATUS_PENDING, BookSubScription.STATUS_ACTIVE]).exists()
                if already_taken:
                    return Response({"error":"This book already has a payment in progress or an active subscription."},
                                    status=status.HTTP_409_CONFLICT)
                price = SUBSCRIPTION_PRICES[duration]
                subscription = BookSubScription.objects.create(
                    user = request.user,
                    book = book,
                    subscription_duration = duration,
                    price = price,
                    status = BookSubScription.STATUS_PENDING
                )

        except Book.DoesNotExist:
            return Response({"error":"book not found"}, status=status.HTTP_404_NOT_FOUND)
        except IntegrityError:
            return Response({"error":"This book was just taken by another user."}, status=status.HTTP_409_CONFLICT)
        
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
                idempotency_key=f"subscription-{subscription.id}",
            )

        except stripe.error.StripeError:
            subscription.status = BookSubScription.STATUS_FAILED
            subscription.save(update_fields=['status'])
            return Response({"error": "Could not start payment. Please try again."}, status=status.HTTP_502_BAD_GATEWAY)
        
        except Exception:
            subscription.status = BookSubScription.STATUS_FAILED
            subscription.save(update_fields=["status"])
            return Response({"error": "Could not start payment."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        subscription.stripe_checkout_session_id = session.id
        subscription.save(update_fields=["stripe_checkout_session_id"])

        return Response(
            {"checkout_url": session.url,
             "subscription_id": subscription.id}, 
            status=status.HTTP_200_OK) 

class StripeWebhookAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

        try:
            event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
        except ValueError:
            return Response(
                {"error":"invalid payload"},
                status = status.HTTP_400_BAD_REQUEST
            )
        except stripe.SignatureVerificationError:
            return Response(
                {"error":"invalid signature"},
                status = status.HTTP_400_BAD_REQUEST
            )

        event_id = event["id"]
        event_type = event["type"]

        # idempotency
        if StripeWebHookEvent.objects.filter(event_id=event_id).exists():
            return Response(
                {"message": "Event already processed."},
                status=status.HTTP_200_OK)

        try:
            with transaction.atomic():
                if event_type == "checkout.session.completed":
                    session = event["data"]["object"]
                    sub_id = session["metadata"].get("subscription_id")

                    if not sub_id:
                        return Response(
                            {"error": "Invalid event data."},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                    subscription = BookSubScription.objects.select_for_update().filter(id=sub_id).first()

                    if not subscription:
                        return Response(
                            {"error": "Subscription not found."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        )

                    if subscription.status == BookSubScription.STATUS_PENDING:
                        now = timezone.now()
                        subscription.status = BookSubScription.STATUS_ACTIVE
                        subscription.stripe_payment_intent_id = session.get("payment_intent")
                        subscription.start_date = now
                        subscription.end_date = now + relativedelta(months=subscription.subscription_duration)
                        subscription.save()

                        book = Book.objects.select_for_update().get(id=subscription.book_id)

                        book.is_available = True
                        book.save(update_fields=["is_available"])

                elif event_type == "checkout.session.expired":
                    session = event["data"]["object"]
                    sub_id = session.get("metadata", {}).get("subscription_id")
                    if sub_id:
                        BookSubScription.objects.filter(
                            id=sub_id, status=BookSubScription.STATUS_PENDING
                        ).update(status=BookSubScription.STATUS_FAILED)

                elif event_type == "payment_intent.payment_failed":
                    payment_intent = event["data"]["object"]
                    sub_id = payment_intent.get("metadata", {}).get("subscription_id")
                    if sub_id:
                        BookSubScription.objects.filter(
                            id=sub_id, status=BookSubScription.STATUS_PENDING
                        ).update(status=BookSubScription.STATUS_FAILED)
                
                StripeWebHookEvent.objects.create(event_id=event_id, event_type=event_type)

        except IntegrityError:
            if StripeWebHookEvent.objects.filter(event_id=event_id).exists():
                return Response(
                    {"message":"event already processed"},
                    status=status.HTTP_200_OK
                )
            return Response(
                {"error": "temporary processing failure."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        except Exception:
            return Response(
                {"error": "temporary processing failure."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return Response(
            {"message":"webhook processed successfully"},
            status=status.HTTP_200_OK)


FEATURE_REVIEW_IMPROVEMENT = "review_improvement"
AI_MODEL_NAME = "nvidia/nemotron-3-ultra-550b-a55b:free"

class AiReviewAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]
    serializer_class = ReviewImproveSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review_text = serializer.validated_data["review_text"]

        try:
            with transaction.atomic():
                credit = UserAiCredit.objects.select_for_update().get(user=request.user)
                if credit.remaining_credits <= 0:
                    return Response(
                        {
                            "success": False,
                            "detail": "AI credits exhausted.",
                            "remaining_credits": 0,
                        },
                        status=status.HTTP_429_TOO_MANY_REQUESTS,
                    )
                credit.remaining_credits -= 1
                credit.total_used_credits += 1
                credit.save(update_fields=["remaining_credits", "total_used_credits", "updated_at"])
                remaining_credits = credit.remaining_credits
        except UserAiCredit.DoesNotExist:
            return Response(
                {"success": False, 
                 "detail": "AI credit account not found"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        start_time = time.monotonic()
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY is not configured")

            client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=api_key,
                timeout=15.0,
            )

            response = client.chat.completions.create(
                model=AI_MODEL_NAME,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a professional book review editor. "
                            "Improve the user's review while preserving "
                            "their original meaning, opinion, and personal voice. "
                            "Fix grammar, spelling, clarity, and sentence structure. "
                            "Do not add new facts or opinions. "
                            "Keep the review approximately the same length. "
                            "Return only the improved review."
                        ),
                    },
                    {"role": "user", "content": review_text},
                ],
                temperature=0.3,
                max_tokens=300,
            )

            response_time_ms = int((time.monotonic() - start_time) * 1000)
            improved_review = response.choices[0].message.content.strip()

            AiUsageLog.objects.create(
                user=request.user,
                feature=FEATURE_REVIEW_IMPROVEMENT,
                model_name=AI_MODEL_NAME,
                credits_used=1,
                input_tokens=getattr(response.usage, "prompt_tokens", 0) if response.usage else 0,
                output_tokens=getattr(response.usage, "completion_tokens", 0) if response.usage else 0,
                status="success",
                response_time_ms=response_time_ms,
            )

            return Response(
                {
                    "success": True,
                    "original_review": review_text,
                    "improved_review": improved_review,
                    "ai_credits": {"remaining": remaining_credits},
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            response_time_ms = int((time.monotonic() - start_time) * 1000)

            try:
                with transaction.atomic():
                    credit = UserAiCredit.objects.select_for_update().get(user=request.user)
                    credit.remaining_credits += 1
                    credit.total_used_credits -= 1
                    credit.save(update_fields=["remaining_credits", "total_used_credits", "updated_at"])
                    remaining_credits = credit.remaining_credits

                AiUsageLog.objects.create(
                    user=request.user,
                    feature=FEATURE_REVIEW_IMPROVEMENT,
                    model_name=AI_MODEL_NAME,
                    credits_used=0,
                    status="failed",
                    response_time_ms=response_time_ms,
                )
            except UserAiCredit.DoesNotExist:
                remaining_credits = None

            return Response(
                {
                    "success": False,
                    "detail": "unable to improve review right now.",
                    "ai_credits": {"remaining": remaining_credits},
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )