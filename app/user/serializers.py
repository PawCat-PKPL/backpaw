from html import escape
from rest_framework import serializers

from authentication.models import CustomUser
from user.models import Friendship, Notification

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'avatar_id']

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'

    def validate(self, data):
        title = data.get('title', '').strip()
        message = data.get('message', '').strip()

        if not data.get('title'):
            raise serializers.ValidationError("Title is required")
        if not data.get('message'):
            raise serializers.ValidationError("Message is required")
        
        data['title'] = escape(title)
        data['message'] = escape(message)
        return data

class FriendshipSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    receiver = UserSerializer(read_only=True)

    class Meta:
        model = Friendship
        fields = ['id', 'sender', 'receiver', 'status', 'created_at']