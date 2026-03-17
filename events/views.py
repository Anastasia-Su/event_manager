from rest_framework import viewsets, permissions, filters
from .models import Event, EventRegistration
from .serializers import (
    EventSerializer,
    EventRegistrationSerializer
)
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema
from django.core.mail import send_mail
from django.conf import settings

from .permissions import IsOrganizerOrReadOnly


class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrganizerOrReadOnly]
    
    # Filters
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # Exact field filters
    filterset_fields = ['date', 'location', 'organizer']
    
    # Search in title or description (partial match)
    search_fields = ['title', 'description']
    
    # Allow ordering
    ordering_fields = ['date', 'title', 'location']
    
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
            
        # Send email after successful registration
        subject = f"Registration Confirmed: {event.title}"
        message = (
            f"Hello,\n\n"
            f"You have successfully registered for the event:\n\n"
            f"Title: {event.title}\n"
            f"Date: {event.date.strftime('%Y-%m-%d %H:%M')}\n"
            f"Location: {event.location}\n\n"
            "See you there!"
        )
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [request.user.email],
            fail_silently=False,
        )
        
        return Response({"detail": "Registered successfully"}, status=201)
