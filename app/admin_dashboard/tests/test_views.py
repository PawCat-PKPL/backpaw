from django.utils.timezone import now
from django.urls import reverse
from datetime import timedelta

from rest_framework import status
from rest_framework.test import APITestCase

from authentication.models import CustomUser

class TestAdminDashboard(APITestCase):
    def setUp(self):
        self.admin_user = CustomUser.objects.create_superuser(
            email='admin@example.com',
            username='admin',
            password='admin123'
        )
        self.inactive_user = CustomUser.objects.create_user(
            email='inactive@example.com',
            username='inactive_user',
            password='password123',
            last_login=now() - timedelta(days=6 * 30)  # Lebih dari 5 bulan
        )
        self.active_user = CustomUser.objects.create_user(
            email='active@example.com',
            username='active_user',
            password='password123',
            last_login=now()
        )

        self.client.force_authenticate(user=self.admin_user)
        self.all_users_url = reverse('admin_dashboard:user_list')
        self.inactive_users_url = reverse('admin_dashboard:inactive_user_list')
        self.delete_user_url = lambda user_id: reverse('admin_dashboard:delete_user', kwargs={'user_id': user_id})

    def test_get_all_users(self):
        response = self.client.get(self.all_users_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 3)  # Total 3 user dari setUp

    def test_get_inactive_users(self):
        response = self.client.get(self.inactive_users_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 1)  # Hanya 1 user yang inactive

    def test_delete_user(self):
        response = self.client.delete(self.delete_user_url(self.inactive_user.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(CustomUser.objects.filter(id=self.inactive_user.id).exists())

    def test_delete_non_existing_user(self):
        response = self.client.delete(self.delete_user_url(9999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_delete_admin_user(self):
        response = self.client.delete(self.delete_user_url(self.admin_user.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_with_invalid_user_id(self):
        response = self.client.delete(self.delete_user_url("1"))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
