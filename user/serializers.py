import re
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from .models import ActivationToken
import quopri

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        min_length=8,
        style={'input_type': 'password', 'placeholder': 'Minimum 8 characters'},
    )
    confirm_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password', 'placeholder': 'Confirm password'},
    )
    
    def validate_password(self, value):
        """
        Field-level validation for password complexity
        """
        if not re.search(r'[A-Z]', value):
            raise serializers.ValidationError("Password must contain at least one uppercase letter.")
        if not re.search(r'[a-z]', value):
            raise serializers.ValidationError("Password must contain at least one lowercase letter.")
        if not re.search(r'\d', value):
            raise serializers.ValidationError("Password must contain at least one digit.")
        return value
    
    def validate(self, data):
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError({"password": "Passwords do not match"})
        return data

    def create(self, validated_data):
        validated_data.pop("confirm_password")
        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
        )
        user.is_active = False
        user.save()

        # Create activation token & send email
        token_obj = ActivationToken.create_for_user(user)
        activation_url = (
            f"http://127.0.0.1:8000/user/activate/?token={token_obj.token}&email={user.email}"
        )
        message = f"Click to activate your account:\n\n{activation_url}"

        send_mail(
            "Activate Your Account",
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        return user

    class Meta:
        model = User
        fields = ('email', 'password', 'confirm_password')
        extra_kwargs = {
            'email': {
                'required': True,
                'help_text': 'Used for login and activation',
            }
        }

class ActivationSerializer(serializers.Serializer):
    token = serializers.CharField()
    email = serializers.EmailField()

    def validate(self, data):
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

    def save(self):
        user = self.validated_data["user"]
        user.is_active = True
        user.save()
        self.validated_data["token_obj"].delete()
        
class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()
    access = serializers.CharField(required=False)