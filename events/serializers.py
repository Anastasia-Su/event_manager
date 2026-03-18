from typing import Any
from rest_framework import serializers
from django.utils import timezone
from .models import Event, EventRegistration


class EventSerializer(serializers.ModelSerializer):
    """
    Serializer for Event model.
    Handles validation to prevent duplicate events
    with the same title, date, and location,
    and ensures events cannot be created in the past.
    """

    organizer = serializers.PrimaryKeyRelatedField(read_only=True)
    
    def validate_date(self, value: timezone.datetime) -> timezone.datetime:
        """
        Ensure the event date is not in the past.
        Allows events starting today (even if already started).
        """
        if value < timezone.now():
            raise serializers.ValidationError(
                "Event date cannot be in the past. "
                "Events can only be created for today or in the future."
            )
        return value

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        """Validate that no duplicate event exists."""

        if Event.objects.filter(
            title=data["title"], date=data["date"], location=data["location"]
        ).exists():
            raise serializers.ValidationError(
                "An event with the same title, date, and location already exists."
            )

        return data

    class Meta:
        model = Event
        fields = (
            "id",
            "title",
            "description",
            "date",
            "location",
            "organizer",
        )


class EventRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for EventRegistration model.
    Represents a user's registration for an event.
    """

    user = serializers.PrimaryKeyRelatedField(read_only=True)
    event = EventSerializer(read_only=True)

    class Meta:
        model = EventRegistration
        fields = ("id", "user", "event", "registered_at")
