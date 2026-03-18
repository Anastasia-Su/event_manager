from django.db import models
from django.conf import settings


class Event(models.Model):
    """Represents an event created by a user."""

    title = models.CharField(max_length=255)
    description = models.TextField()
    date = models.DateTimeField()
    location = models.CharField(max_length=255)
    organizer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return self.title

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("title", "date", "location"), name="unique_event"
            )
        ]
        ordering = ["-date", "title"]


class EventRegistration(models.Model):
    """
    Represents a user's registration for a specific event.
    Ensures that a user can register for the same event only once.
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("user", "event"), name="unique_register")
        ]
        ordering = ["-registered_at"]
