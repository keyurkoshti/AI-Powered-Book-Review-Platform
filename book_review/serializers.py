from rest_framework import serializers
from .models import UserProfile, Book_Review_forms, Book, Category
from better_profanity import profanity


class RegisterSerializer(serializers.Serializer):
    user_name = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate_email(self, value):
        if UserProfile.objects.filter(email=value).exists():
            raise serializers.ValidationError("user with this email already exists")
        return value

    def create(self, validated_data):
        return UserProfile.objects.create_user(
            user_name=validated_data['user_name'],
            email=validated_data['email'],
            password=validated_data['password']
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
    user_name = serializers.CharField()
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
    class Meta:
        model = Book_Review_forms
        fields = ['book', 'book_photo', 'book_url', 'rating', 'book_review']

    def validate_book_review(self, value):
        if profanity.contains_profanity(value):
            raise serializers.ValidationError("Review contains inappropriate language. Please remove any offensive words.")
        return value

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value


# --------------------------Add Book Serializer---------------------------
class AddBookSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(write_only=True)

    class Meta:
        model = Book
        fields = [
            'title',
            'category',
            'category_name',
            'author',
            'description',
            'added_by',
        ]

        read_only_fields = [
            'category',
            'added_by',
        ]

    def validate_category_name(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Category name cannot be empty."
            )

        return value

    def create(self, validated_data):
        category = validated_data.pop('category_name')
        user = validated_data.pop('added_by')

        category, created = Category.objects.get_or_create(
            name = category,
            defaults={
                'added_by': user
            }
        )

        validated_data['category'] = category
        validated_data['added_by'] = user

        return super().create(validated_data)


# --------------------------Category Serializer---------------------------
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']