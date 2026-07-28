from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Book_Review_forms, Book, Category

User = get_user_model()


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists")
        return value

    def validate(self, attrs):
        if attrs['password1'] != attrs['password2']:
            raise serializers.ValidationError({
                "password": "Passwords do not match"
            })
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password1']
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


# --------------------------Book List Serializer (for dropdown)---------------------------
class BookListSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField()

    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'category']


# --------------------------Create Review Serializer---------------------------
class CreateReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book_Review_forms
        fields = ['book', 'book_photo', 'book_url', 'rating', 'book_review']

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value


# --------------------------Add Book Serializer---------------------------
class AddBookSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(write_only=True)

    class Meta:
        model = Book
        fields = ['title', 'category', 'category_name', 'author', 'description']
        read_only_fields = ['category']

    def validate_category_name(self, value):
        category, created = Category.objects.get_or_create(name=value.strip())
        return category

    def create(self, validated_data):
        category = validated_data.pop('category_name')
        validated_data['category'] = category
        return super().create(validated_data)
