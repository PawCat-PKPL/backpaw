from django.urls import path

from authentication.views import ForgotPasswordView, LoginView, RegisterView, LogoutView, CookieTokenRefreshView, UserInfoView

app_name = 'authentication'

urlpatterns = [
    path('register', RegisterView.as_view(), name='register'),
    path('login', LoginView.as_view(), name='login'),
    path('logout', LogoutView.as_view(), name='logout'),
    path('forgot-password', ForgotPasswordView.as_view(), name='forgot_password'),
    path('refresh', CookieTokenRefreshView.as_view(), name='token_refresh'),
    path('user-info', UserInfoView.as_view(), name='user_info'),
]
