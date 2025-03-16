from django.db import models
from authentication.models import CustomUser

class Notification(models.Model):
    title = models.CharField(max_length=255)
    message = models.TextField()
    sender = models.ForeignKey(CustomUser, related_name='sent_notifications', on_delete=models.CASCADE)
    receiver = models.ForeignKey(CustomUser, related_name='received_notifications', on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
