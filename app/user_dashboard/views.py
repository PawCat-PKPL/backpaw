from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import Transaction, Category
from .serializers import TransactionSerializer
from utils import api_response
from django.shortcuts import get_object_or_404
from decimal import Decimal


class TransactionListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        transactions = Transaction.objects.filter(user=request.user).order_by('-date')
        serializer = TransactionSerializer(transactions, many=True)
        return api_response(status.HTTP_200_OK, "Transactions retrieved", serializer.data)

    def post(self, request):
        serializer = TransactionSerializer(data=request.data)
        if serializer.is_valid():
            transaction = serializer.save(user=request.user)

            # Update saldo
            user = request.user
            if transaction.type == "income":
                user.saldo += Decimal(transaction.amount)
            elif transaction.type == "expense":
                user.saldo -= Decimal(transaction.amount)
            user.save()

            return api_response(status.HTTP_201_CREATED, "Transaction added", serializer.data)
        return api_response(status.HTTP_400_BAD_REQUEST, "Invalid data", serializer.errors)


class TransactionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
        old_amount = transaction.amount
        old_type = transaction.type

        serializer = TransactionSerializer(transaction, data=request.data, partial=True)
        if serializer.is_valid():
            updated_transaction = serializer.save()

            # Undo old saldo
            user = request.user
            if old_type == "income":
                user.saldo -= old_amount
            elif old_type == "expense":
                user.saldo += old_amount

            # Apply new saldo
            if updated_transaction.type == "income":
                user.saldo += updated_transaction.amount
            elif updated_transaction.type == "expense":
                user.saldo -= updated_transaction.amount
            user.save()

            return api_response(status.HTTP_200_OK, "Transaction updated", serializer.data)
        return api_response(status.HTTP_400_BAD_REQUEST, "Invalid data", serializer.errors)

    def delete(self, request, pk):
        transaction = get_object_or_404(Transaction, pk=pk, user=request.user)

        # Undo saldo impact
        user = request.user
        if transaction.type == "income":
            user.saldo -= transaction.amount
        elif transaction.type == "expense":
            user.saldo += transaction.amount
        user.save()

        transaction.delete()
        return api_response(status.HTTP_200_OK, "Transaction deleted")