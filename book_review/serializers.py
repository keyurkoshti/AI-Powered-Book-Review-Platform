from rest_framework import serializers
from .models import UserProfile, Book_Review_forms, Book, Category
from better_profanity import profanity
from rest_framework.validators import UniqueValidator, ValidationError
from django.contrib.auth import authenticate

# --------------------------Register Serializer---------------------------
class RegisterSerializer(serializers.Serializer):
    user_name = serializers.CharField(max_length=100, required=True)
    email = serializers.EmailField(validators=[UniqueValidator(queryset=UserProfile.objects.all(), message="User with this email already exsits !")])
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user_name = attrs.get('user_name')
        if not user_name:
            raise serializers.ValidationError({"user_name": "Username is required."})
        attrs['user_name'] = user_name
        return attrs

    def create(self, validated_data):
        user_name = validated_data.get('user_name')
        email = validated_data['email']
        password = validated_data['password']
        return UserProfile.objects.create_user(
            user_name=user_name,
            email=email,
            password=password
        )

# -------------------------Login Serializer-----------------------------
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only = True)

    def validate(self, data):
        user = authenticate(username = data.get('email'), password = data.get('password'))
        if not user:
            raise serializers.ValidationError('invalid email or password')
        return user

# --------------------------Home-page Serializer---------------------------
class HomepageSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    book = serializers.SerializerMethodField()
    book_title = serializers.CharField(source='book.title', read_only=True)
    author = serializers.CharField(source='book.author', read_only=True)

    class Meta:
        model = Book_Review_forms
        fields = [
            'id',
            'user',
            'book',
            'book_title',
            'author',
            'rating',
            'book_review',
            'book_photo',
            'book_url',
            'created_at'
        ]

    def get_user(self, obj):
        return obj.user.user_name if obj.user else "Anonymous"

    def get_book(self, obj):
        return obj.book.title if obj.book else "Unknown Book"


# --------------------------Profile Serializer---------------------------
class ProfileSerializer(serializers.Serializer):
    user_name = serializers.CharField()
    username = serializers.CharField(source='user_name', read_only=True)
    email = serializers.EmailField()
    date_joined = serializers.DateTimeField()
    reviews_count = serializers.IntegerField()


# --------------------------Book List Serializer (for dropdown)---------------------------
class BookListSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField()

    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'category', 'description']


# --------------------------Create Review Serializer---------------------------
class CreateReviewSerializer(serializers.ModelSerializer):
    book_photo = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Book_Review_forms
        fields = ['book', 'book_photo', 'book_url', 'rating', 'book_review']

    def validate_book_review(self, value):
        if profanity.contains_profanity(value):
            raise serializers.ValidationError("Review contains inappropriate language. Please remove any offensive words.")
        return value

    def validate_rating(self, value):
        if value is not None and (value < 1 or value > 5):
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value


# --------------------------Add Book Serializer---------------------------
class AddBookSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(write_only=True)

    class Meta:
        model = Book
        fields = [
            'id',
            'title',
            'category',
            'category_name',
            'author',
            'description',
            'added_by',
        ]
        read_only_fields = [
            'id',
            'category',
            'added_by',
        ]

    def validate_category_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Category name cannot be empty.")
        return value

    def create(self, validated_data):
        category_name = validated_data.pop('category_name')
        user = validated_data.pop('added_by', None)

        category, _ = Category.objects.get_or_create(
            name=category_name,
            defaults={'added_by': user}
        )

        validated_data['category'] = category
        if user:
            validated_data['added_by'] = user

        return super().create(validated_data)


# --------------------------Category Serializer---------------------------
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']


# --------------------------Ai Geenrated Review Serializer---------------------------------
class ReviewImproveSerializer(serializers.Serializer):
    review_text = serializers.CharField(min_length=10, max_length=2000, trim_whitespace=True)

    def validate_review_text(self, value):
        if not value.strip():
            raise serializers.ValidationError("review text can not be empty")
        return value
    

