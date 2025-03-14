from django.core.cache import cache
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from authentication.models import CustomUser

class TestAuthentication(APITestCase):
    def setUp(self):
        self.register_url = reverse('authentication:register')
        self.login_url = reverse('authentication:login')
        self.forgot_password_url = reverse('authentication:forgot-password')
        self.user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "testpassword",
            "full_name": "Test User"
        }
        self.user = CustomUser.objects.create_user(
            email=self.user_data["email"], 
            username=self.user_data["username"],
            password=self.user_data["password"], 
            full_name=self.user_data["full_name"]
        )

    def tearDown(self):
        cache.clear()

    def test_register_success(self):
        response = self.client.post(self.register_url, data={
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "newpassword",
            "password2": "newpassword",
            "full_name": "New User"
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("User registered successfully", response.data["message"])

    def test_register_fail(self):
        response = self.client.post(self.register_url, data={})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_success(self):
        response = self.client.post(self.login_url, data={
            "username_or_email": self.user_data["email"],
            "password": self.user_data["password"]
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Login successful", response.data["message"])

    def test_login_fail(self):
        response = self.client.post(self.login_url, data={
            "username_or_email": self.user_data["email"], 
            "password": "wrongpassword"
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_rate_limit(self):
        for _ in range(3):
            self.client.post(self.login_url, {
                'username_or_email': self.user_data['email'],
                'password': 'wrongpassword'
            })

        response = self.client.post(self.login_url, {
            'username_or_email': self.user_data['email'],
            'password': 'wrongpassword'
        })

        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_forgot_password_rate_limit(self):
        for _ in range(3):
            self.client.post(self.forgot_password_url, {
                'username_or_email': self.user_data['email'],
                'new_password': 'newsecurepassword123'
            })

        response = self.client.post(self.forgot_password_url, {
            'username_or_email': self.user_data['email'],
            'new_password': 'newsecurepassword123'
        })

        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    # def test_forgot_password_success(self):
    #     self.user.hex_color = "somehashedcolor"
    #     self.user.save()
        
    #     response = self.client.post(self.forgot_password_url, data={
    #         "username_or_email": self.user_data["email"],
    #         "hex_color": "somehashedcolor",
    #         "new_password": "newsecurepassword"
    #     })
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     self.assertIn("Password changed successfully", response.data["message"])
    
    # def test_forgot_password_fail(self):
    #     response = self.client.post(self.forgot_password_url, data={})
    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
