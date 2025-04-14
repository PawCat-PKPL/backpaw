from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from authentication.models import CustomUser

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('email', 'username', 'full_name', 'is_staff', 'is_active')
    search_fields = ('email', 'username', 'full_name')
    ordering = ('email',)

admin.site.register(CustomUser, CustomUserAdmin)