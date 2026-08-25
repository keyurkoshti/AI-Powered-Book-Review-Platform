# 📚 Book Review App

A simple Book Review web application built using **Python**, **Django**, and **MySQL**. Users can register, log in, submit book reviews, and view reviews submitted by other users. The project also includes REST APIs built with Django REST Framework (DRF), which are called using JavaScript Fetch API.

---

## Technologies Used

- Python
- Django
- Django REST Framework (DRF)
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

## REST APIs

- Register API
- Login API
- Homepage API
- Profile API
- JWT Token Refresh API
- checkoutSession payment API
- Stripe Webhook API

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