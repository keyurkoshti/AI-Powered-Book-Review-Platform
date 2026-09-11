from django.dispatch import receiver
from django.db.models.signals import post_save
from .models import UserProfile, UserAiCredit

@receiver(post_save, sender=UserProfile)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserAiCredit.objects.get_or_create(user=instance)
