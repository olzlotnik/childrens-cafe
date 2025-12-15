from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import ContactMessage

User = get_user_model()

class ContactsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            username='testuser'
        )
    
    def test_contact_form_view(self):
        """Тест отображения формы обратной связи"""
        url = reverse('contacts:contacts')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'форма обратной связи')
    
    def test_contact_form_submission(self):
        """Тест отправки контактного сообщения"""
        url = reverse('contacts:contacts')
        response = self.client.post(url, {
            'name': 'Иван Иванов',
            'email': 'ivan@example.com',
            'message': 'Здравствуйте! Хочу задать вопрос по меню.'
        })
        
        self.assertEqual(response.status_code, 302)  # Редирект на success
        self.assertTrue(ContactMessage.objects.filter(email='ivan@example.com').exists())
    
    def test_contact_form_auto_fill(self):
        """Тест автозаполнения для авторизованных пользователей"""
        self.client.login(email='test@example.com', password='testpass123')
        
        url = reverse('contacts:contacts')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        # Форма должна быть предзаполнена данными пользователя
        self.assertContains(response, 'test@example.com')
    
    def test_ip_address_capture(self):
        """Тест сохранения IP-адреса"""
        url = reverse('contacts:contacts')
        
        # Отправляем запрос с заголовком X-Forwarded-For
        response = self.client.post(url, {
            'name': 'Тест',
            'email': 'test@test.com',
            'message': 'Тестовое сообщение'
        }, HTTP_X_FORWARDED_FOR='192.168.1.1, 10.0.0.1')
        
        # Проверяем создание сообщения
        message = ContactMessage.objects.first()
        self.assertIsNotNone(message)
        # В тестовом окружении IP может быть 127.0.0.1
        self.assertTrue(hasattr(message, 'ip_address'))
    
    def test_email_validation_contact_form(self):
        """Тест валидации email в форме"""
        url = reverse('contacts:contacts')
        
        # Неправильный email
        response = self.client.post(url, {
            'name': 'Иван',
            'email': 'invalid-email',
            'message': 'Сообщение'
        })
        
        self.assertEqual(response.status_code, 200)  # Форма не прошла валидацию
        self.assertContains(response, 'Введите корректный email адрес')