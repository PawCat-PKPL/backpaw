from html import escape

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
        
        username = attrs.get('username', '').lower()
        if 'admin' in username or 'pawcat' in username:
            raise serializers.ValidationError({'username': 'Invalid username. Can not use this username.'})

        attrs['username'] = escape(username)
        attrs['email'] = escape(attrs.get('email', ''))
        attrs['full_name'] = escape(attrs.get('full_name', ''))
        
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        user = CustomUser.objects.create_user(**validated_data)
        return user

class LoginSerializer(serializers.Serializer):
    username_or_email = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        username_or_email = escape(attrs.get('username_or_email'))
        password = escape(attrs.get('password'))
        
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
        username_or_email = escape(data.get("username_or_email"))
        hex_color = escape(data.get("hex_color"))

        user = CustomUser.objects.filter(email=username_or_email).first() or \
               CustomUser.objects.filter(username=username_or_email).first()

        if not user:
            raise serializers.ValidationError({"message": "User not found"})

        if not user.check_hex_color(hex_color):
            raise serializers.ValidationError({"message": "Invalid hex color"})

        data["user"] = user
        return data