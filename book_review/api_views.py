from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import RegisterSerializer, HomepageSerializer, ProfileSerializer
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, logout
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.cache import cache
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Book_Review_forms
from django.core.mail import send_mail
from django.conf import settings


# --------------------Register API------------------------
class RegisterApiview(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data = request.data)

        if serializer.is_valid():
            user = serializer.save()

            send_mail(
                subject="Welcome",
                message="Your acccount has created successfully",
                from_email = settings.EMAIL_HOST_USER,
                recipient_list=[user.email],
                fail_silently=True
            )
            return Response(
                {"message":"user created successfully"},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

# ------------------------Login Api--------------------------------
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

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "message": "Login successful.",
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh),
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                }
            },
            status=status.HTTP_200_OK
        )

    
# ------------------------Home-page Api--------------------------
class HomepageApiview(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        reviews = Book_Review_forms.objects.select_related("user","book").order_by("-id")
        serializer = HomepageSerializer(reviews, many=True)

        return Response(serializer.data)

# ------------------------Profile-page Api--------------------------
class ProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

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
    


class LogoutAPIView(APIView):

    def post(self, request):
        logout(request)
        return Response(
            {"message": "Logged out successfully"},
            status=status.HTTP_200_OK
        )