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

---

## Features

- User Registration
- User Login
- User Logout
- JWT Authentication
- Book Review Form using Django Forms
- Upload Book Image
- Add Book URL
- Give Rating and Review
- View All Book Reviews
- User Profile
- Protected Pages and APIs

---

## Project Flow

1. Register a new account.
2. Login using your credentials.
3. View all book reviews on the homepage.
4. Submit a book review.
5. View your profile.

---

## REST APIs

- Register API
- Login API
- Homepage API
- Profile API
- JWT Token Refresh API

All APIs are called using **JavaScript Fetch API**.

---

## Database

MySQL is used to store:

- Users
- Books
- Categories
- Book Reviews

---

## Project Setup

### Clone Repository

```bash
git clone <repository-url>
```

### Create Virtual Environment

```bash
python -m venv env
```

### Activate Virtual Environment

**Windows**

```bash
env\Scripts\activate
```

### Apply Migrations

```bash
python manage.py migrate
```

### Run Server

```bash
python manage.py runserver
```

---

## Author

**Keyur Koshti**
