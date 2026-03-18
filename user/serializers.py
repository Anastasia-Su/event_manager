import re
from typing import Any
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import ActivationToken, User as UserType
from .services import send_account_activation_email

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.

    Handles:
    - Email + password input
    - Password confirmation & complexity validation
    - Creates inactive user
    - Generates activation token
    - Sends activation email (best-effort delivery)
    """

    password = serializers.CharField(
        write_only=True,
        required=True,
        min_length=8,
        style={"input_type": "password", "placeholder": "Minimum 8 characters"},
    )
    confirm_password = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password", "placeholder": "Confirm password"},
    )

    def validate_password(self, value: str) -> str:
        """Field-level validation for password complexity"""

        if not re.search(r"[A-Z]", value):
            raise serializers.ValidationError(
                "Password must contain at least one uppercase letter."
            )
        if not re.search(r"[a-z]", value):
            raise serializers.ValidationError(
                "Password must contain at least one lowercase letter."
            )
        if not re.search(r"\d", value):
            raise serializers.ValidationError(
                "Password must contain at least one digit."
            )
        return value

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        """Check that passwords match."""

        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError({"password": "Passwords do not match"})
        return data

    def create(self, validated_data: dict[str, Any]) -> UserType:
        """Create inactive user, generate activation token, and send email."""

        validated_data.pop("confirm_password")
        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
        )
        user.is_active = False
        user.save()

        send_account_activation_email(user=user)

        return user

    class Meta:
        model = User
        fields = ("email", "password", "confirm_password")
        extra_kwargs = {
            "email": {
                "required": True,
                "help_text": "Used for login and activation",
            }
        }


class ActivationSerializer(serializers.Serializer):
    """
    Serializer for account activation via token + email.

    Validates:
    - Token exists and belongs to the user
    - Token is not expired

    On success: activates user and deletes token
    """

    token = serializers.CharField()
    email = serializers.EmailField()

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Validate token and email combination.

        Raises:
            ValidationError: If token/email invalid or token expired.
        """

        try:
            user = User.objects.get(email=data["email"])
            token_obj = ActivationToken.objects.get(user=user, token=data["token"])
        except (User.DoesNotExist, ActivationToken.DoesNotExist):
            raise serializers.ValidationError("Invalid token or email")

        if token_obj.is_expired():
            token_obj.delete()
            raise serializers.ValidationError("Token has expired")

        data["user"] = user
        data["token_obj"] = token_obj

        return data

    def save(self, **kwargs: Any) -> None:
        user = self.validated_data["user"]
        user.is_active = True
        user.save()
        self.validated_data["token_obj"].delete()


class LogoutSerializer(serializers.Serializer):
    """
    Serializer for logout request payload.

    Required: refresh token
    Optional: current access token (for immediate revocation)
    """

    refresh = serializers.CharField()
    access = serializers.CharField(required=False)
