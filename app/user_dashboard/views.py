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

            user.refresh_from_db()

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
        return api_response(status.HTTP_200_OK, "Category deleted")


class StatisticsSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get summary statistics for today, this week, this month, and this year"""
        today = datetime.today().date()
        start_of_week = today - timedelta(days=today.weekday())
        start_of_month = today.replace(day=1)
        start_of_year = today.replace(month=1, day=1)

        # Ambil data per periode
        today_stats = self._get_period_summary(request.user, today, today, by='day')
        week_stats = self._get_period_summary(request.user, start_of_week, today, by='week')
        month_stats = self._get_period_summary(request.user, start_of_month, today, by='month')
        year_stats = self._get_period_summary(request.user, start_of_year, today, by='year')

        data = {
            'today': today_stats,
            'this_week': week_stats,
            'this_month': month_stats,
            'this_year': year_stats,
            'saldo': request.user.saldo
        }

        return api_response(status.HTTP_200_OK, "Statistics retrieved", data)

    def _get_period_summary(self, user, start_date, end_date, by='day'):
        filters = {'user': user}

        if by == 'day':
            filters['date'] = start_date
        elif by == 'week':
            filters['date__year'] = start_date.isocalendar()[0]
            filters['date__week'] = start_date.isocalendar()[1]
        elif by == 'month':
            filters['date__year'] = start_date.year
            filters['date__month'] = start_date.month
        elif by == 'year':
            filters['date__year'] = start_date.year
        else:
            filters['date__range'] = (start_date, end_date)

        income_data = Transaction.objects.filter(
            **filters,
            type='income'
        ).aggregate(
            total=Sum('amount'),
            count=Count('id')
        )

        expense_data = Transaction.objects.filter(
            **filters,
            type='expense'
        ).aggregate(
            total=Sum('amount'),
            count=Count('id')
        )
     

        income_total = income_data['total'] or Decimal('0.00')
        expense_total = expense_data['total'] or Decimal('0.00')
        
        net = income_total - expense_total

        return {
            'income': {
                'total': income_total,
                'count': income_data['count']
            },
            'expenses': {
                'total': expense_total,
                'count': expense_data['count']
            },
            'net': net
        }

class CategoryStatisticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get transaction statistics per category for the current month"""
        transaction_type = request.query_params.get('type', 'expense')
        
        # Determine the date range for the current month
        today = datetime.today().date()
        start_date = today.replace(day=1)  # First day of the current month

        # Base query to filter transactions for the current month and specified type
        query = Transaction.objects.filter(
            user=request.user,
            type=transaction_type,
            date__gte=start_date,  # Filter from the first day of the current month
            date__lte=today  # Filter until today
        )
        
        # Get total for percentage calculation
        total_amount = query.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Get data per category (ID, name, total, and transaction count)
        categories = query.values(
            'category__id', 
            'category__name'
        ).annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')
        
        # Calculate percentage and prepare the response data
        result = []
        for cat in categories:
            percentage = (cat['total'] / total_amount) * 100 if total_amount > 0 else 0
            result.append({
                'category_id': cat['category__id'],
                'category_name': cat['category__name'] or 'Uncategorized',  # Handle empty category name
                'total': cat['total'],
                'count': cat['count'],
                'percentage': round(percentage, 2)  # Round percentage to two decimal places
            })
        

        # Return the response with the statistics
        return api_response(
            status.HTTP_200_OK, 
            f"{transaction_type.capitalize()} statistics by category for {today.strftime('%B %Y')}", 
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
