from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
)
from drf_spectacular.types import OpenApiTypes
from django.db.models import QuerySet
from django.http import HttpRequest
from django_filters.rest_framework import DjangoFilterBackend

from .models import Event, EventRegistration
from .serializers import EventSerializer, EventRegistrationSerializer
from .filters import EventFilter
from .services import send_registration_email, register_user_to_event
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
        responses={201: EventRegistrationSerializer},
    )
    @action(detail=True, methods=["post"])
    def register(self, request: HttpRequest, pk: str | None = None) -> Response:
        event = self.get_object()
        try:
            register_user_to_event(event=event, user=request.user)
        except AlreadyRegisteredError:
            return Response(
                {"detail": "You are already registered for this event."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        send_registration_email(event=event, user=request.user)

        return Response(
            {"detail": "Registered successfully"}, status=status.HTTP_201_CREATED
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
