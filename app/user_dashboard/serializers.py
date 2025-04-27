from rest_framework import serializers
from .models import Transaction, Category
from django.db.models import Sum, Count
from datetime import datetime, timedelta

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'user']

class TransactionSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), write_only=True, source='category'
    )

    class Meta:
        model = Transaction
        fields = ['id', 'user', 'category', 'category_id', 'amount', 'type', 'description', 'date']


class TransactionSummarySerializer(serializers.Serializer):
    total = serializers.DecimalField(max_digits=12, decimal_places=2)
    count = serializers.IntegerField()

class PeriodSummarySerializer(serializers.Serializer):
    expenses = TransactionSummarySerializer()
    income = TransactionSummarySerializer()
    net = serializers.DecimalField(max_digits=12, decimal_places=2)

class CategorySummarySerializer(serializers.Serializer):
    category_id = serializers.IntegerField()
    category_name = serializers.CharField()
    total = serializers.DecimalField(max_digits=12, decimal_places=2)
    count = serializers.IntegerField()
    percentage = serializers.DecimalField(max_digits=5, decimal_places=2)

