from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction, IntegrityError
from dateutil.relativedelta import relativedelta
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.db.models import Q
from django.utils import timezone
from django.conf import settings
from django.core.paginator import Paginator
from .models import Book_Review_forms,Book,Category,UserProfile,BookSubScription, StripeWebHookEvent
from .forms import RegisterForm,LoginForm,BookForm,user_form, SUBSCRIPTION_PRICES
from .api_views import store_refresh_token,ACCESS_COOKIE_MAX_AGE,REFRESH_COOKIE_MAX_AGE
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
import stripe
import logging


logger = logging.getLogger(__name__)


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



def register_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])
            user.save()
            messages.success(request,"Registration successful. Please login.")

            return redirect("login")

    else:
        form = RegisterForm()

    return render(request,"register.html",{"form": form})


@login_required(login_url="login")
def profile_view(request):

    user = request.user
    reviews_count = Book_Review_forms.objects.filter(user=user).count()
    has_active_subscription = BookSubScription.objects.filter(user=user,status=BookSubScription.STATUS_ACTIVE).exists()

    context = {
        "user": user,
        "reviews_count": reviews_count,
        "has_active_subscription": has_active_subscription,
    }
    print(context)
    return render(request,"profile.html",context)

# ---------------------------------Add New Book(Subscription Required)------------------------------------------
@login_required(login_url="login")
def book_info_view(request):
    if request.method == "GET":
        form = BookForm()

        return render(
            request,
            "book.html",
            {"form": form},
        )

    form = BookForm(request.POST)

    if not form.is_valid():
        return render(
            request,
            "book.html",
            {"form": form},
        )

    category_name = form.cleaned_data["category_name"].strip()
    duration = form.cleaned_data["subscription_duration"]
    # print("DURATION:", duration)
    # print("SUBSCRIPTION_PRICES:", SUBSCRIPTION_PRICES)
    # print("PRICE:", SUBSCRIPTION_PRICES.get(duration))

    price = SUBSCRIPTION_PRICES.get(duration)
    # print("FINAL PRICE:", price)
    # print("STRIPE AMOUNT:", int(price * 100))

    if price is None:
        form.add_error(
            "subscription_duration",
            "Please select a valid subscription duration.",
        )

        return render(
            request,
            "book.html",
            {"form": form},
        )

    try:

        with transaction.atomic():
            category, _ = Category.objects.get_or_create(
                name=category_name
            )

            has_active_subscription = (
                BookSubScription.objects
                .filter(
                    user=request.user,
                    status=BookSubScription.STATUS_ACTIVE,
                    end_date__gt=timezone.now(),
                )
                .exists()
            )

            book = form.save(commit=False)
            book.category = category
            book.added_by = request.user

            if has_active_subscription:
                book.is_available = True
                book.save()
                messages.success(request,"Book added successfully!")
                return redirect("form_view")

            book.is_available = False
            book.save()

            subscription = BookSubScription.objects.create(
                user=request.user,
                book=book,
                subscription_duration=duration,
                price=price,
                status=BookSubScription.STATUS_PENDING,
            )

    except IntegrityError:

        messages.error(request,"Unable to add this book. Please try again.")
        return render(request,"book.html",{"form": form})

    try:

        session = stripe.checkout.Session.create(
            mode="payment",
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "inr",
                        "unit_amount": int(price * 100),
                        "product_data": {
                            "name": f"Subscription: {book.title}",
                        },
                    },
                    "quantity": 1,
                }
            ],
            metadata={
                "subscription_id": str(subscription.id),
                "book_id": str(book.id),
                "user_id": str(request.user.id),
            },
            success_url=(
                request.build_absolute_uri(
                    reverse("payment_success")
                )
                + "?session_id={CHECKOUT_SESSION_ID}"
            ),
            cancel_url=request.build_absolute_uri(
                reverse("payment_cancel")
            ),
            idempotency_key=f"subscription-{subscription.id}",
        )

    except stripe.error.StripeError as e:

        # print("STRIPE ERROR:", repr(e))

        subscription.status = BookSubScription.STATUS_FAILED
        subscription.save(update_fields=["status"])
        messages.error(request,f"Stripe error: {e}")

        return redirect("form_view")

    except Exception as e:

        # print("GENERAL ERROR:", repr(e))

        subscription.status = BookSubScription.STATUS_FAILED
        subscription.save(update_fields=["status"])
        messages.error(request,f"Payment error: {e}")

        return redirect("form_view")
    
    subscription.stripe_checkout_session_id = session.id
    subscription.save(update_fields=["stripe_checkout_session_id"])
    return redirect(session.url)

