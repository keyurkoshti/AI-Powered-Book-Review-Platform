import logging

import stripe
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from book_review.forms import SUBSCRIPTION_PRICES
from book_review.models import Book, BookSubScription, Category

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY


def user_has_active_subscription(user) -> bool:
    return BookSubScription.objects.filter(
        user=user,
        status=BookSubScription.STATUS_ACTIVE,
        end_date__gt=timezone.now(),
    ).exists()


def create_book_from_form(user, cleaned_data) -> Book:
    category_name = cleaned_data["category_name"].strip()
    category, _ = Category.objects.get_or_create(
        name=category_name,
        defaults={"added_by": user},
    )
    return Book.objects.create(
        title=cleaned_data["title"].strip(),
        author=cleaned_data["author"].strip(),
        description=cleaned_data["description"],
        category=category,
        added_by=user,
        is_available=True,
    )


def create_book_from_pending(subscription: BookSubScription) -> Book | None:
    title = (subscription.pending_title or "").strip()
    if not title:
        return None

    category_name = (subscription.pending_category_name or "").strip() or "Uncategorized"
    category, _ = Category.objects.get_or_create(name=category_name,defaults={"added_by": subscription.user})
    book = Book.objects.create(
        title=title,
        author=(subscription.pending_author or "").strip() or "Unknown",
        description=subscription.pending_description or "",
        category=category,
        added_by=subscription.user,
        is_available=True,
    )
    subscription.book = book
    subscription.pending_title = ""
    subscription.pending_author = ""
    subscription.pending_category_name = ""
    subscription.pending_description = ""
    subscription.pending_book_url = ""
    subscription.save(
        update_fields=[
            "book",
            "pending_title",
            "pending_author",
            "pending_category_name",
            "pending_description",
            "pending_book_url",
            "updated_at",
        ]
    )
    return book


def start_subscription_checkout(request, user, duration, draft_fields) -> str:
    price = SUBSCRIPTION_PRICES[duration]

    with transaction.atomic():
        BookSubScription.objects.filter(user=user,status=BookSubScription.STATUS_PENDING).update(status=BookSubScription.STATUS_CANCELLED)

        subscription = BookSubScription.objects.create(
            user=user,
            book=None,
            subscription_duration=duration,
            price=price,
            status=BookSubScription.STATUS_PENDING,
            pending_title=draft_fields.get("title", "").strip(),
            pending_author=draft_fields.get("author", "").strip(),
            pending_category_name=draft_fields.get("category_name", "").strip(),
            pending_description=draft_fields.get("description", ""),
            pending_book_url=draft_fields.get("book_url", ""),
        )

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
                            "name": f"{duration}-Month Book Subscription",
                        },
                    },
                    "quantity": 1,
                }
            ],
            metadata={
                "subscription_id": str(subscription.id),
                "user_id": str(user.id),
            },
            success_url=(
                request.build_absolute_uri(reverse("payment_success"))
                + "?session_id={CHECKOUT_SESSION_ID}"
            ),
            cancel_url=request.build_absolute_uri(reverse("payment_cancel")),
            idempotency_key=f"subscription-{subscription.id}",
        )
    except Exception:
        subscription.status = BookSubScription.STATUS_FAILED
        subscription.save(update_fields=["status", "updated_at"])
        raise

    subscription.stripe_checkout_session_id = session.id
    subscription.save(update_fields=["stripe_checkout_session_id", "updated_at"])
    return session.url


def activate_subscription_after_payment(
    subscription: BookSubScription,
    *,
    payment_intent_id=None,
) -> BookSubScription:
    """Activate a paid subscription and create the draft book if needed."""
    if subscription.status == BookSubScription.STATUS_ACTIVE:
        if subscription.book_id is None and (subscription.pending_title or "").strip():
            create_book_from_pending(subscription)
        elif subscription.book_id and not subscription.book.is_available:
            subscription.book.is_available = True
            subscription.book.save(update_fields=["is_available"])
        return subscription

    start_date = timezone.now()
    subscription.status = BookSubScription.STATUS_ACTIVE
    subscription.start_date = start_date
    subscription.end_date = start_date + relativedelta(
        months=subscription.subscription_duration
    )
    if payment_intent_id:
        subscription.stripe_payment_intent_id = payment_intent_id

    subscription.save(
        update_fields=[
            "status",
            "start_date",
            "end_date",
            "stripe_payment_intent_id",
            "updated_at",
        ]
    )

    if subscription.book_id:
        if not subscription.book.is_available:
            subscription.book.is_available = True
            subscription.book.save(update_fields=["is_available"])
    elif (subscription.pending_title or "").strip():
        create_book_from_pending(subscription)

    logger.info("Subscription %s activated successfully.", subscription.id)
    return subscription
