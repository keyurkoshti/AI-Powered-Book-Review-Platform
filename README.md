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

---

## REST APIs

- Register API
- Login API
- Homepage API
- Profile API
- JWT Token Refresh API

### Create Virtual Environment

```bash
python -m venv env
```

### Apply Migration to Database
```bash
python manage.py migrate
```

### Run Server

```bash
python manage.py runserver
```
