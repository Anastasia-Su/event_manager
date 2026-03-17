from datetime import datetime, timezone

from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .serializers import RegisterSerializer, ActivationSerializer, LogoutSerializer
from rest_framework_simplejwt.authentication import JWTAuthentication

    
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken, UntypedToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken


# class RegisterView(generics.CreateAPIView):
#     serializer_class = RegisterSerializer
#     permission_classes = [AllowAny]
    
#     def perform_create(self, serializer):
#         serializer.save()

from drf_spectacular.utils import extend_schema

# from drf_spectacular.utils import extend_schema


# @extend_schema(request=RegisterSerializer, responses=RegisterSerializer)
class RegisterUserView(generics.CreateAPIView):
    serializer_class = RegisterSerializer

    # def create(self, request, *args, **kwargs):
    #     response = super().create(request, *args, **kwargs)
        
    #     return response



from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .serializers import ActivationSerializer

class ActivateView(generics.GenericAPIView):
    serializer_class = ActivationSerializer
    permission_classes = [AllowAny]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="email",
                type=str,
                location=OpenApiParameter.QUERY,
                required=True,
                description="Email address of the user",
            ),
            OpenApiParameter(
                name="token",
                type=str,
                location=OpenApiParameter.QUERY,
                required=True,
                description="Activation token sent via email",
            ),
        ],
        responses={200: ActivationSerializer},  # optional, just to show output schema
        description="Activate a user account using an email verification token.",
    )
    def get(self, request):
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Account activated."}, status=status.HTTP_200_OK)


# # Optional: customize login response (add user info if needed)
# class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
#     @classmethod
#     def get_token(cls, user):
#         token = super().get_token(user)
#         token["email"] = user.email
#         return token


# class LoginView(TokenObtainPairView):
#     serializer_class = CustomTokenObtainPairSerializer
#     permission_classes = [AllowAny]


class LogoutView(APIView):
    """
    Logout user by blacklisting refresh token (and optionally access token).
    
    Expected request body:
    {
        "refresh": "your.refresh.token.here"
    }
    
    Optional: can also send "access" token in body to blacklist it too.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = LogoutSerializer

    def post(self, request):
        refresh_token = request.data.get("refresh")
        access_token = request.data.get("access")  # optional

        if not refresh_token:
            return Response(
                {"detail": "Refresh token is required."},
                status=status.HTTP_400_BAD_REQUEST
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
                    exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)

                    outstanding_token, _ = OutstandingToken.objects.get_or_create(
                        token=str(untyped_token),
                        defaults={
                            "user": request.user,
                            "jti": untyped_token["jti"],
                            "expires_at": exp_datetime,
                        }
                    )
                    BlacklistedToken.objects.get_or_create(token=outstanding_token)
                except TokenError:
                    pass  # ignore if access token is invalid/expired

            return Response(status=status.HTTP_205_RESET_CONTENT)

        except TokenError:
            return Response(
                {"detail": "Token is invalid or already blacklisted."},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            return Response(
                {"detail": f"Logout failed. Please try again. {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )