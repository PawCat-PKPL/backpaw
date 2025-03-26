from django.db.models import Q

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser, IsAuthenticated

from authentication.models import CustomUser
from user.models import Friendship, Notification
from user.serializers import NotificationSerializer, UserSerializer
from utils import api_response

# NOTIFICATION
class SendNotificationView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, *args, **kwargs):
        data = request.data
        sender = request.user
        receiver_id = data.get('receiver_id')

        if not data.get('title') or not data.get('message'):
            return api_response(status.HTTP_400_BAD_REQUEST, "Title and message are required")

        # Kirim ke semua user
        if not receiver_id:
            users = CustomUser.objects.filter(is_active=True).exclude(id=sender.id)
            notifications = [
                Notification(title=data['title'], message=data['message'], sender=sender, receiver=user)
                for user in users
            ]
            Notification.objects.bulk_create(notifications)
            return api_response(status.HTTP_201_CREATED, 'Notification successfully sent to all users')

        # Kirim ke user tertentu
        try:
            receiver = CustomUser.objects.get(id=receiver_id, is_active=True)

            if receiver == sender:
                return api_response(status.HTTP_400_BAD_REQUEST, 'Cannot send notification to yourself')

            Notification.objects.create(title=data['title'], message=data['message'], sender=sender, receiver=receiver)
            return api_response(status.HTTP_201_CREATED, 'Notification successfully sent')
        except CustomUser.DoesNotExist:
            return api_response(status.HTTP_404_NOT_FOUND, 'User not found')
        
class UserNotificationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notifications = Notification.objects.filter(receiver=request.user).order_by('-created_at')
        serializer = NotificationSerializer(notifications, many=True)
        return api_response(status.HTTP_200_OK, 'Notifications retrieved successfully', serializer.data)
    
class AdminNotificationView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        notifications = Notification.objects.all().order_by('-created_at')
        serializer = NotificationSerializer(notifications, many=True)
        return api_response(status.HTTP_200_OK, 'Notifications retrieved successfully', serializer.data)


# FRIENDSHIP
class AddFriendView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        sender = request.user
        receiver_id = request.data.get("receiver_id")

        if not receiver_id:
            return api_response(status.HTTP_400_BAD_REQUEST, 'Receiver ID is required')

        try:
            receiver = CustomUser.objects.get(id=receiver_id)
        except CustomUser.DoesNotExist:
            return api_response(status.HTTP_404_NOT_FOUND, 'User not found')

        if receiver == sender:
            return api_response(status.HTTP_400_BAD_REQUEST, 'Cannot add yourself as friend')
        
        if Friendship.objects.filter(
            Q(sender=sender, receiver=receiver) | Q(sender=receiver, receiver=sender),
            status="accepted"
        ).exists():
            return api_response(status.HTTP_400_BAD_REQUEST, "Already friends")

        if Friendship.objects.filter(sender=sender, receiver=receiver, status="pending").exists():
            return api_response(status.HTTP_400_BAD_REQUEST, "Already sent a request")

        Friendship.objects.create(sender=sender, receiver=receiver)
        return api_response(status.HTTP_201_CREATED, "Friend request sent")

class AcceptFriendRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        sender_id = request.data.get("sender_id")

        if not sender_id:
            return api_response(status.HTTP_400_BAD_REQUEST, "Sender ID is required")

        try:
            friend_request = Friendship.objects.get(sender_id=sender_id, receiver=request.user, status="pending")
        except Friendship.DoesNotExist:
            return api_response(status.HTTP_404_NOT_FOUND, "Friend request not found")

        if friend_request.status != "pending":
            return api_response(status.HTTP_400_BAD_REQUEST, "Friend request is no longer valid")

        if friend_request.receiver != request.user:
            return api_response(status.HTTP_403_FORBIDDEN, "You are not authorized to accept this request")

        friend_request.status = "accepted"
        friend_request.save()

        return api_response(status.HTTP_200_OK, "Friend request accepted")


class SearchFriendView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get("query")

        if not query:
            return api_response(status.HTTP_400_BAD_REQUEST, "Search query is required")

        users = CustomUser.objects.filter(username__iexact=query) | CustomUser.objects.filter(email__iexact=query)

        if not users.exists():
            return api_response(status.HTTP_404_NOT_FOUND, f"User with username or email '{query}' not found", [])

        serializer = UserSerializer(users, many=True)

        return api_response(status.HTTP_200_OK, "Friends retrieved successfully", serializer.data)


class ListFriendsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        accepted_friends = Friendship.objects.filter(
            Q(sender=user, status="accepted") | Q(receiver=user, status="accepted")
        ).values_list("sender_id", "receiver_id")

        friend_ids = set()
        for sender, receiver in accepted_friends:
            friend_ids.add(sender if receiver == user.id else receiver)

        friends = CustomUser.objects.filter(id__in=friend_ids)

        # pending requests yang masuk
        pending_users = CustomUser.objects.filter(
            id__in=Friendship.objects.filter(receiver=user, status="pending").values_list("sender_id", flat=True)
        )

        # request yang dikirim
        sent_users = CustomUser.objects.filter(
            id__in=Friendship.objects.filter(sender=user, status="pending").values_list("receiver_id", flat=True)
        )
        
        data = {
            "friends": UserSerializer(friends, many=True).data,
            "pending_requests": UserSerializer(pending_users, many=True).data,
            "sent_requests": UserSerializer(sent_users, many=True).data,
        }
        
        return api_response(status.HTTP_200_OK, "List of friends retrieved successfully", data)