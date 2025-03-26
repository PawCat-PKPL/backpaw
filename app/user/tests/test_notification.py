from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from authentication.models import CustomUser
from user.models import Notification

class TestSendNotification(APITestCase):
    def setUp(self):
        self.admin_user = CustomUser.objects.create_superuser(
            email="admin@example.com", 
            username="admin", 
            password="adminpassword"
        )
        self.user1 = CustomUser.objects.create_user(
            email="user1@example.com", 
            username="user1", 
            password="password1"
        )
        self.user2 = CustomUser.objects.create_user(
            email="user2@example.com", 
            username="user2", 
            password="password2"
        )
        self.send_notification_url = reverse('admin_dashboard:send_notification')
        self.admin_notification_url = reverse('admin_dashboard:see_notifications')
        self.user_notification_url = reverse('user:see_notifications')

    def authenticate(self, user):
        self.client.force_authenticate(user)

    def test_send_notification_to_all(self):
        self.authenticate(self.admin_user)
        response = self.client.post(self.send_notification_url, {"title": "Test", "message": "Hello everyone"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Notification.objects.count(), 2)

    def test_send_notification_to_specific_user(self):
        self.authenticate(self.admin_user)
        response = self.client.post(self.send_notification_url, {
            "title": "Test", "message": "Hello user1", "receiver_id": self.user1.id
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Notification.objects.filter(receiver=self.user1).count(), 1)

    def test_send_notification_to_self_fail(self):
        self.authenticate(self.admin_user)
        response = self.client.post(self.send_notification_url, {
            "title": "Test", "message": "Hello me", "receiver_id": self.admin_user.id
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_send_notification_as_non_admin_fail(self):
        self.authenticate(self.user1)
        response = self.client.post(self.send_notification_url, {
            "title": "Test", "message": "Unauthorized"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_send_notification_unauthenticated_fail(self):
        response = self.client.post(self.send_notification_url, {
            "title": "Test", "message": "No auth"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_send_notification_to_nonexistent_user(self):
        self.authenticate(self.admin_user)
        response = self.client.post(self.send_notification_url, {
            "title": "Test", "message": "Ghost user", "receiver_id": 9999
        })
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_send_notification_with_empty_data_fails(self):
        self.authenticate(self.admin_user)
        response = self.client.post(self.send_notification_url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_user_notifications(self):
        Notification.objects.create(title="Test", message="Notification", sender=self.admin_user, receiver=self.user1)
        self.authenticate(self.user1)
        response = self.client.get(self.user_notification_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_admin_notifications(self):
        Notification.objects.create(title="Admin Test", message="Admin Notification", sender=self.admin_user, receiver=self.user1)
        self.authenticate(self.admin_user)
        response = self.client.get(self.admin_notification_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_user_notifications_without_authentication(self):
        response = self.client.get(self.user_notification_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_admin_notifications_as_non_admin(self):
        self.authenticate(self.user1)
        response = self.client.get(self.admin_notification_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
