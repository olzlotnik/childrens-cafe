from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        if not extra_fields.get('username'):
            extra_fields['username'] = email.split('@')[0]

        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True, verbose_name='Email адрес')
    
    # Делаем email в качестве идентификатора для входа
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # Убираем username из REQUIRED_FIELDS
    
    objects = CustomUserManager()
    
    def __str__(self):
        return self.email

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
    
    # ВАЖНО: Для совместимости с PasswordResetTokenGenerator
    def get_username(self):
        return self.email

class CafeRating(models.Model):
    FOOD_TASTE_CHOICES = [
        ('excellent', 'Очень вкусная'),
        ('good', 'Вкусная'),
        ('average', 'Нормальная'),
        ('poor', 'Не очень'),
        ('bad', 'Не вкусная'),
    ]
    
    PORTION_SIZE_CHOICES = [
        ('large', 'Очень большие'),
        ('normal', 'Нормальные'),
        ('small', 'Маленькие'),
    ]
    
    SPEED_SERVICE_CHOICES = [
        ('fast', 'Очень быстро'),
        ('normal', 'Нормально'),
        ('slow', 'Медленно'),
        ('very_slow', 'Очень медленно'),
    ]
    
    STAFF_FRIENDLINESS_CHOICES = [
        ('excellent', 'Очень вежливые'),
        ('good', 'Вежливые'),
        ('average', 'Нормальные'),
        ('poor', 'Не очень вежливые'),
    ]
    
    PRICE_QUALITY_CHOICES = [
        ('excellent', 'Отличное'),
        ('good', 'Хорошее'),
        ('fair', 'Удовлетворительное'),
        ('poor', 'Плохое'),
    ]
    
    CHILD_FRIENDLY_CHOICES = [
        ('excellent', 'Отлично'),
        ('good', 'Хорошо'),
        ('average', 'Нормально'),
        ('poor', 'Плохо'),
    ]
    
    RECOMMEND_CHOICES = [
        ('yes', 'Да, обязательно'),
        ('maybe', 'Возможно'),
        ('no', 'Нет'),
    ]
    
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, verbose_name='Пользователь')
    
    # Основные критерии (звезды)
    food_quality = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='Качество еды'
    )
    service_quality = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='Качество обслуживания'
    )
    atmosphere = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='Атмосфера'
    )
    cleanliness = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='Чистота'
    )
    
    # Дополнительные критерии (выбор)
    food_taste = models.CharField(
        max_length=20, 
        choices=FOOD_TASTE_CHOICES,
        verbose_name='Вкус еды'
    )
    portion_size = models.CharField(
        max_length=20, 
        choices=PORTION_SIZE_CHOICES,
        verbose_name='Размер порций'
    )
    speed_service = models.CharField(
        max_length=20, 
        choices=SPEED_SERVICE_CHOICES,
        verbose_name='Скорость обслуживания'
    )
    staff_friendliness = models.CharField(
        max_length=20, 
        choices=STAFF_FRIENDLINESS_CHOICES,
        verbose_name='Вежливость персонала'
    )
    price_quality = models.CharField(
        max_length=20, 
        choices=PRICE_QUALITY_CHOICES,
        verbose_name='Соотношение цены и качества'
    )
    child_friendly = models.CharField(
        max_length=20, 
        choices=CHILD_FRIENDLY_CHOICES,
        verbose_name='Удобство для детей'
    )
    
    # Рекомендация
    recommend = models.CharField(
        max_length=10, 
        choices=RECOMMEND_CHOICES,
        verbose_name='Рекомендация'
    )
    
    # Комментарий
    comment = models.TextField(blank=True, max_length=500, verbose_name='Комментарий')
    
    # Общая оценка (вычисляемое поле)
    overall_rating = models.FloatField(verbose_name='Общая оценка')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    
    def save(self, *args, **kwargs):
        # Вычисляем общую оценку как среднее основных критериев
        self.overall_rating = (
            self.food_quality + 
            self.service_quality + 
            self.atmosphere + 
            self.cleanliness
        ) / 4.0
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Оценка от {self.user.email} - {self.overall_rating:.1f}/5"

    class Meta:
        verbose_name = 'Оценка кафе'
        verbose_name_plural = 'Оценки кафе'
        ordering = ['-created_at']

