from rest_framework import serializers
from .models import Event, EventRegistration


class EventSerializer(serializers.ModelSerializer):
    organizer = serializers.PrimaryKeyRelatedField(
        read_only=True  
    )

    
    def validate(self, data):
        if Event.objects.filter(
            title=data['title'],
            date=data['date'],
            location=data['location']
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
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    event = EventSerializer(read_only=True)
    
    class Meta:
        model = EventRegistration
        fields = ("id", "user", "event", "registered_at")
