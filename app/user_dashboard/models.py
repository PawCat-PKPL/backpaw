from django.db import models
from authentication.models import CustomUser

class Category(models.Model):
    name = models.CharField(max_length=50)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)  # categories are per-user

    def __str__(self):
        return self.name
    
class Transaction(models.Model):
    TRANSACTION_TYPE = (
        ('income', 'Income'),
        ('expense', 'Expense'),
    )

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    type = models.CharField(max_length=7, choices=TRANSACTION_TYPE)
    description = models.TextField(blank=True)
    date = models.DateField()

    def __str__(self):
        return f"{self.type.capitalize()} - {self.amount} on {self.date}"