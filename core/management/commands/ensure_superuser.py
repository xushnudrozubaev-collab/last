import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create the configured superuser if it does not already exist."

    def handle(self, *args, **options):
        username = os.getenv("DJANGO_SUPERUSER_USERNAME", "coachadmin")
        email = os.getenv("DJANGO_SUPERUSER_EMAIL", "coach@example.com")
        password = os.getenv("DJANGO_SUPERUSER_PASSWORD")

        User = get_user_model()
        user = User.objects.filter(username=username).first()

        if user:
            self.stdout.write(self.style.SUCCESS(f"Superuser '{username}' already exists."))
            return

        if not password:
            self.stdout.write(
                self.style.WARNING(
                    "DJANGO_SUPERUSER_PASSWORD is not set; skipping superuser creation."
                )
            )
            return

        User.objects.create_superuser(username=username, email=email, password=password)
        self.stdout.write(self.style.SUCCESS(f"Superuser '{username}' created."))