# ----------------------------------Write Review to A Book----------------------------------------
@login_required(login_url="login")
def review_form_view(request):
    if request.method == "POST":
        form = user_form(request.POST,request.FILES)

        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.save()
            messages.success(request,"Review submitted successfully!")
            return redirect("home")

    else:
        form = user_form()

    return render(request,"book_review_form.html",{"form": form})

# ---------------------------------Payment Checkout Session----------------------------------------
@login_required(login_url="login")
def create_checkout_session_view(request, book_id):
    if request.method != "POST":
        return redirect("book_info")

    duration = request.POST.get("subscription_duration")

    try:
        duration = int(duration)
    except (TypeError, ValueError):
        messages.error(request,"Invalid subscription duration.")
        return redirect("book_info")

    if duration not in SUBSCRIPTION_PRICES:
        messages.error(request,"Invalid subscription duration.")
        return redirect("book_info")

    try:
        with transaction.atomic():
            book = (Book.objects.select_for_update().get(id=book_id))
            already_taken = (BookSubScription.objects.filter(
                    book=book,
                    status__in=[
                        BookSubScription.STATUS_PENDING,
                        BookSubScription.STATUS_ACTIVE,
                    ],
                )
                .exists()
            )

            if already_taken:
                messages.error(request,"This book already has a payment in progress or an active subscription.")
                return redirect("home")

            price = SUBSCRIPTION_PRICES[duration]

            subscription = (
                BookSubScription.objects.create(
                    user=request.user,
                    book=book,
                    subscription_duration=duration,
                    price=price,
                    status=BookSubScription.STATUS_PENDING,
                )
            )

    except Book.DoesNotExist:
        messages.error(request,"Book not found.")
        return redirect("home")

    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "inr",
                        "unit_amount": int(price * 100),
                        "product_data": {
                            "name": (
                                f"Subscription: {book.title}"
                            ),
                        },
                    },
                    "quantity": 1,
                }
            ],

            metadata={
                "subscription_id": str(subscription.id),
                "book_id": str(book.id),
                "user_id": str(request.user.id),
            },

            success_url=(
                "http://localhost:8000/payment/success/"
                "?session_id={CHECKOUT_SESSION_ID}"
            ),

            cancel_url=(
                "http://localhost:8000/payment/cancel/"
            ),

            idempotency_key=(f"subscription-{subscription.id}"),
        )

    except stripe.error.StripeError:
        subscription.status = (BookSubScription.STATUS_FAILED)
        subscription.save(update_fields=["status"])
        messages.error(request,"Could not start payment. Please try again.")
        return redirect("home")

    except Exception:
        subscription.status = (BookSubScription.STATUS_FAILED)
        subscription.save(update_fields=["status"])
        messages.error(request,"Could not start payment.")
        return redirect("home")

    subscription.stripe_checkout_session_id = session.id
    subscription.save(update_fields=["stripe_checkout_session_id"])
    return redirect(session.url)

# -----------------------------stripe webhook-------------------------------

