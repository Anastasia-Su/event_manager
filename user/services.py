from django.core.mail import send_mail
from django.conf import settings
from .models import ActivationToken, User as UserType


def send_account_activation_email(user: UserType) -> None:
    """
    Send an activation email to the user after successful registration.
    Email delivery failures are silently ignored (best-effort delivery).
    """

    token_obj = ActivationToken.create_for_user(user)
    activation_url = f"http://127.0.0.1:8000/user/activate/?token={token_obj.token}&email={user.email}"
    message = f"Click to activate your account:\n\n{activation_url}"

    send_mail(
        "Activate Your Account",
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=True,
    )
