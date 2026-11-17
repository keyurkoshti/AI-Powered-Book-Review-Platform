from django import forms 
from .models import Book_Review_forms, UserProfile, Book, Category
from better_profanity import profanity
from decimal import Decimal

RATING_CHOICES = (
    (1, "⭐"),
    (2, "⭐⭐"),
    (3, "⭐⭐⭐"),
    (4, "⭐⭐⭐⭐"),
    (5, "⭐⭐⭐⭐⭐"),
)

class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))
    
    class Meta:
        model = UserProfile
        fields = ['user_name', 'email', 'password']
        widgets = {
            'user_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data["password"]
        user.set_password(password)

        if commit:
            user.save()
        return user

class LoginForm(forms.Form):
    username_or_email = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username or Email'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))

SUBSCRIPTION_PRICES = {
    1: Decimal("50.00"),
    3: Decimal("249.00"),
    6: Decimal("449.00"),
    12: Decimal("799.00"),
}

class BookForm(forms.ModelForm):

    category_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "e.g. Fiction, Non-Fiction",
            }
        ),
    )

    subscription_duration = forms.TypedChoiceField(
        choices=[(key,f"{key} Month" if key == 1 else f"{key} Months")
            for key in SUBSCRIPTION_PRICES
        ],
        coerce=int,
        widget=forms.Select(
            attrs={
                "class": "form-control",
            }
        ),
        label="Subscription Duration",
        required=False,
    )

    class Meta:
        model = Book

        fields = [
            "title",
            "category_name",
            "author",
            "description",
            "subscription_duration",
        ]

        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter book title",
                }
            ),
            "author": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter author name",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Enter book description",
                }
            ),
        }

    def __init__(self, *args, require_subscription=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.require_subscription = require_subscription
        self.fields["subscription_duration"].required = require_subscription
        if not require_subscription:
            self.fields["subscription_duration"].widget = forms.HiddenInput()

    def clean_subscription_duration(self):
        duration = self.cleaned_data.get("subscription_duration")
        if self.require_subscription and duration not in SUBSCRIPTION_PRICES:
            raise forms.ValidationError("Please select a valid subscription duration.")
        return duration

    def clean_title(self):
        title = self.cleaned_data["title"].strip()
        if Book.objects.filter(title__iexact=title).exists():
            raise forms.ValidationError("A book with this title already exists.")
        return title

class user_form(forms.ModelForm):
    rating = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True
        )
    
    class Meta:
        model=Book_Review_forms
        fields=['book','book_photo','book_url','book_review','rating']
        widgets = {
            "book": forms.Select(
                attrs={
                'class': 'form-control'
            }
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['book'].empty_label = "Select Book..."

    def clean_book_review(self):
        review = self.cleaned_data['book_review']
        if profanity.contains_profanity(review):
            raise forms.ValidationError("Review contains inappropriate language. Please remove any offensive words.")
        return review

    def clean_rating(self):
        rating = int(self.cleaned_data['rating'])
        if rating < 1 or rating > 5:
            raise forms.ValidationError("Rating must be between 1 and 5.")
        return rating
