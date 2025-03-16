from django.urls import path

from user.views import UserNotificationView

app_name = 'user'

urlpatterns = [
    path('see-notifications', UserNotificationView.as_view(), name='see_notifications'),
]
