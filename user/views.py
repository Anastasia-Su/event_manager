from datetime import datetime, timezone
from typing import Any

from rest_framework import generics, status, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken, UntypedToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from .serializers import RegisterSerializer, ActivationSerializer, LogoutSerializer


@extend_schema(
    summary="Register a new user",
    description=(
        "Creates a new user account with the provided email and password. "
        "An activation email with a verification token will be sent."
    ),
    request=RegisterSerializer,
    responses={
        201: RegisterSerializer,
        400: OpenApiResponse(description="Validation error or passwords do not match"),
    },
    tags=["auth"],
)
class RegisterUserView(generics.CreateAPIView):
    """
    Endpoint for user registration.
    On success: creates inactive user and sends activation email.
    """

    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


@extend_schema(
    summary="Activate user account",
    description="Activates a user account using the email + token received via email.",
    parameters=[
        OpenApiParameter(
            name="email",
            type=str,
            location=OpenApiParameter.QUERY,
            required=True,
            description="User's email address",
        ),
        OpenApiParameter(
            name="token",
            type=str,
            location=OpenApiParameter.QUERY,
            required=True,
            description="Activation token from email",
        ),
    ],
    responses={
        200: OpenApiResponse(description="Account successfully activated"),
        400: OpenApiResponse(description="Invalid or expired token / email"),
    },
    tags=["auth"],
)
class ActivateView(generics.GenericAPIView):
    """
    Activates user account via GET query parameters (email + token).
    Typically called from email link.
    """

    serializer_class = ActivationSerializer
    permission_classes = [AllowAny]

    def get(self, request, *args: Any, **kwargs: Any) -> Response:
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Account activated."}, status=status.HTTP_200_OK)


@extend_schema(
    summary="Logout user (blacklist tokens)",
    description=(
        "Blacklists the provided refresh token to invalidate the session. "
        "Optionally blacklists the current access token for immediate revocation."
    ),
    request=LogoutSerializer,
    responses={
        205: OpenApiResponse(description="Successfully logged out"),
        400: OpenApiResponse(description="Invalid or missing token"),
    },
    tags=["auth"],
)
class LogoutView(APIView):
    """
    Logout endpoint that blacklists refresh (and optionally access) token.

    Payload example:
    ```json
    {
        "refresh": "your.refresh.token.here",
        "access": "optional.current.access.token"
    }
    """

    permission_classes = [IsAuthenticated]
    serializer_class = LogoutSerializer

    def post(self, request, *args: Any, **kwargs: Any) -> Response:
        refresh_token = request.data.get("refresh")
        access_token = request.data.get("access")  # optional

        if not refresh_token:
            return Response(
                {"detail": "Refresh token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Blacklist refresh token
            refresh = RefreshToken(refresh_token)
            refresh.blacklist()

            # Optional: blacklist current access token too (extra security)
            if access_token:
                try:
                    untyped_token = UntypedToken(access_token)
                    exp_timestamp = untyped_token["exp"]
                    exp_datetime = datetime.fromtimestamp(
                        exp_timestamp, tz=timezone.utc
                    )

                    outstanding_token, _ = OutstandingToken.objects.get_or_create(
                        token=str(untyped_token),
                        defaults={
                            "user": request.user,
                            "jti": untyped_token["jti"],
                            "expires_at": exp_datetime,
                        },
                    )
                    BlacklistedToken.objects.get_or_create(token=outstanding_token)
                except TokenError:
                    pass  # Ignore if access token is invalid/expired

            return Response(status=status.HTTP_205_RESET_CONTENT)

        except TokenError:
            return Response(
                {"detail": "Token is invalid or already blacklisted."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            import traceback

            print(traceback.format_exc())
            return Response(
                {"detail": f"Logout failed. Please try again. {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
