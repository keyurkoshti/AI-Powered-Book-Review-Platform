from django import forms 
from .models import Book_Review_forms

RATING_CHOICES = (
    (1, "⭐"),
    (2, "⭐⭐"),
    (3, "⭐⭐⭐"),
    (4, "⭐⭐⭐⭐"),
    (5, "⭐⭐⭐⭐⭐"),
)

class user_form(forms.ModelForm):
    rating = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True
        )
    
    class Meta:
        model=Book_Review_forms
        fields=['user','book','book_photo','book_url','book_review','rating']
        widgets = {
            "book": forms.Select(attrs={
                'class': 'form-control'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['book'].empty_label = "Select Book..."

    def clean_rating(self):
        rating = int(self.cleaned_data['rating'])
        if rating < 1 or rating > 5:
            raise forms.ValidationError("Rating must be between 1 and 5.")
        return rating