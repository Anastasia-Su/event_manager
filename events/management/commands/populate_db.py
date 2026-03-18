import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from events.models import Event
from faker import Faker

User = get_user_model()

fake = Faker()


class Command(BaseCommand):
    help = "Populate database with demo users and events using Faker"

    def handle(self, *args, **kwargs):
        # --- Create users ---
        users = []
        for i in range(1, 6):
            email = f"user{i}@test.com"
            user, created = User.objects.get_or_create(
                email=email, defaults={"is_active": True}
            )
            if created:
                user.set_password("Password123")
                user.save()
            users.append(user)
        self.stdout.write(self.style.SUCCESS(f"Created {len(users)} users."))

        # --- Create 100 unique events ---
        used_titles = set()
        for _ in range(100):
            # Ensure unique event title
            while True:
                title = fake.unique.sentence(nb_words=3).rstrip(".")
                if title not in used_titles:
                    used_titles.add(title)
                    break

            description = fake.text(max_nb_chars=100)
            date = datetime.now() + timedelta(days=random.randint(1, 30))
            location = fake.city()
            organizer = random.choice(users)

            _, created = Event.objects.get_or_create(
                title=title,
                date=date,
                location=location,
                defaults={
                    "description": description,
                    "organizer": organizer,
                },
            )

        self.stdout.write(
            self.style.SUCCESS("Populated 100 unique events successfully.")
        )
