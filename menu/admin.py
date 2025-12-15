from django.contrib import admin
from django.utils.html import format_html
from .models import Product, Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product_title', 'product_price', 'quantity']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'customer_name', 'total_price', 'delivery_method', 'created_at']
    list_filter = ['delivery_method', 'payment_method', 'created_at']
    search_fields = ['customer_name', 'customer_phone', 'user__email']
    readonly_fields = ['created_at']
    inlines = [OrderItemInline]

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product_link', 'product_title', 'product_price', 'quantity', 'get_total']
    list_filter = ['order']
    search_fields = ['product_title', 'order__id']
    readonly_fields = ['get_total']
    
    def product_link(self, obj):
        if obj.product:
            return format_html('<a href="/admin/menu/product/{}/change/">{}</a>', 
                             obj.product.id, obj.product.title)
        return "—"
    product_link.short_description = 'Товар'
    
    def get_total(self, obj):
        return f"{obj.get_total()} руб."
    get_total.short_description = 'Сумма'

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['title', 'display_price', 'category', 'display_image', 'is_available', 'created_at']
    list_filter = ['category', 'is_available', 'created_at']
    search_fields = ['title', 'description']
    list_editable = ['is_available']
    readonly_fields = ['display_image_preview', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'description', 'full_description', 'price', 'category', 'is_available')
        }),
        ('Изображение', {
            'fields': ('image', 'display_image_preview'),
            'classes': ('collapse',)
        }),
        ('Пищевая ценность', {
            'fields': ('ingredients', 'calories', 'protein', 'carbs'),
            'classes': ('collapse',)
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def display_price(self, obj):
        return f"{obj.price} руб."
    display_price.short_description = 'Цена'
    display_price.admin_order_field = 'price'
    
    def display_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="border-radius: 5px;" />', obj.image)
        return "Нет изображения"
    display_image.short_description = 'Изображение'
    
    def display_image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="200" style="border-radius: 10px; border: 1px solid #ddd;" />', obj.image)
        return "Изображение не загружено"
    display_image_preview.short_description = 'Предпросмотр изображения'
    
    def save_model(self, request, obj, form, change):
        # Автоматически генерируем полное описание, если оно пустое
        if not obj.full_description and obj.description:
            obj.full_description = obj.description
        super().save_model(request, obj, form, change)
    
    class Media:
        css = {
            'all': ('admin/css/product_admin.css',)
        }