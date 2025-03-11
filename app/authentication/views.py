from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes

from rest_framework import serializers, status
from rest_framework.response import Response 
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView

from authentication.models import CustomUser
from authentication.serializers import LoginSerializer, RegisterSerializer, VerifyColorSerializer
from utils import api_response

def hello_pawcat(request):
    return HttpResponse("hello pawcat")

class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return api_response(status.HTTP_201_CREATED, "User registered successfully")
        return api_response(status.HTTP_400_BAD_REQUEST, "Validation error", serializer.errors)

class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            return api_response(status.HTTP_200_OK, "Login successful", serializer.validated_data)
        return api_response(status.HTTP_400_BAD_REQUEST, "Invalid credentials", serializer.errors)

class ForgotPasswordView(APIView):
     def post(self, request):
        serializer = VerifyColorSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            new_password = request.data.get("new_password")

            if not new_password:
                return api_response(status.HTTP_400_BAD_REQUEST, "New password is required")

            user.set_password(new_password)
            user.save()

            return api_response(status.HTTP_200_OK, "Password changed successfully")

        return api_response(status.HTTP_400_BAD_REQUEST, "Verification failed", serializer.errors)