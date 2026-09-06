from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from smtplib import SMTPException
from .models import UserProfile


@shared_task(autoretry_for=(SMTPException,), retry_backoff=True, retry_backoff_max=300, retry_jitter=True, max_reties=3)
def send_email_task(user_id):
    user = UserProfile.objects.get(id=user_id)
    subject = "Welcome to Book Review"
    body = f"""
        Hi {user.user_name},

        Welcome to Book Review!

        Your account has been created successfully.

        Login:
        http://localhost:8000/login/

        Happy reading!

        The Book Review Team
        """
    html = f"""
    <html>
        <body>
            <h1>Welcome to Book Review 📚</h1>

            <p>
                Hi <strong>{user.user_name}</strong>,
            </p>

            <p>
                Welcome to Book Review!
                Your account has been created successfully.
            </p>

            <p>
                Start exploring books, writing reviews,
                and building your reading journey.
            </p>

            <a href="http://localhost:8000/login/">
                Login to Your Account
            </a>

            <p>
                Happy reading!
            </p>

            <p>
                <strong>The Book Review Team</strong>
            </p>
        </body>
    </html>
    """

    email = EmailMultiAlternatives(subject=subject, body=body, 
                           from_email=f"Book Review <{settings.EMAIL_HOST_USER}>",
                           to = [user.email])
    email.extra_headers = {
        "Reply-To":settings.EMAIL_HOST_USER,
        "X-Mailer":"Django",
    }
    email.attach_alternative(html, "text/html")

    email.send(fail_silently=False)

    return f"welcome email sent to {user.email}"
