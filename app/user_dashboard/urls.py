from django.urls import path
from .views import *

app_name = 'user_dashboard'

urlpatterns = [
    # Transaction endpoints
    path('transactions', TransactionListCreateView.as_view(), name='transaction-list-create'),
    path('transactions/<int:pk>', TransactionDetailView.as_view(), name='transaction-detail'),

    # Category endpoints
    path('categories', CategoryListCreateView.as_view(), name='category-list-create'),
    path('categories/<int:pk>', CategoryDetailView.as_view(), name='category-detail'),

    # Statistics endpoints
    path('statistics/summary', StatisticsSummaryView.as_view(), name='statistics-summary'),
    path('statistics/categories', CategoryStatisticsView.as_view(), name='statistics-categories'),
    path('statistics/monthly-trends', MonthlyTrendsView.as_view(), name='statistics-monthly-trends'),
]