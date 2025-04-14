from django.urls import path

from user.views import AcceptFriendRequestView, AddFriendView, BankDetailView, ListFriendsView, PaymentMethodView, SearchFriendView, UserNotificationView, UserProfileView

app_name = 'user'

urlpatterns = [
    path('see-notifications', UserNotificationView.as_view(), name='see_notifications'),

    path('friends/add', AddFriendView.as_view(), name='add_friend'),
    path('friends/accept', AcceptFriendRequestView.as_view(), name='accept_friend'),
    path('friends/search', SearchFriendView.as_view(), name='search_friend'),
    path('friends/list', ListFriendsView.as_view(), name='list_friends'),

    path('profile', UserProfileView.as_view(), name='user_profile'),
    path('profile/payment-method', PaymentMethodView.as_view(), name='payment_method'),
    path("profile/bank-detail", BankDetailView.as_view(), name="bank_detail_create"),
    path("profile/bank-detail/<str:bank_name>", BankDetailView.as_view(), name="bank_detail_delete"), 
]
