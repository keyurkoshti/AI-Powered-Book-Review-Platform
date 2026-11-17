from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction, IntegrityError
from dateutil.relativedelta import relativedelta
from django.http import HttpResponse, JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.db.models import Q
from django.utils import timezone
from django.conf import settings
from django.core.paginator import Paginator
from .models import Book_Review_forms, OutboxEvent, Book,Category,UserProfile, BookSubScription, StripeWebHookEvent
from .forms import RegisterForm,LoginForm,BookForm,user_form, SUBSCRIPTION_PRICES
from .api_views import store_refresh_token,ACCESS_COOKIE_MAX_AGE,REFRESH_COOKIE_MAX_AGE
from .services.subscription import user_has_active_subscription, create_book_from_form, start_subscription_checkout, activate_subscription_after_payment
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from book_review.ai_review_service import AIReviewService
import json
import stripe
import logging


logger = logging.getLogger(__name__)

ACCESS_COOKIE_MAX_AGE = int(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds())
REFRESH_COOKIE_MAX_AGE = int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds())

def set_jwt_cookies(response, user):
    access = AccessToken.for_user(user)
    refresh = RefreshToken.for_user(user)

    access_token = str(access)
    refresh_token = str(refresh)

    store_refresh_token(user, refresh_token)

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,       
        samesite="Lax",
        max_age=ACCESS_COOKIE_MAX_AGE,
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,      
        samesite="Lax",
        max_age=REFRESH_COOKIE_MAX_AGE,
    )

    return response

# ----------------------------Register View--------------------------------------
def register_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            with transaction.atomic():
                user = form.save()
                OutboxEvent.objects.create(event_type="WELCOME_EMAIL",payload={"user_id": user.id})

            # Django session authentication
            login(request, user)
            response = redirect("home")
            set_jwt_cookies(response, user)
            messages.success(request,"Welcome To Book Review App.")
            return response

    else:
        form = RegisterForm()

    return render(request,"register.html",{"form": form})

# -----------------------------Login View--------------------------------
def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)

        if form.is_valid():
            username_or_email = form.cleaned_data["username_or_email"]
            password = form.cleaned_data["password"]

            user = authenticate(request=request,email=username_or_email,password=password)

            if user is None:
                user_obj = (UserProfile.objects.filter(user_name=username_or_email).first())

                if user_obj:
                    user = authenticate(
                        request=request,
                        email=user_obj.email,
                        password=password,
                    )

            if user is not None:
                login(request, user)
                response = redirect("home")

                return set_jwt_cookies(response, user)
            
            messages.error(request,"Invalid username/email or password.")

    else:
        form = LoginForm()

    return render(request,"login.html",{"form": form})

# -------------------------------------Home View------------------------------------------
@login_required(login_url="login")
def home_view(request):
    reviews = (
        Book_Review_forms.objects
        .select_related("user", "book", "book__category")
        .order_by("-id")
    )

    search = request.GET.get("search", "").strip()

    if search:
        reviews = reviews.filter(
            Q(book__title__icontains=search)
            | Q(book__author__icontains=search)
            | Q(book__category__name__icontains=search)
        )

    paginator = Paginator(reviews, 4)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "reviews": page_obj,
        "search": search,
        "page_obj": page_obj,
    }

    return render(request, "home.html", context)

# -----------------------------------Profile View----------------------------------------
@login_required(login_url="login")
def profile_view(request):

    user = request.user
    reviews_count = Book_Review_forms.objects.filter(user=user).count()
    has_active_subscription = user_has_active_subscription(user)

    context = {
        "user": user,
        "reviews_count": reviews_count,
        "has_active_subscription": has_active_subscription,
    }

    return render(request,"profile.html",context)

# ---------------------------------Add New Book(Subscription Required)------------------------------------------

# ----------------------------------Write Review to A Book----------------------------------------
@login_required(login_url="login")
def review_form_view(request):
    if request.method == "GET":
        form = user_form()
        return render(request, 'book_review_form.html', {"form":form})
    
    action = request.POST.get("action")
    if action == "improve":
        form = user_form(request.POST, request.FILES)
        if not form.is_valid():
            return render(request,"book_review_form.html",{"form": form})
        
        review_text = form.cleaned_data["book_review"]
        if not review_text.strip():
            form.add_error("book_review Please write a review before improving it.")
            return render(request,"book_review_form.html",{"form": form})
        
        try:
            improved_review = AIReviewService.improve_review(review_text)

        except Exception:
            logger.exception("AI review improvement failed for user_id=%s",request.user.id)
            form.add_error("book_review","Unable to improve the review right now.")
            return render(request,"book_review_form.html",{"form": form})

        form.data = form.data.copy()
        form.data['book_review'] = improved_review

        form = user_form(form.data,request.FILES)
        messages.success(request,"AI improved your review. Please review it before saving.")

        return render(request,"book_review_form.html",{"form": form})
    
    if action == "save":
        form = user_form(request.POST,request.FILES)

        if not form.is_valid():
            return render(request,"book_review_form.html",{"form": form})
        
        review = form.save(commit=False)
        review.user = request.user
        review.save()

        messages.success(request,"Review submitted successfully!")
        return redirect("home")

    form = user_form(request.POST,request.FILES)
    form.add_error(None,"Invalid form submission.")
    return render(request,"book_review_form.html",{"form": form})

# -----------------------------Payment Success-----------------------------------
@login_required(login_url="login")
def payment_success_view(request):
    session_id = request.GET.get("session_id")
    subscription = None

    if session_id:
        subscription = (
            BookSubScription.objects.filter(
                stripe_checkout_session_id=session_id,
                user=request.user,
            )
            .select_related("book")
            .first()
        )

        if subscription and subscription.status == BookSubScription.STATUS_PENDING:
            try:
                session = stripe.checkout.Session.retrieve(session_id)
                if session.payment_status == "paid":
                    with transaction.atomic():
                        subscription = (
                            BookSubScription.objects.select_for_update()
                            .select_related("book")
                            .get(id=subscription.id)
                        )
                        activate_subscription_after_payment(
                            subscription,
                            payment_intent_id=session.payment_intent,
                        )
                        subscription.refresh_from_db()
            except Exception:
                logger.exception(
                    "Failed to reconcile payment for session %s",
                    session_id,
                )

    return render(
        request,
        "payment_success.html",
        {
            "subscription": subscription,
        },
    )

# --------------------------Payment Cancel------------------------------------
@login_required(login_url="login")
def payment_cancel_view(request):
    BookSubScription.objects.filter(
        user=request.user,
        status=BookSubScription.STATUS_PENDING,
    ).update(status=BookSubScription.STATUS_CANCELLED)
    return render(request, "payment_cancel.html")

# -------------------------Logout User----------------------------------
def logout_view(request):
    if request.method != "POST":
        return redirect("home")
    logout(request)

    response = redirect("login")
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")

    return response
