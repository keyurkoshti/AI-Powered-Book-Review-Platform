from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import RegisterSerializer, HomepageSerializer, ProfileSerializer, CreateReviewSerializer, AddBookSerializer, BookListSerializer
from django.contrib.auth import authenticate, logout, get_user_model
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from django.core.cache import cache
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Book_Review_forms, Book, Category, RefreshTokenStore
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.utils import timezone

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
class RegisterApiview(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            email = EmailMultiAlternatives(
            subject="Welcome to Book Review",
            body=f"""
                Hi {user.username},

                Welcome to Book Review! Your account has been created successfully.

                Here's what you can do next:

                1. LOGIN TO YOUR ACCOUNT
                Go to the login page and enter your credentials:
                Username: {user.username}
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
                from_email = "Book Review <{}>".format(settings.EMAIL_HOST_USER),
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
                                            <p style="font-size:16px; color:#333333; margin:0 0 10px 0;">Hi <strong>{user.username}</strong>,</p>
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
            return Response(
                {"message": "User created successfully"},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ------------------------Login Api (sets HttpOnly cookies)--------------------------------
class LoginApiview(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response(
                {"error": "Username and Password are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(username=username, password=password)

        if user is None:
            return Response(
                {"error": "Invalid username or password."},
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
                    "username": user.username,
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
class HomepageApiview(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        reviews = Book_Review_forms.objects.select_related("user", "book").order_by("-id")
        serializer = HomepageSerializer(reviews, many=True)

        return Response(serializer.data)


# ------------------------Profile-page Api--------------------------
class ProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_classes = [None]

    def get(self, request):
        user = request.user
        data = {
            "username": user.username,
            "email": user.email,
            "date_joined": user.date_joined,
            "reviews_count": Book_Review_forms.objects.filter(user=user).count()
        }
        serializer = ProfileSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)


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
class CategoryListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        categories = Category.objects.all()
        data = [{"id": c.id, "name": c.name} for c in categories]
        return Response(data, status=status.HTTP_200_OK)


# ------------------------Book List API (for dropdown)--------------------------
class BookListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        books = Book.objects.all().select_related('category')
        serializer = BookListSerializer(books, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ------------------------Create Review API--------------------------
class CreateReviewAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreateReviewSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(
                {"message": "Review created successfully."},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ------------------------Add Book API (Admin only)--------------------------
class AddBookAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AddBookSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Book added successfully."},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
