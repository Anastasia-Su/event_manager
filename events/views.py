from rest_framework import viewsets, permissions
from .models import Event, EventRegistration
from .serializers import (
    EventSerializer,
    EventRegistrationSerializer
)
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from .permissions import IsOrganizerOrReadOnly


class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrganizerOrReadOnly]
    
    def get_permissions(self):
        if self.action == "register":
            return [permissions.IsAuthenticated()]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(organizer=self.request.user)

    @extend_schema(
        request=None,  # ← disables request body in Swagger
        responses={201: EventRegistrationSerializer},
        description="Register the authenticated user for this event"
    )
    @action(detail=True, methods=["post"])
    def register(self, request, pk=None):
        event = self.get_object()
        _, created = EventRegistration.objects.get_or_create(
        user=request.user,
        event=event
    )
        if not created:
            return Response(
                {"detail": "You are already registered for this event."},
                status=400
            )
            
        EventRegistration.objects.get_or_create(user=request.user, event=event)
        return Response({"detail": "Registered successfully"}, status=201)
