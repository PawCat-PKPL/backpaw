from django.urls import path

from user.views import AcceptFriendRequestView, AddFriendView, ListFriendsView, SearchFriendView, UserNotificationView

app_name = 'user'

urlpatterns = [
    path('see-notifications', UserNotificationView.as_view(), name='see_notifications'),
    path('friends/add', AddFriendView.as_view(), name='add_friend'),
    path('friends/accept', AcceptFriendRequestView.as_view(), name='accept_friend'),
    path('friends/search', SearchFriendView.as_view(), name='search_friend'),
    path('friends/list', ListFriendsView.as_view(), name='list_friends'),
]
