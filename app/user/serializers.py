from html import escape
from rest_framework import serializers

from user.models import Notification

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