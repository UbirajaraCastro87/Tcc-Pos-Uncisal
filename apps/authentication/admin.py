
# Register your models here.
from django.contrib import admin
from .models import UserAccessLog

@admin.register(UserAccessLog)
class UserAccessLogAdmin(admin.ModelAdmin):
    list_display = ('username', 'login_time', 'logout_time', 'duration', 'ip_address')
    search_fields = ('username', 'ip_address')
