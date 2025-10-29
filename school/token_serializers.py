from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import serializers
from typing import Any, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from .models import User


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT Token Serializer that requires role in login and validates it
    """
    role = serializers.CharField(required=True, write_only=True)
    
    @classmethod
    def get_token(cls, user: "User"):  # type: ignore[override]
        token = super().get_token(user)
        
        # Add custom claims
        token['role'] = user.role
        token['email'] = user.email
        token['is_approved'] = user.is_approved
        token['is_active'] = user.is_active
        
        return token
    
    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        # Extract role from request
        role = attrs.pop('role', None)
        
        # Call parent validation (validates email and password)
        data = super().validate(attrs)
        
        # Get the authenticated user
        user: "User" = self.user  # type: ignore[assignment]
        
        if not user:
            raise serializers.ValidationError(
                {"detail": "Authentication failed. Invalid credentials."}
            )
        
        # Check 1: Email exists (already validated by parent)
        # Check 2: Password is correct (already validated by parent)
        
        # Check 3: User is approved
        if not user.is_approved:
            raise serializers.ValidationError(
                {"detail": "Your account is pending approval. Please contact the administrator."}
            )
        
        # Check 4: User is active
        if not user.is_active:
            raise serializers.ValidationError(
                {"detail": "Your account has been deactivated. Please contact the administrator."}
            )
        
        # Check 5: Role matches
        if role and user.role != role:
            raise serializers.ValidationError(
                {"role": f"Invalid role. You are registered as '{user.role}', but attempted to login as '{role}'."}
            )
        
        # Add user details to response
        data['role'] = user.role  # type: ignore[typeddict-item]
        data['email'] = user.email  # type: ignore[typeddict-item]
        data['is_approved'] = user.is_approved  # type: ignore[typeddict-item]
        data['is_active'] = user.is_active  # type: ignore[typeddict-item]
        
        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom Token View that uses CustomTokenObtainPairSerializer
    """
    serializer_class = CustomTokenObtainPairSerializer
