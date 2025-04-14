from html import escape
from rest_framework import serializers

from authentication.models import BankDetail, CustomUser, PaymentMethod
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


# PROFILE
class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = ['payment_type', 'account_number']

class BankDetailSerializer(serializers.ModelSerializer):
    account_number = serializers.SerializerMethodField()

    class Meta:
        model = BankDetail
        fields = ['bank_name', 'account_number']

    # Show hanya ke pemiliknya
    def get_account_number(self, obj):
        request = self.context.get("request")
        user = request.user if request else None

        return obj.account_number if user and obj.user == user else "Restricted"

class UserProfileSerializer(serializers.ModelSerializer):
    payment_methods = PaymentMethodSerializer(many=True, read_only=True)
    bank_details = BankDetailSerializer(many=True, read_only=True)
    friends_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'full_name', 'email', 'avatar_id', 'bio', 'friends_count', 'payment_methods', 'bank_details']
        read_only_fields = ['email', 'username']  # ini buat kunci supaya gabisa diubah