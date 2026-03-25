from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Movie, MovieSubscriber

@receiver(post_save, sender=Movie)
def send_new_movie_notification(sender, instance, created, **kwargs):
    if not created:
        return

    recipients = list(
        MovieSubscriber.objects.filter(is_active=True)
        .exclude(user__email__isnull=True)
        .exclude(user__email="")
        .values_list("user__email", flat=True)
    )
    if not recipients:
        return

    send_mail(
        subject=f"New movie added: {instance.title}",
        message=(
            "A new movie has been added to the platform.\n\n"
            f"Title: {instance.title}\n"
            f"Genre: {instance.genre.name}\n"
            f"Release date: {instance.release_date}\n"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipients,
        fail_silently=True,
    )
