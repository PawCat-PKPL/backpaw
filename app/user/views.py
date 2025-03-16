from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser, IsAuthenticated

from authentication.models import CustomUser
from user.models import Notification
from user.serializers import NotificationSerializer
from utils import api_response

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
