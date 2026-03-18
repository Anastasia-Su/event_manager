from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiResponse,
)
from drf_spectacular.types import OpenApiTypes
from django.db.models import QuerySet
from django.http import HttpRequest
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from .models import Event, EventRegistration
from .serializers import EventSerializer, EventRegistrationSerializer
from .filters import EventFilter
from .services import (
    send_registration_email,
    send_cancellation_email,
    register_user_to_event,
)
from .exceptions import AlreadyRegisteredError
from .permissions import IsOrganizerOrReadOnly


@extend_schema_view(
    list=extend_schema(
        summary="List all events",
        description=(
            "Returns a paginated list of events. Supports search in title/description, "
            "ordering by date/title/location, and standard page-based pagination."
        ),
        parameters=[
            # search
            OpenApiParameter(
                name="search",
                type=OpenApiTypes.STR,
                description="Partial search in event title or description",
            ),
            # ordering
            OpenApiParameter(
                name="ordering",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Sort results. Prefix with '-' for descending order.",
                enum=[
                    "date",
                    "-date",
                    "title",
                    "-title",
                    "location",
                    "-location",
                ],
            ),
            # pagination
            OpenApiParameter(
                name="page",
                type=OpenApiTypes.INT,
                description="Page number",
            ),
        ],
    )
)
class EventViewSet(viewsets.ModelViewSet):
    """
    API endpoint for viewing and managing events.

    - Authenticated users can view all events
    - Only organizers can update/delete their own events
    - Anyone can register for an event (via custom action)
    - Anyone can view events they are registered for (via custom action)
    """

    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrganizerOrReadOnly]
    filterset_class = EventFilter
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = ["title", "description"]
    ordering_fields = ["date", "title", "location"]

    def get_queryset(self) -> QuerySet[Event]:
        return Event.objects.select_related("organizer")

    def get_permissions(self) -> list[permissions.BasePermission]:
        if self.action == "register":
            return [permissions.IsAuthenticated()]
        return super().get_permissions()

    def perform_create(self, serializer: EventSerializer) -> None:
        serializer.save(organizer=self.request.user)

    @extend_schema(
        summary="Register for an event",
        description="Registers the authenticated user for the specified event.",
        request=None,  # Disables request body in Swagger
        responses={
            201: OpenApiResponse(
                response=EventRegistrationSerializer,
                description="Registration created successfully",
            ),
            400: OpenApiResponse(
                description="Invalid request (already registered / past event)"
            ),
            404: OpenApiResponse(description="Event not found"),
        },
    )
    @action(detail=True, methods=["post"], url_path="register")
    def register(self, request: HttpRequest, pk: str | None = None) -> Response:
        event = self.get_object()

        # Check if action is past
        if event.date < timezone.now():
            return Response(
                {"detail": "Cannot register for past events."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            registration = register_user_to_event(event=event, user=request.user)
        except AlreadyRegisteredError:
            return Response(
                {"detail": "You are already registered for this event."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        send_registration_email(event=event, user=request.user)
        serializer = EventRegistrationSerializer(registration)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="Cancel registration for an event",
        description=(
            "Unregisters the authenticated user from the specified event. "
            "No request body is required. "
            "Registration cannot be cancelled for past events."
        ),
        request=None,  # Disables request body in Swagger
        responses={
            200: OpenApiResponse(
                description="Registration cancelled successfully",
                response=EventRegistrationSerializer,  # або просто {"detail": "str"}
            ),
            400: OpenApiResponse(
                description="Cannot cancel (past event or not registered)"
            ),
            404: OpenApiResponse(description="Not registered for this event"),
        },
    )
    @action(
        detail=True,
        methods=["post"],
        permission_classes=[permissions.IsAuthenticated],
        url_path="unregister",
    )
    def unregister(self, request, pk=None):
        """
        Cancel / unregister the current authenticated user
        from the specified event.
        """

        event = self.get_object()

        try:
            registration = EventRegistration.objects.get(user=request.user, event=event)
        except EventRegistration.DoesNotExist:
            return Response(
                {"detail": "You are not registered for this event."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if event.date < timezone.now():
            return Response(
                {"detail": "Cannot cancel registration for past events."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        registration.delete()

        send_cancellation_email(event=event, user=request.user)

        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        summary="List all events the current user is registered for",
        description=(
            "Returns a list of event registrations for the authenticated user. "
            "Includes event details via nested EventSerializer. "
            "Requires authentication."
        ),
        responses={
            200: OpenApiResponse(
                response=EventRegistrationSerializer(many=True),
                description="List of user's event registrations (paginated if applicable)",
            ),
            401: OpenApiResponse(
                description="Authentication credentials were not provided"
            ),
            403: OpenApiResponse(
                description="You do not have permission to perform this action"
            ),
        },
    )
    @action(
        detail=False,
        methods=["get"],
        permission_classes=[permissions.IsAuthenticated],
        url_path="my-registrations",
    )
    def my_registrations(self, request: HttpRequest) -> Response:
        """
        List all events the current authenticated user is registered for
        """

        registrations = EventRegistration.objects.filter(
            user=request.user
        ).select_related("event")
        
        serializer = EventRegistrationSerializer(registrations, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
