from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, CafeRating
from .models import Booking

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'first_name', 'last_name', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('username', 'first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )

@admin.register(CafeRating)
class CafeRatingAdmin(admin.ModelAdmin):
    list_display = ('user', 'overall_rating', 'food_quality', 'service_quality', 'recommend', 'created_at')
    list_filter = ('food_quality', 'service_quality', 'recommend', 'created_at')
    search_fields = ('user__email', 'user__username', 'comment')
    readonly_fields = ('created_at', 'overall_rating')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'created_at', 'overall_rating')
        }),
        ('Основные критерии (звезды)', {
            'fields': ('food_quality', 'service_quality', 'atmosphere', 'cleanliness')
        }),
        ('Дополнительные оценки', {
            'fields': (
                'food_taste', 
                'portion_size', 
                'speed_service', 
                'staff_friendliness',
                'price_quality',
                'child_friendly'
            )
        }),
        ('Рекомендация и комментарий', {
            'fields': ('recommend', 'comment')
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('user',)
        return self.readonly_fields

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'event_date', 'event_time', 'event_type', 'guests_count', 'status', 'total_cost')
    list_filter = ('status', 'event_type', 'event_date', 'created_at')
    search_fields = ('user__email', 'user__username', 'phone', 'comments')
    readonly_fields = ('created_at', 'updated_at', 'event_end_time', 'base_cost', 'services_cost', 'total_cost')
    date_hierarchy = 'event_date'
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'status', 'created_at', 'updated_at')
        }),
        ('Детали мероприятия', {
            'fields': (
                'event_date', 
                'event_time', 
                'event_end_time',
                'event_duration',
                'guests_count', 
                'event_type',
                'comments'
            )
        }),
        ('Контактная информация', {
            'fields': ('phone',)
        }),
        ('Стоимость', {
            'fields': ('base_cost', 'services_cost', 'total_cost')
        }),
        ('Дополнительные услуги', {
            'fields': ('services',),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('user', 'services')
        return self.readonly_fields