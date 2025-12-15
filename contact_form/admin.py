from django.contrib import admin
from .models import ContactMessage

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'user', 'created_at', 'ip_address')
    list_filter = ('created_at', 'user')
    search_fields = ('name', 'email', 'message', 'user__email')
    readonly_fields = ('created_at', 'ip_address')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Информация о сообщении', {
            'fields': ('name', 'email', 'message', 'created_at', 'ip_address')
        }),
        ('Связь с пользователем', {
            'fields': ('user',),
            'classes': ('collapse',)
        }),
    )