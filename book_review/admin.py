from django.contrib import admin
from .models import Book_Review_forms, Book, Category
# Register your models here.


class BookReviewAdmin(admin.ModelAdmin):
    list_display = ('book', 'book_url', 'rating', 'book_review')  # columns in list view
    search_fields = ('book',)  # search bar by book_name
    list_filter = ('book',)    # filter by book_name

class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author')
    search_fields = ('author',)

admin.site.register(Book_Review_forms,BookReviewAdmin),
admin.site.register(Book, BookAdmin)
admin.site.register(Category)