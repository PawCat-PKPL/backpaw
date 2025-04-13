from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import Transaction, Category
from .serializers import TransactionSerializer, CategorySerializer, TransactionSummarySerializer, PeriodSummarySerializer, CategorySummarySerializer
from utils import api_response
from django.shortcuts import get_object_or_404
from decimal import Decimal


from django.db.models import Sum, Count, F, Q
from django.db.models.functions import TruncMonth, TruncYear, TruncWeek
from datetime import datetime, timedelta
import calendar




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
    
class CategoryListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        categories = Category.objects.filter(user=request.user)
        serializer = CategorySerializer(categories, many=True)
        return api_response(status.HTTP_200_OK, "Categories retrieved", serializer.data)

    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return api_response(status.HTTP_201_CREATED, "Category created", serializer.data)
        return api_response(status.HTTP_400_BAD_REQUEST, "Invalid data", serializer.errors)

class CategoryDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        return Category.objects.filter(pk=pk, user=user).first()

    def put(self, request, pk):
        category = self.get_object(pk, request.user)
        if not category:
            return api_response(status.HTTP_404_NOT_FOUND, "Category not found")
        serializer = CategorySerializer(category, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return api_response(status.HTTP_200_OK, "Category updated", serializer.data)
        return api_response(status.HTTP_400_BAD_REQUEST, "Invalid data", serializer.errors)

    def delete(self, request, pk):
        category = self.get_object(pk, request.user)
        if not category:
            return api_response(status.HTTP_404_NOT_FOUND, "Category not found")
        category.delete()
        return api_response(status.HTTP_204_NO_CONTENT, "Category deleted")


class StatisticsSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get summary statistics for today, this week, this month, and this year"""
        today = datetime.today().date()
        start_of_week = today - timedelta(days=today.weekday())
        start_of_month = today.replace(day=1)
        start_of_year = today.replace(month=1, day=1)

        # Get data for different periods
        today_stats = self._get_period_summary(request.user, today, today)
        week_stats = self._get_period_summary(request.user, start_of_week, today)
        month_stats = self._get_period_summary(request.user, start_of_month, today)
        year_stats = self._get_period_summary(request.user, start_of_year, today)

        data = {
            'today': today_stats,
            'this_week': week_stats,
            'this_month': month_stats,
            'this_year': year_stats,
            'saldo': request.user.saldo
        }

        return api_response(status.HTTP_200_OK, "Statistics retrieved", data)

    def _get_period_summary(self, user, start_date, end_date):
        # Get income data
        income_data = Transaction.objects.filter(
            user=user,
            type='income',
            date__gte=start_date,
            date__lte=end_date
        ).aggregate(
            total=Sum('amount') or Decimal('0.00'),
            count=Count('id')
        )

        # Get expense data
        expense_data = Transaction.objects.filter(
            user=user,
            type='expense',
            date__gte=start_date,
            date__lte=end_date
        ).aggregate(
            total=Sum('amount') or Decimal('0.00'),
            count=Count('id')
        )

        # Calculate net
        income_total = income_data['total'] or Decimal('0.00')
        expense_total = expense_data['total'] or Decimal('0.00')
        net = income_total - expense_total

        return {
            'income': income_data,
            'expenses': expense_data,
            'net': net
        }


class CategoryStatisticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get transaction statistics per category"""
        period = request.query_params.get('period', 'month')
        transaction_type = request.query_params.get('type', 'expense')
        
        # Determine date range based on period
        today = datetime.today().date()
        if period == 'week':
            start_date = today - timedelta(days=today.weekday())
        elif period == 'month':
            start_date = today.replace(day=1)
        elif period == 'year':
            start_date = today.replace(month=1, day=1)
        elif period == 'all':
            start_date = None
        else:
            return api_response(
                status.HTTP_400_BAD_REQUEST, 
                "Invalid period. Use 'week', 'month', 'year', or 'all'"
            )

        # Base query
        query = Transaction.objects.filter(
            user=request.user,
            type=transaction_type
        )
        
        # Apply date filter if not 'all'
        if start_date:
            query = query.filter(date__gte=start_date, date__lte=today)
        
        # Get total for percentage calculation
        total_amount = query.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Get data per category
        categories = query.values(
            'category__id', 
            'category__name'
        ).annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')
        
        # Calculate percentage and prepare response
        result = []
        for cat in categories:
            percentage = (cat['total'] / total_amount) * 100 if total_amount > 0 else 0
            result.append({
                'category_id': cat['category__id'],
                'category_name': cat['category__name'] or 'Uncategorized',
                'total': cat['total'],
                'count': cat['count'],
                'percentage': round(percentage, 2)
            })
            
        return api_response(
            status.HTTP_200_OK, 
            f"{transaction_type.capitalize()} statistics by category", 
            result
        )


class MonthlyTrendsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get monthly trends for income and expenses"""
        year = request.query_params.get('year', datetime.today().year)
        try:
            year = int(year)
        except ValueError:
            return api_response(status.HTTP_400_BAD_REQUEST, "Invalid year")

        # Get monthly income data
        income_by_month = self._get_monthly_data(request.user, year, 'income')
        
        # Get monthly expense data
        expenses_by_month = self._get_monthly_data(request.user, year, 'expense')
        
        # Combine data
        result = []
        for month in range(1, 13):
            month_name = calendar.month_name[month]
            income = next((x for x in income_by_month if x['month'] == month), {'total': Decimal('0.00')})
            expense = next((x for x in expenses_by_month if x['month'] == month), {'total': Decimal('0.00')})
            
            result.append({
                'month': month,
                'month_name': month_name,
                'income': income['total'],
                'expenses': expense['total'],
                'net': income['total'] - expense['total']
            })
            
        return api_response(status.HTTP_200_OK, f"Monthly trends for {year}", result)

    def _get_monthly_data(self, user, year, transaction_type):
        return list(Transaction.objects.filter(
            user=user,
            type=transaction_type,
            date__year=year
        ).annotate(
            month=F('date__month')
        ).values('month').annotate(
            total=Sum('amount')
        ).order_by('month'))
