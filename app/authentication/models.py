from html import escape

from django.contrib.auth.models import AbstractUser
from django.contrib.auth.hashers import make_password, check_password
from django.db import models

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)

    avatar_id = models.PositiveSmallIntegerField(default=1)
    bio = models.TextField(blank=True, null=True)
    friends_count = models.PositiveIntegerField(default=0)
    payment_info = models.CharField(max_length=50, blank=True, null=True)
    
    hex_color = models.CharField(max_length=128, blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'full_name']

    def set_hex_color(self, color):
        self.hex_color = make_password(escape(color))

    def check_hex_color(self, color):
        if not self.hex_color:
            return False
        return check_password(escape(color), self.hex_color)

class PaymentMethod(models.Model):
    PAYMENT_CHOICES = [
        ('gopay', 'GoPay'),
        ('ovo', 'OVO'),
        ('shopeepay', 'ShopeePay'),
        ('bank', 'Bank Transfer'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='payment_methods')
    payment_type = models.CharField(max_length=20, choices=PAYMENT_CHOICES)
    account_number = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.user.email} - {self.payment_type}"
