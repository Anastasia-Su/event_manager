from typing import Any
from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView


class IsOrganizerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow only the event organizer to modify an object.

    - Read-only access (GET, HEAD, OPTIONS) is allowed for any request.
    - Write access is restricted to the object's organizer.
    """

    def has_object_permission(
        self,
        request: Request,
        view: APIView,
        obj: Any,
    ) -> bool:
        """Check if the request should be permitted for a specific object."""

        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.organizer == request.user
