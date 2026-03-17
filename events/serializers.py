from rest_framework import serializers
from .models import Event, EventRegistration


class EventSerializer(serializers.ModelSerializer):
    organizer = serializers.PrimaryKeyRelatedField(
        read_only=True  # ← makes organizer read-only, cannot be set in input
    )

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
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    event = serializers.PrimaryKeyRelatedField(read_only=True)
    
    class Meta:
        model = EventRegistration
        fields = ("id", "user", "event", "registered_at")
