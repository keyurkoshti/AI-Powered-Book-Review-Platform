# Book Review App

A simple Book Review web application built using **Python**, **Django**, and **MySQL**. Users can register, log in, submit book reviews, and view reviews submitted by other users. The project also includes REST APIs built with Django REST Framework (DRF), which are called using JavaScript Fetch API.

---

## Technologies Used

- Python
- Django
- Django REST Framework (DRF)
- Celery
- MySQL
- HTML
- CSS
- JavaScript (Fetch API)
- Virtual Environment (venv)

## Features

- User Registration
- User Login
- User Logout
- JWT Authentication
- Book Review Form
- Add Book URL
- Give Rating and Review
- View All Book Reviews
- User Profile
- Protected Pages and APIs
- Profanity Filtering — Blocks inappropriate/abusive language in reviews using `better-profanity`
- Stripe Payment - like subscription to add book for normal user (1,3,6,12 months)
---

## AI-Powered Review Improvement

The application includes an **AI-powered Review Improvement feature** that helps users improve the quality, clarity, and professionalism of their book reviews while preserving the original meaning.

### How It Works

When a user writes a review, they can use the **"Improve with AI"** feature.

```text
User writes review
        ↓
Click "Improve with AI"
        ↓
Django REST API
        ↓
Authentication & Review Ownership Check
        ↓
OpenRouter API
        ↓
AI Model
        ↓
Improved Review
        ↓
Return response to user
```

### 🔧 AI Technology

* **OpenRouter API** – AI model gateway
* **OpenAI Python SDK** – API client
* **Django REST Framework** – AI API endpoint
* **Cookie-based JWT Authentication** – protects the endpoint
* **Environment Variables** – securely stores API credentials

### AI Review Endpoint

```http
POST /api/reviews/improve/
```

Example request:

```json
{
    "review_text": "This book is very good and I like the story because it is interesting."
}
```

Example response:

```json
{
    "improved_review": "This book offers an engaging and compelling story that kept me interested throughout. The well-developed narrative makes it an enjoyable read."
}
```

### Security

The AI endpoint is protected using authentication. Before sending the review to the AI service, the backend verifies that:

* The user is authenticated.
* The review belongs to the requesting user.
* The submitted review meets the required validation rules.
* The API key is stored securely as an environment variable and is not exposed in the source code.

### AI Configuration

The AI request is configured with parameters such as:

* **Temperature** – controls the creativity/randomness of the generated response.
* **Max Tokens** – limits the maximum amount of generated text.
* **Timeout** – prevents the application from waiting indefinitely for the external AI service.

The system prompt instructs the model to behave as a **professional book-review editor** and return only the improved review.

### Design Goal

The feature is designed to **assist the user rather than replace their writing**. The AI improves grammar, clarity, readability, and professional tone while attempting to preserve the original meaning of the user's review.

### Example

**Original Review**

> "This book is very good and I like the story. Some parts are little boring but overall I enjoyed reading it."

**AI Improved Review**

> "This book offers an engaging story that was enjoyable to read overall. Although a few sections felt slightly slow, the compelling narrative made the book a satisfying experience."


## REST APIs

- Register API
- Login API
- Homepage API
- Profile API
- JWT Token Refresh API
- checkoutSession payment API
- Stripe Webhook API
- AI Power Review Improvement

### Create Virtual Environment

```bash
python -m venv venv
```

### Apply Migration to Database
```bash
python manage.py migrate
```

### Run Server

```bash
python manage.py runserver
```

### Stripe Webhook (Local Development)

Stripe needs a way to reach your local server to send payment events (checkout completed, failed, etc.). Since `localhost` isn't publicly reachable, use the Stripe CLI to forward events to your local webhook endpoint.

1. Install the [Stripe CLI](https://stripe.com/docs/stripe-cli) and log in:
```bash
   stripe login
```

2. Start forwarding webhook events to your local server:
```bash
   stripe listen --forward-to localhost:8000/api/payment/webhook/
```

3. Copy the `whsec_...` signing secret printed in the terminal and set it in your `.env`:


### Note 
This secret changes every time you restart `stripe listen`. Keep this terminal running throughout your dev session — if you restart it, update `.env` with the new secret.



## Stripe Payment & Subscription Flow

The platform uses Stripe Checkout for book subscriptions.
Payment activation is handled through Stripe webhooks rather than
trusting the frontend success redirect.

```mermaid
flowchart TD

    A[User submits book + subscription duration] --> B[Django validates form]

    B --> C{Valid duration?}

    C -- No --> D[Show validation error]
    C -- Yes --> E[Create Book]

    E --> F[Create BookSubscription<br/>status = PENDING]

    F --> G[Create Stripe Checkout Session]

    G --> H{Stripe Checkout}

    H -- Payment failed/cancelled --> I[Subscription FAILED]
    I --> J[Book remains unavailable]

    H -- Payment successful --> K[Stripe checkout.session.completed]

    K --> L[Stripe Webhook]

    L --> M[Verify webhook signature]

    M --> N{Event already processed?}

    N -- Yes --> O[Return 200]

    N -- No --> P[Store Stripe event]

    P --> Q[Lock subscription row]

    Q --> R{Payment status = paid?}

    R -- No --> O

    R -- Yes --> S[Calculate subscription period]

    S --> T[start_date = now]

    T --> U[end_date = start_date + N months]

    U --> V[status = ACTIVE]

    V --> W[Store Payment Intent ID]

    W --> X[Book is_available = True]

    X --> O

    O --> Y[Celery Beat checks expired subscriptions]

    Y --> Z{end_date <= now?}

    Z -- No --> Y

    Z -- Yes --> AA[Celery Worker]

    AA --> AB[status = EXPIRED]

    AB --> AC[Book is_available = False]


## 1. Transactional Outbox for Welcome Emails
Added an OutboxEvent to reliably track welcome-email events.
User creation and outbox event creation happen inside the same database transaction.
Registration succeeds even if the email service, Redis, or Celery worker is temporarily unavailable.
Prevents email events from being silently lost.

## 2. Celery Retry & Failure Recovery
Added Celery-based asynchronous email processing.
Failed email tasks can be retried with backoff.
Designed to handle temporary email-service failures and worker interruptions.

## 3. Celery Beat – Outbox Recovery
Added periodic Celery Beat job to check for pending/failed outbox events.
Unprocessed welcome-email events can be re-queued automatically after service recovery.
Provides an additional recovery mechanism beyond normal Celery retries.

## 4. Celery Beat – Subscription Monitoring
Added a periodic background job to check subscription status.
Automatically detects subscriptions whose end_date has passed.
Keeps subscription state synchronized even if an external event/webhook is delayed or missed.
Configured for periodic execution (e.g. every minute; shorter intervals can be used for development/testing).

## 5. Production Failure Testing
Tested failure scenarios including:
Email service unavailable
Celery worker unavailable
Redis unavailable
Background task failure/retry
Pending Outbox event recovery
Subscription expiry/reconciliation