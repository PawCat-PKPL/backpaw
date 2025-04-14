from django.urls import path
from admin_dashboard.views import user_list, active_users, inactive_users, delete_user
from user.views import AdminNotificationView, SendNotificationView

app_name = 'admin_dashboard'

urlpatterns = [
    path('users', user_list, name='user_list'),
    path('active-users', active_users, name='active_user_list'),
    path('inactive-users', inactive_users, name='inactive_user_list'),
    path('delete-user/<int:user_id>', delete_user, name='delete_user'),
    
    path('send-notification', SendNotificationView.as_view(), name='send_notification'),
    path('see-notifications', AdminNotificationView.as_view(), name='see_notifications'),
]
