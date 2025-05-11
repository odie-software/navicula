from django.contrib import admin
from .models import UserApplicationSetting

@admin.register(UserApplicationSetting)
class UserApplicationSettingAdmin(admin.ModelAdmin):
    list_display = ('user_identifier', 'app_id', 'updated_at')
    list_filter = ('app_id', 'user_identifier')
    search_fields = ('user_identifier', 'app_id', 'settings')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('user_identifier', 'app_id', 'settings')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
