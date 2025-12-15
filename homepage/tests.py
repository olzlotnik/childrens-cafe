from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import CafeRating, Booking
from datetime import datetime, timedelta, date

User = get_user_model()

class HomepageTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            username='testuser'
        )
    
    def test_custom_user_creation(self):
        """Проверка создания пользователя с email"""
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertEqual(self.user.get_username(), 'test@example.com')
        self.assertTrue(self.user.check_password('testpass123'))
    
    def test_user_registration_view(self):
        """Тест регистрации пользователя через форму"""
        url = reverse('homepage:register')
        response = self.client.post(url, {
            'email': 'newuser@example.com',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
            'username': 'newuser'
        })
        self.assertEqual(response.status_code, 302)  # Редирект после успеха
        self.assertTrue(User.objects.filter(email='newuser@example.com').exists())
    
    def test_user_login_view(self):
        """Тест входа пользователя"""
        url = reverse('homepage:login')
        response = self.client.post(url, {
            'username': 'test@example.com',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)  # Редирект после успешного входа
    
    def test_profile_requires_login(self):
        """Профиль недоступен без авторизации"""
        url = reverse('homepage:profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Редирект на логин
    
    def test_cafe_rating_creation(self):
        """Тест создания оценки кафе"""
        self.client.login(email='test@example.com', password='testpass123')
        
        rating = CafeRating.objects.create(
            user=self.user,
            food_quality=5,
            service_quality=4,
            atmosphere=5,
            cleanliness=4,
            food_taste='excellent',
            portion_size='normal',
            speed_service='fast',
            staff_friendliness='excellent',
            price_quality='good',
            child_friendly='excellent',
            recommend='yes',
            comment='Отличное кафе!'
        )
        
        self.assertEqual(rating.overall_rating, 4.5)  # (5+4+5+4)/4 = 4.5
        self.assertEqual(rating.user.email, 'test@example.com')
    
    def test_booking_creation(self):
        """Тест создания бронирования"""
        self.client.login(email='test@example.com', password='testpass123')
        
        future_date = date.today() + timedelta(days=7)
        booking = Booking.objects.create(
            user=self.user,
            event_date=future_date,
            event_time=datetime.strptime('14:00', '%H:%M').time(),
            event_duration=2,
            guests_count=10,
            event_type='birthday',
            phone='+79991234567',
            services=['animator', 'cake']
        )
        
        self.assertEqual(booking.status, 'pending')
        self.assertEqual(booking.guests_count, 10)
        self.assertEqual(booking.event_type, 'birthday')
        self.assertIn('animator', booking.services)
    
    def test_booking_time_availability(self):
        """Тест проверки доступности времени"""
        future_date = date.today() + timedelta(days=7)
        
        # Создаем первое бронирование
        booking1 = Booking.objects.create(
            user=self.user,
            event_date=future_date,
            event_time=datetime.strptime('14:00', '%H:%M').time(),
            event_duration=2,
            guests_count=10,
            event_type='birthday',
            phone='+79991234567'
        )
        
        # Пытаемся создать пересекающееся бронирование
        booking2 = Booking(
            user=self.user,
            event_date=future_date,
            event_time=datetime.strptime('15:00', '%H:%M').time(),
            event_duration=2,
            guests_count=8,
            event_type='holiday',
            phone='+79997654321'
        )
        
        self.assertFalse(booking2.is_time_slot_available())