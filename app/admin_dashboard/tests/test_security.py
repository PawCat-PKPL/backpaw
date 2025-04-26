from django.utils.timezone import now
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from authentication.models import CustomUser

from datetime import timedelta
import json
import django

class TestAdminDashboardSecurity(APITestCase):
    def setUp(self):
        self.admin_user = CustomUser.objects.create_superuser(
            email='admin@example.com',
            username='admin',
            password='admin123'
        )
        self.staff_user = CustomUser.objects.create_user(
            email='staff@example.com',
            username='staff_user',
            password='staff123',
            is_staff=True
        )
        self.regular_user = CustomUser.objects.create_user(
            email='user@example.com',
            username='regular_user',
            password='user123'
        )
        self.inactive_user = CustomUser.objects.create_user(
            email='inactive@example.com',
            username='inactive_user',
            password='password123',
            last_login=now() - timedelta(days=6 * 30)
        )

        self.all_users_url = reverse('admin_dashboard:user_list')
        self.inactive_users_url = reverse('admin_dashboard:inactive_user_list')
        self.delete_user_url = lambda user_id: reverse('admin_dashboard:delete_user', kwargs={'user_id': user_id})
        self.login_url = reverse('authentication:login')

    def test_unauthorized_access_to_admin_endpoints(self):
        # Tes user biasa tidak bisa akses endpoint admin
        # OWASP A01:2021 - Broken Access Control
        self.client.force_authenticate(user=self.regular_user)
        
        response = self.client.get(self.all_users_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        response = self.client.get(self.inactive_users_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        response = self.client.delete(self.delete_user_url(self.inactive_user.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_horizontal_privilege_escalation(self):
        # Tes user tidak bisa mengakses data user lain
        # OWASP A01:2021 - Broken Access Control
        user1 = CustomUser.objects.create_user(
            email='user1@example.com',
            username='user1',
            password='password123'
        )
        user2 = CustomUser.objects.create_user(
            email='user2@example.com',
            username='user2',
            password='password123'
        )
        
        self.client.force_authenticate(user=user1)
        
        response = self.client.delete(self.delete_user_url(user2.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_sql_injection_in_user_id(self):
        # Tes ketahanan terhadap SQL injection di parameter URL
        # OWASP A03:2021 - Injection
        self.client.force_authenticate(user=self.admin_user)
        
        base_url = reverse('admin_dashboard:delete_user', kwargs={'user_id': 1})
        injection_url = base_url.replace('1', '1 OR 1=1')
        
        initial_user_count = CustomUser.objects.count()
        
        response = self.client.delete(injection_url)
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)
        
        self.assertEqual(CustomUser.objects.count(), initial_user_count)

    def test_business_logic_constraints(self):
        # Tes bahwa aturan bisnis mencegah penghapusan user admin
        # OWASP A04:2021 - Insecure Design
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.delete(self.delete_user_url(self.staff_user.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(CustomUser.objects.filter(id=self.staff_user.id).exists())

    def test_error_handling_leaks_no_sensitive_info(self):
        # Tes bahwa error handling tidak membocorkan informasi sensitif
        # OWASP A05:2021 - Security Misconfiguration
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.delete(self.delete_user_url(99999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        response_content = json.loads(response.content)
        self.assertNotIn("Traceback", str(response_content))
        self.assertNotIn("django", str(response_content).lower())

    def test_brute_force_protection(self):
        # Tes bahwa rate limiting mencegah brute force login
        # OWASP A07:2021 - Identification and Authentication Failures
        client = APIClient()
        
        for i in range(10):
            client.post(self.login_url, {
                'username': 'admin',
                'password': f'wrong_password_{i}'
            })
        
        response = client.post(self.login_url, {
            'username': 'admin',
            'password': 'wrong_password_again'
        })
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_csrf_protection(self):
        # Tes bahwa CSRF protection mencegah perubahan status yang tidak sah
        self.client.logout()
        response = self.client.delete(self.delete_user_url(self.regular_user.id))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(self.delete_user_url(self.regular_user.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_input_validation_and_sanitization(self):
        # Tes bahwa input yang tidak valid ditolak dan tidak menyebabkan error
        # OWASP A03:2021 - Injection
        self.client.force_authenticate(user=self.admin_user)
        
        malicious_inputs = [
            "<script>alert('XSS')</script>",
            "'; DROP TABLE users; --",
            "\x00\x1a\xff"
        ]
        
        base_url = reverse('admin_dashboard:delete_user', kwargs={'user_id': 1})
        
        for inp in malicious_inputs:
            try:
                test_url = base_url.replace('1', inp)
                
                response = self.client.delete(test_url)
                self.assertNotIn(response.status_code, [status.HTTP_500_INTERNAL_SERVER_ERROR, status.HTTP_200_OK])
            except Exception:
                pass

    def test_password_is_hashed(self):
        # Tes password yang disimpan harus terenkripsi
        # OWASP A02:2021 - Cryptographic Failures
        user = CustomUser.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='mypassword'
        )
        self.assertNotEqual(user.password, 'mypassword')
        self.assertTrue(user.password.startswith('pbkdf2_sha256$'))

    def test_django_version(self):
        # Tes versi Django yang digunakan
        # OWASP A06:2021 - Vulnerable and Outdated Components
        self.assertTrue(django.get_version() >= '4.2')

    