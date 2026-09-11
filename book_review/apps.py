from django.apps import AppConfig


class BookReviewConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'book_review'

    def ready(self):
        import book_review.signals