class Booking(models.Model):
    EVENT_TYPE_CHOICES = [
        ('birthday', 'День рождения'),
        ('holiday', 'Праздник'),
        ('graduation', 'Выпускной'),
        ('other', 'Другое'),
    ]
    
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, verbose_name='Пользователь')
    
    # Дата и время мероприятия
    event_date = models.DateField(verbose_name='Дата мероприятия')
    event_time = models.TimeField(verbose_name='Время начала')
    event_duration = models.IntegerField(
        verbose_name='Продолжительность (часы)',
        default=2,
        validators=[MinValueValidator(1), MaxValueValidator(8)]
    )
    
    # Расчетное время окончания
    event_end_time = models.TimeField(verbose_name='Время окончания', blank=True, null=True)
    
    # Детали мероприятия
    guests_count = models.IntegerField(
        verbose_name='Количество гостей',
        validators=[MinValueValidator(1), MaxValueValidator(50)]
    )
    event_type = models.CharField(
        max_length=20,
        choices=EVENT_TYPE_CHOICES,
        verbose_name='Тип мероприятия'
    )
    
    # Дополнительные услуги
    services = models.JSONField(
        verbose_name='Дополнительные услуги',
        default=list,
        help_text='Список выбранных услуг'
    )
    
    # Контактная информация
    phone = models.CharField(max_length=20, verbose_name='Контактный телефон')
    comments = models.TextField(blank=True, verbose_name='Дополнительные пожелания')
    
    # Статус бронирования
    STATUS_CHOICES = [
        ('pending', 'Ожидает подтверждения'),
        ('confirmed', 'Подтверждено'),
        ('cancelled', 'Отменено'),
        ('completed', 'Завершено'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Статус'
    )
    
    # Расчет стоимости
    base_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=5000.00,
        verbose_name='Базовая стоимость'
    )
    services_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name='Стоимость услуг'
    )
    total_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=5000.00,
        verbose_name='Общая стоимость'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    def save(self, *args, **kwargs):
        # Рассчитываем время окончания
        from datetime import datetime, timedelta
        start_datetime = datetime.combine(self.event_date, self.event_time)
        end_datetime = start_datetime + timedelta(hours=self.event_duration)
        self.event_end_time = end_datetime.time()
        
        # Рассчитываем стоимость
        self.calculate_cost()
        
        super().save(*args, **kwargs)
    
    def calculate_cost(self):
        """Расчет стоимости бронирования"""
        # Базовая стоимость (5000 руб за 2 часа)
        base_hourly_rate = 2500  # руб/час
        self.base_cost = base_hourly_rate * self.event_duration
        
        # Стоимость дополнительных услуг
        services_prices = {
            'animator': 1000,
            'cake': 1500,
            'decorations': 2000,
            'photographer': 2500,
        }
        
        self.services_cost = sum(services_prices.get(service, 0) for service in self.services)
        self.total_cost = self.base_cost + self.services_cost
    
    def is_time_slot_available(self):
        """Проверка, свободен ли временной слот"""
        from datetime import datetime, timedelta
        from django.utils import timezone
        
        # Получаем дату и время начала
        start_datetime = datetime.combine(self.event_date, self.event_time)
        end_datetime = start_datetime + timedelta(hours=self.event_duration)
        
        # Ищем пересекающиеся бронирования
        overlapping_bookings = Booking.objects.filter(
            event_date=self.event_date,
            status__in=['pending', 'confirmed']
        ).exclude(id=self.id)
        
        for booking in overlapping_bookings:
            booking_start = datetime.combine(booking.event_date, booking.event_time)
            booking_end = datetime.combine(booking.event_date, booking.event_end_time)
            
            # Проверяем пересечение временных интервалов
            if (start_datetime < booking_end) and (end_datetime > booking_start):
                return False
        
        return True
    
    def __str__(self):
        return f"Бронирование #{self.id} от {self.user.email} на {self.event_date} {self.event_time}"
    
    class Meta:
        verbose_name = 'Бронирование мероприятия'
        verbose_name_plural = 'Бронирования мероприятий'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event_date', 'event_time']),
            models.Index(fields=['status']),
        ]