from django.urls import path
from .views import *

urlpatterns = [
    # Transaction endpoints
    path('transactions', TransactionListCreateView.as_view(), name='transaction-list-create'),
    path('transactions/<int:pk>', TransactionDetailView.as_view(), name='transaction-detail'),

    # Category endpoints
    path('categories', CategoryListCreateView.as_view(), name='category-list-create'),
    path('categories/<int:pk>', CategoryDetailView.as_view(), name='category-detail'),
]