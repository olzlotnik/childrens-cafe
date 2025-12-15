from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
import re

class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, verbose_name='Пользователь')
    customer_name = models.CharField(max_length=100, verbose_name='Имя клиента')
    customer_phone = models.CharField(max_length=20, verbose_name='Телефон')
    customer_address = models.TextField(blank=True, verbose_name='Адрес доставки')
    payment_method = models.CharField(max_length=20, choices=[
        ('cash', 'Наличными'),
        ('card', 'Картой'),
        ('online', 'Онлайн оплата')
    ], verbose_name='Способ оплаты')
    delivery_method = models.CharField(max_length=20, choices=[
        ('pickup', 'Самовывоз'),
        ('delivery', 'Доставка')
    ], verbose_name='Способ получения')
    delivery_city = models.CharField(max_length=50, blank=True, verbose_name='Город доставки')
    delivery_distance = models.IntegerField(default=0, verbose_name='Расстояние доставки (кm)')
    delivery_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Стоимость доставки')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Общая стоимость')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    def clean(self):
        """Валидация данных перед сохранением"""
        # Валидация телефона
        if self.customer_phone:
            cleaned_phone = re.sub(r'[\s\-()+]', '', self.customer_phone)
            if len(cleaned_phone) not in [10, 11]:
                raise ValidationError({'customer_phone': 'Номер телефона должен содержать 10 или 11 цифр'})
            
            if not cleaned_phone.isdigit():
                raise ValidationError({'customer_phone': 'Номер телефона должен содержать только цифры'})
    
    def save(self, *args, **kwargs):
        # Вызываем clean() перед сохранением
        self.clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Заказ #{self.id} - {self.customer_name}"

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(
        'Product',  # Ссылка на продукт
        on_delete=models.SET_NULL,  # При удалении продукта оставляем запись
        null=True,
        blank=True,
        verbose_name='Товар'
    )
    product_title = models.CharField(max_length=200, verbose_name='Название товара')
    product_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена товара')
    quantity = models.IntegerField(verbose_name='Количество')
    
    def __str__(self):
        return f"{self.product_title} x {self.quantity} (заказ #{self.order.id})"
    
    def save(self, *args, **kwargs):
        # Автоматически заполняем название и цену из продукта, если он указан
        if self.product and not self.product_title:
            self.product_title = self.product.title
        if self.product and not self.product_price:
            self.product_price = self.product.price
        super().save(*args, **kwargs)

    def get_total(self):
        """Возвращает общую стоимость позиции"""
        return self.product_price * self.quantity

    class Meta:
        verbose_name = 'Элемент заказа'
        verbose_name_plural = 'Элементы заказа'
        ordering = ['-id']

class Product(models.Model):
    """Модель для товаров/продуктов"""
    CATEGORY_CHOICES = [
        ('breakfast', 'Завтраки'),
        ('main', 'Основные блюда'),
        ('salad', 'Салаты'),
        ('drink', 'Напитки'),
        ('dessert', 'Десерты'),
        ('child', 'Детские блюда'),
    ]
    
    title = models.CharField(max_length=200, verbose_name='Название')
    description = models.TextField(verbose_name='Описание')
    full_description = models.TextField(blank=True, verbose_name='Полное описание')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена')
    category = models.CharField(
        max_length=20, 
        choices=CATEGORY_CHOICES, 
        default='main',
        verbose_name='Категория'
    )
    image = models.URLField(max_length=500, blank=True, verbose_name='Ссылка на изображение')
    ingredients = models.TextField(blank=True, verbose_name='Состав (через запятую)')
    calories = models.IntegerField(null=True, blank=True, verbose_name='Калории')
    protein = models.CharField(max_length=50, blank=True, verbose_name='Белки')
    carbs = models.CharField(max_length=50, blank=True, verbose_name='Углеводы')
    is_available = models.BooleanField(default=True, verbose_name='В наличии')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    def get_ingredients_list(self):
        """Возвращает список ингредиентов"""
        if self.ingredients:
            return [ing.strip() for ing in self.ingredients.split(',')]
        return []
    
    def get_nutrition_info(self):
        """Возвращает информацию о пищевой ценности"""
        return {
            'calories': f'{self.calories} ккал' if self.calories else 'Не указано',
            'protein': f'{self.protein}г' if self.protein else 'Не указано',
            'carbs': f'{self.carbs}г' if self.carbs else 'Не указано'
        }
    
    def __str__(self):
        return f"{self.title} - {self.price} руб."
    
    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        ordering = ['category', 'title']
        indexes = [
            models.Index(fields=['is_available']),
            models.Index(fields=['category', 'is_available']),
            models.Index(fields=['title']),
            models.Index(fields=['price']),
        ]