@csrf_exempt
def stripe_webhook(request):
    if request.method != "POST":
        return HttpResponse(status=405)

    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            settings.STRIPE_WEBHOOK_SECRET,
        )

    except ValueError:
        logger.error("Invalid Stripe webhook payload.")
        return HttpResponse(status=400)

    except stripe.error.SignatureVerificationError:
        logger.error("Invalid Stripe webhook signature.")
        return HttpResponse(status=400)

    except Exception:
        logger.exception("Unexpected error verifying Stripe webhook.")
        return HttpResponse(status=400)

    event_id = event["id"]
    event_type = event["type"]

    logger.info("Stripe webhook received: %s - %s",event_id,event_type)

    try:
        with transaction.atomic():
            webhook_event, created = (
                StripeWebHookEvent.objects.get_or_create(
                    event_id=event_id,
                    defaults={
                        "event_type": event_type,
                    },
                )
            )
            if not created:
                logger.info("Stripe event %s already processed.",event_id)
                return HttpResponse(status=200)


            if event_type == "checkout.session.completed":
                session = event["data"]["object"]
                metadata = session.metadata.to_dict() if session.metadata else {}
                subscription_id = metadata.get("subscription_id")
                if not subscription_id:
                    logger.error(
                        "subscription_id missing from Stripe metadata. "
                        "Event: %s",
                        event_id,
                    )
                    return HttpResponse(status=400)
                
                # print(f"subcription id :- {subscription_id}")

                subscription = (
                    BookSubScription.objects
                    .select_for_update()
                    .select_related("book")
                    .get(id=subscription_id)
                )

                if subscription.status == (BookSubScription.STATUS_ACTIVE):
                    logger.info("Subscription %s already active.",subscription.id)
                    return HttpResponse(status=200)

                payment_status = session.payment_status

                if payment_status != "paid":
                    logger.warning(
                        "Checkout session %s completed but "
                        "payment_status=%s",
                        session.get("id"),
                        payment_status,
                    )
                    return HttpResponse(status=200)

                subscription.status = (BookSubScription.STATUS_ACTIVE)
                start_date = timezone.now()
                end_date = start_date + relativedelta(months=subscription.subscription_duration)

                subscription.status = BookSubScription.STATUS_ACTIVE
                subscription.start_date = subscription.start_date
                subscription.end_date = end_date
                payment_intent_id = session.payment_intent

                if payment_intent_id:
                    subscription.stripe_payment_intent_id = (payment_intent_id)

                subscription.save(
                    update_fields=[
                        "status",
                        "start_date",
                        "stripe_payment_intent_id",
                        "updated_at",
                    ]
                )

                book = subscription.book
                book.is_available = True

                book.save(update_fields=["is_available"])

                logger.info(
                    "Subscription %s activated successfully. "
                    "Book %s is now available.",
                    subscription.id,
                    book.id,
                )

            else:
                logger.info("Ignoring Stripe event type: %s",event_type)

    except BookSubScription.DoesNotExist:
        logger.exception(
            "Subscription %s does not exist. Stripe event=%s",
            subscription_id,
            event_id,
        )
        return HttpResponse(status=404)

    except Exception:
        logger.exception(
            "Error processing Stripe event %s (%s)",
            event_id,
            event_type,
        )

        return HttpResponse(status=500)

    return HttpResponse(status=200)

# -----------------------------Payment Success-----------------------------------
@login_required(login_url="login")
def payment_success_view(request):
    session_id = request.GET.get("session_id")
    subscription = None

    if session_id:
        subscription = (BookSubScription.objects.filter(
                stripe_checkout_session_id=session_id,
                user=request.user,
            ).select_related("book").first()
        )

    return render(request,"payment_success.html",
        {
            "subscription": subscription,
        },
    )

# --------------------------Payment Cancel------------------------------------
@login_required(login_url="login")
def payment_cancel_view(request):

    return render(request,"payment_cancel.html")

# -------------------------Logout User----------------------------------
def logout_view(request):
    if request.method != "POST":
        return redirect("home")
    logout(request)

    response = redirect("login")
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")

    return response
