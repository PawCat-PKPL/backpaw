from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from authentication.models import CustomUser
from user.models import Friendship

class TestFriend(APITestCase):
    def setUp(self):
        self.user1 = CustomUser.objects.create_user(
            email='user1@example.com', 
            username='user1', 
            password='password123'
        )
        self.user2 = CustomUser.objects.create_user(
            email='user2@example.com', 
            username='user2', 
            password='password123'
        )
        self.user3 = CustomUser.objects.create_user(
            email='user3@example.com', 
            username='user3', 
            password='password123'
        )

        self.add_friend_url = reverse('user:add_friend')
        self.accept_request_url = reverse('user:accept_friend')
        self.search_friend_url = reverse('user:search_friend')
        self.list_friends_url = reverse('user:list_friends')
        
        self.client.force_authenticate(user=self.user1)

    def test_add_friend_success(self):
        response = self.client.post(self.add_friend_url, {'receiver_id': self.user2.id})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Friendship.objects.filter(sender=self.user1, receiver=self.user2, status='pending').exists())

    def test_add_friend_without_receiver_id(self):
        response = self.client.post(self.add_friend_url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_friend_to_nonexistent_user(self):
        response = self.client.post(self.add_friend_url, {'receiver_id': 999})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_add_friend_to_self(self):
        response = self.client.post(self.add_friend_url, {'receiver_id': self.user1.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_duplicate_friend_request(self):
        Friendship.objects.create(sender=self.user1, receiver=self.user2, status='pending')
        response = self.client.post(self.add_friend_url, {'receiver_id': self.user2.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_accept_friend_request_success(self):
        Friendship.objects.create(sender=self.user2, receiver=self.user1, status='pending')
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(self.accept_request_url, {'sender_id': self.user2.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(Friendship.objects.filter(sender=self.user2, receiver=self.user1, status='accepted').exists())

    def test_accept_nonexistent_friend_request(self):
        response = self.client.post(self.accept_request_url, {'sender_id': self.user3.id})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_accept_friend_request_without_sender_id(self):
        response = self.client.post(self.accept_request_url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_search_friend_success(self):
        response = self.client.get(f"{self.search_friend_url}?query=user2")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 1)

    def test_search_friend_not_found(self):
        response = self.client.get(f"{self.search_friend_url}?query=unknownuser")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_friends(self):
        Friendship.objects.create(sender=self.user1, receiver=self.user2, status='accepted')
        response = self.client.get(self.list_friends_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']['friends']), 1)

    def test_list_friends_no_friends(self):
        response = self.client.get(self.list_friends_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']['friends']), 0)
