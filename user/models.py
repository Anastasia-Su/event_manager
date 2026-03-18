from typing import Any, Optional, Type
from django.db import models
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.translation import gettext as _

from django.contrib.auth.models import (
    AbstractUser,
    BaseUserManager,
)


class UserManager(BaseUserManager):
    """
    Custom manager for User model that uses email instead of username.
    Provides helper methods to create regular users and superusers.
    """

    use_in_migrations = True

    def _create_user(
        self, email: str, password: Optional[str], **extra_fields: Any
    ) -> "User":
        """Create and save a User with the given email and password."""

        if not email:
            raise ValueError("The given email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(
        self, email: str, password: Optional[str], **extra_fields: Any
    ) -> "User":
        """Create and save a regular User with the given email and password."""

        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(
        self,
        email: str,
        password: str,
        **extra_fields: Any,
    ) -> "User":
        """Create and save a SuperUser with the given email and password."""

        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Custom user model that replaces username with email as the unique identifier.
    """

    username = None
    email = models.EmailField(_("email address"), unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()


class ActivationToken(models.Model):
    """
    Stores a one-time activation token for a user.
    Used for account activation flows with expiration logic.
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=64, unique=True, default=get_random_string(48))
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self) -> bool:
        return self.created_at < timezone.now() - timezone.timedelta(hours=24)

    @classmethod
    def create_for_user(cls, user: User) -> "ActivationToken":
        """
        Create a new activation token for a user.
        Removes any existing token to ensure only one active token per user.
        """

        cls.objects.filter(user=user).delete()

        return cls.objects.create(user=user)
