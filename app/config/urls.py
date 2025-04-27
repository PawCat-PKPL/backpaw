from django.contrib import admin
from django.urls import include, path
from authentication.views import hello_pawcat

urlpatterns = [
    path('admin/', admin.site.urls),
    path('hello/', hello_pawcat, name='hello-pawcat'),
    path('api/auth/', include('authentication.urls')),
    path('api/admin/', include('admin_dashboard.urls')),
    path('api/user/', include('user.urls')),
    path('api/dashboard/', include('user_dashboard.urls')),
]
