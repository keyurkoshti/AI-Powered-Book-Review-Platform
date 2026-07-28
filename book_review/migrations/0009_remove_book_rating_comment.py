# Generated manually - Remove rating and comment from Book model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('book_review', '0008_alter_book_review_forms_rating'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='book',
            name='rating',
        ),
        migrations.RemoveField(
            model_name='book',
            name='comment',
        ),
    ]

