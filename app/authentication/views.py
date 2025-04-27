from django.http import HttpResponse
from django.core.cache import cache
from django.contrib.auth import login

from rest_framework import status
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework.permissions import IsAuthenticated

from authentication.models import CustomUser
from authentication.serializers import LoginSerializer, RegisterSerializer, VerifyColorSerializer, UserSerializer
from utils import api_response

def hello_pawcat(request):
    return HttpResponse("hello pawcat")

class RateLimiter:
    @staticmethod
    def is_rate_limited(key, limit=3, timeout=300):
        failures = cache.get(key, 0)
        if failures >= limit:
            return True
        return False

    @staticmethod
    def increment_failures(key, timeout=300):
        failures = cache.get(key, 0)
        cache.set(key, failures + 1, timeout=timeout)

    @staticmethod
    def reset_attempts(key):
        cache.delete(key)

class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return api_response(status.HTTP_201_CREATED, "User registered successfully")
        return api_response(status.HTTP_400_BAD_REQUEST, "Validation error", serializer.errors)

class LoginView(APIView):
    def post(self, request):
        key = f"login_attempts_{request.data.get('username_or_email')}"
        if RateLimiter.is_rate_limited(key):
            return api_response(status.HTTP_429_TOO_MANY_REQUESTS, "Too many login attempts. Try again later.")

        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            RateLimiter.reset_attempts(key)
            user = CustomUser.objects.get(id=serializer.validated_data['user_id'])

            # Hapus token lama sebelum membuat yang baru
            OutstandingToken.objects.filter(user=user).delete()

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)

            login(request, user)
            
            response = api_response(status.HTTP_200_OK, "Login successful", {
                'user_id': serializer.validated_data['user_id'],
                'username': user.username,
            })
        
            response.set_cookie(
                key='refresh_token',
                value=str(refresh),
                httponly=True,
                secure=True, # Safari = False
                samesite="None"
            )
            response.set_cookie(
                key='access_token',
                value=access_token,
                httponly=True,
                secure=True, # Safari = False
                samesite="None"
            )

            return response
        
        RateLimiter.increment_failures(key)
        return api_response(status.HTTP_400_BAD_REQUEST, "Invalid credentials", serializer.errors)
    
class LogoutView(APIView):
    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')
        if not refresh_token:
            return api_response(status.HTTP_400_BAD_REQUEST, "No refresh token found")
        
        try:
            refresh = RefreshToken(refresh_token)
            refresh.blacklist()
        except Exception as e:
            return api_response(status.HTTP_400_BAD_REQUEST, "Error blacklisting token", str(e))
        
        response = api_response(status.HTTP_200_OK, "Logout successful")
        response.delete_cookie('refresh_token', path='/', domain=None) 
        response.delete_cookie('access_token', path='/', domain=None) 
        return response

class ForgotPasswordView(APIView):
     def post(self, request):
        key = f"forgot_password_attempts_{request.data.get('username_or_email')}"
        if RateLimiter.is_rate_limited(key):
            return api_response(status.HTTP_429_TOO_MANY_REQUESTS, "Too many attempts. Try again later.")

        serializer = VerifyColorSerializer(data=request.data)
        if serializer.is_valid():
            RateLimiter.reset_attempts(key)
            user = serializer.validated_data["user"]
            new_password = request.data.get("new_password")

            if not new_password:
                return api_response(status.HTTP_400_BAD_REQUEST, "New password is required")

            user.set_password(new_password)
            user.save()

            return api_response(status.HTTP_200_OK, "Password changed successfully")

        return api_response(status.HTTP_400_BAD_REQUEST, "Verification failed", serializer.errors)
     
class CookieTokenRefreshView(TokenRefreshView):
    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')
        if not refresh_token:
            return api_response(status.HTTP_400_BAD_REQUEST, "No refresh token found")
       
        try:
            refresh = RefreshToken(refresh_token)
            access_token = str(refresh.access_token)

            response = api_response(status.HTTP_200_OK, "Token refreshed")
            response.set_cookie(
                key='access_token',
                value=access_token,
                httponly=True,
                secure=True,
                samesite="None"
            )
            return response
        
        except InvalidToken:
            return api_response(status.HTTP_400_BAD_REQUEST, "Invalid refresh token")
        
class UserInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if not user.is_authenticated:
            return api_response(status.HTTP_401_UNAUTHORIZED, "User not authenticated")

        data = {
            'user_id': user.id,
            'username': user.username,
            'avatar_id': user.avatar_id,
            'is_active': user.is_active,
            'is_admin': user.is_staff,
            'is_superuser': user.is_superuser,
        }
        return api_response(status.HTTP_200_OK, "User info retrieved successfully", data)