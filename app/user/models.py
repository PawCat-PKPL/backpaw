from django.db import models
from django.forms import ValidationError

from authentication.models import CustomUser

class Notification(models.Model):
    title = models.CharField(max_length=255)
    message = models.TextField()
    sender = models.ForeignKey(CustomUser, related_name='sent_notifications', on_delete=models.CASCADE)
    receiver = models.ForeignKey(CustomUser, related_name='received_notifications', on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Friendship(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]

    sender = models.ForeignKey(CustomUser, related_name="sent_requests", on_delete=models.CASCADE)
    receiver = models.ForeignKey(CustomUser, related_name="received_requests", on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('sender', 'receiver')  # Mencegah duplikasi request yang sama

    def clean(self):
        if self.sender == self.receiver:
            raise ValidationError("Cannot add yourself as a friend")
        
    def __str__(self):
        return f"{self.sender} -> {self.receiver} ({self.status})"