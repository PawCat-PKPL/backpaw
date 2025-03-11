from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from authentication.models import CustomUser

class RegisterSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(write_only=True)
    
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'full_name', 'password', 'password2']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password': 'Passwords do not match'})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        user = CustomUser.objects.create_user(**validated_data)
        return user

class LoginSerializer(serializers.Serializer):
    username_or_email = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        username_or_email = attrs.get('username_or_email')
        password = attrs.get('password')
        
        user = CustomUser.objects.filter(username=username_or_email).first() or \
               CustomUser.objects.filter(email=username_or_email).first()
        
        if user and user.check_password(password):
            refresh = RefreshToken.for_user(user)
            return {'refresh': str(refresh), 'access': str(refresh.access_token)}
        raise serializers.ValidationError('Invalid credentials')
        
class VerifyColorSerializer(serializers.Serializer):
    username_or_email = serializers.CharField()
    hex_color = serializers.CharField()

    def validate(self, data):
        username_or_email = data.get("username_or_email")
        hex_color = data.get("hex_color")

        user = CustomUser.objects.filter(email=username_or_email).first() or \
               CustomUser.objects.filter(username=username_or_email).first()

        if not user:
            raise serializers.ValidationError({"message": "User not found"})

        if not user.check_hex_color(hex_color):
            raise serializers.ValidationError({"message": "Invalid hex color"})

        data["user"] = user
        return data