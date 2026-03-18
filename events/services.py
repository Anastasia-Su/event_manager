from django.core.mail import send_mail
from django.conf import settings
from .models import EventRegistration, Event
from user.models import User
from .exceptions import AlreadyRegisteredError


def send_registration_email(event: Event, user: User) -> None:
    """
    Send a confirmation email to the user after successful registration for an event.
    Email delivery failures are silently ignored (best-effort delivery).
    """

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
        [user.email],
        fail_silently=True,
    )


def send_cancellation_email(event: Event, user: User) -> None:
    """
    Send a confirmation email to the user after registration for an event is cancelled.
    Email delivery failures are silently ignored (best-effort delivery).
    """

    subject = f"Registration Cancelled: {event.title}"
    message = (
        f"Hello,\n\n"
        f"You have successfully cancelled your registration for the event:\n\n"
        f"Title: {event.title}\n"
        f"Date: {event.date.strftime('%Y-%m-%d %H:%M')}\n"
        f"Location: {event.location}\n\n"
    )
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=True,
    )


def register_user_to_event(event: Event, user: User) -> EventRegistration:
    """Register a user for an event or raise exception if already registered."""

    registration, created = EventRegistration.objects.get_or_create(
        user=user, event=event
    )
    if not created:
        raise AlreadyRegisteredError()
    return registration
