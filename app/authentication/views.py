from html import escape
from django.http import HttpResponse
from django.core.cache import cache
from django.contrib.auth import login

from rest_framework import status
from rest_framework.views import APIView

from authentication.models import CustomUser
from authentication.serializers import LoginSerializer, RegisterSerializer, VerifyColorSerializer
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
            login(request, user)
            
            return api_response(status.HTTP_200_OK, "Login successful", {
                'refresh': serializer.validated_data['refresh'],
                'access': serializer.validated_data['access']
            })
        
        RateLimiter.increment_failures(key)
        return api_response(status.HTTP_400_BAD_REQUEST, "Invalid credentials", serializer.errors)

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