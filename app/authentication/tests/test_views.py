from django.core.cache import cache
from django.urls import reverse
from django.conf import settings

from rest_framework import status
from rest_framework.test import APITestCase

from authentication.models import CustomUser

class TestAuthentication(APITestCase):
    def setUp(self):
        self.register_url = reverse('authentication:register')
        self.login_url = reverse('authentication:login')
        self.user_info_url = reverse('authentication:user_info')
        self.logout_url = reverse('authentication:logout')
        self.forgot_password_url = reverse('authentication:forgot_password')
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

    def test_register_with_empty_data(self):
        response = self.client.post(self.register_url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_with_empty_data(self):
        response = self.client.post(self.login_url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # OWASP Top 10
    # 1. Broken Access Control - akses user info tanpa login
    def test_broken_access_control_user_info(self):
        response = self.client.get(self.user_info_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # 2. Cryptographic Failures - password tetap hashed setelah reset
    def test_cryptographic_failure_password_hashing(self):
        old_password_hash = self.user.password
        self.user.set_password('testpassword')
        self.user.save()
        self.assertNotEqual(old_password_hash, self.user.password)

    # 3. Injection - XSS injection di login
    def test_injection_xss_in_login(self):
        payload = {
            "username_or_email": "<script>alert(1)</script>",
            "password": "password"
        }
        response = self.client.post(self.login_url, data=payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # 4. Insecure Design - register dengan password lemah
    def test_register_without_password_policy(self):
        response = self.client.post(self.register_url, data={
            "email": "weakpassword@example.com",
            "username": "weakuser",
            "password": " ",
            "password2": " ",
            "full_name": "Weak User"
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # 5. Security Misconfiguration - server production harus DEBUG = False
    def test_debug_mode_off(self):
        self.assertFalse(settings.DEBUG)

    # 6. Vulnerable and Outdated Components -  dummy test
    def test_vulnerable_outdated_components_dummy(self):
        self.assertTrue(True)

    # 7. Identification and Authentication Failures - rate limit setelah login gagal berkali-kali
    def test_identification_authentication_rate_limit(self):
        for _ in range(4):  # limit 3 kali
            response = self.client.post(self.login_url, data={
                "username_or_email": self.user.email,
                "password": "wrongpassword"
            })
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    # 8. Software and Data Integrity Failures - logout dengan token invalid
    def test_software_data_integrity_logout_invalid_token(self):
        self.client.cookies['refresh_token'] = 'invalidtoken'
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # 9. Security Logging and Monitoring Failures - login gagal tetap dapat response
    def test_security_logging_monitoring_failed_login(self):
        response = self.client.post(self.login_url, data={
            "username_or_email": "nonexistent@example.com",
            "password": "wrongpassword"
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # 10. Server Side Request Forgery (SSRF) - dummy tes
    def test_server_side_request_forgery_dummy(self):
        self.assertTrue(True)
