from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Book_Review_forms

User = get_user_model()


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length = 100)
    email = serializers.EmailField()
    password1 = serializers.CharField(write_only = True)
    password2 = serializers.CharField(write_only = True)

    def validate_username(self, value):
        if User.objects.filter(username = value).exists():
            raise serializers.ValidationError("usernmae already exists")
        return value
    
    def validate_password(self, attrs):
        if attrs['password1'] != attrs['password2']:
            raise serializers.ValidationError({
                "password": "password does not match"
            })
        return attrs
    
    def create(self, validated_data):
        return User.objects.create_user(
            username = validated_data['username'],
            email = validated_data['email'],
            password = validated_data['password1']
        )
    
    
# --------------------------Home-page Serializer---------------------------
class HomepageSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    book = serializers.StringRelatedField()

    class Meta:
        model = Book_Review_forms
        fields = [
            'id',
            'user',
            'book',
            'rating',
            'book_review',
            'book_photo',
            'book_url',
            'created_at'
        ]

class ProfileSerializer(serializers.Serializer):
    username = serializers.CharField()
    email = serializers.EmailField()
    date_joined = serializers.DateTimeField()
    reviews_count = serializers.IntegerField()