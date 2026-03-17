from rest_framework import permissions

class IsOrganizerOrReadOnly(permissions.BasePermission):
    """
    Only the organizer of the event can edit or delete it.
    Read-only actions are allowed for all authenticated users.
    """

    def has_object_permission(self, request, view, obj):
        # Safe methods: GET, HEAD, OPTIONS
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions only for the organizer
        return obj.organizer == request.user