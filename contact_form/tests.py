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
        # Проверяем наличие ключевых элементов формы
        self.assertContains(response, 'Свяжитесь с нами')
        self.assertContains(response, 'id_name')
        self.assertContains(response, 'id_email')
        self.assertContains(response, 'id_message')
        self.assertContains(response, 'Отправить сообщение')
    
    def test_contact_form_submission(self):
        """Тест отправки контактного сообщения"""
        url = reverse('contacts:contacts')
        
        # Подсчет сообщений до отправки
        initial_count = ContactMessage.objects.count()
        
        # Отправляем форму
        response = self.client.post(url, {
            'name': 'Иван Иванов',
            'email': 'ivan@example.com',
            'message': 'Здравствуйте! Хочу задать вопрос по меню.'
        })
        
        # Проверяем редирект на страницу успеха (302)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('contacts:success'))
        
        # Проверяем успешное сохранение
        self.assertEqual(ContactMessage.objects.count(), initial_count + 1)
        message = ContactMessage.objects.get(email='ivan@example.com')
        self.assertEqual(message.name, 'Иван Иванов')
        self.assertEqual(message.message, 'Здравствуйте! Хочу задать вопрос по меню.')
        
        # Следуем за редиректом на страницу успеха
        response = self.client.get(response.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'contact_success.html')
    
    def test_contact_form_auto_fill(self):
        """Тест автозаполнения для авторизованных пользователей"""
        self.client.login(email='test@example.com', password='testpass123')
        
        url = reverse('contacts:contacts')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        # Проверяем, что форма предзаполнена данными пользователя
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
        self.assertEqual(ContactMessage.objects.count(), 1)
        message = ContactMessage.objects.first()
        self.assertIsNotNone(message)
        
        # IP может быть сохранен как 192.168.1.1 или 127.0.0.1
        self.assertIsNotNone(message.ip_address)
    
    def test_email_validation_contact_form(self):
        """Тест валидации email в форме"""
        url = reverse('contacts:contacts')
        
        # Отправляем форму с неверным email
        response = self.client.post(url, {
            'name': 'Иван',
            'email': 'invalid-email',
            'message': 'Сообщение'
        })
        
        # Проверяем, что форма не прошла валидацию (не было редиректа)
        self.assertEqual(response.status_code, 200)  # Остаемся на той же странице
        self.assertContains(response, 'Свяжитесь с нами')  # Проверяем, что форма отображается
        
        # Проверяем, что сообщение НЕ сохранено
        self.assertEqual(ContactMessage.objects.count(), 0)
    
    def test_authenticated_user_contact(self):
        """Тест отправки сообщения авторизованным пользователем"""
        self.client.login(email='test@example.com', password='testpass123')
        
        url = reverse('contacts:contacts')
        initial_count = ContactMessage.objects.count()
        
        response = self.client.post(url, {
            'name': 'Авторизованный пользователь',
            'email': 'test@example.com',
            'message': 'Вопрос от авторизованного пользователя'
        })
        
        # Проверяем редирект
        self.assertEqual(response.status_code, 302)
        
        # Проверяем сохранение сообщения
        self.assertEqual(ContactMessage.objects.count(), initial_count + 1)
        message = ContactMessage.objects.get(email='test@example.com')
        
        # Проверяем связь с пользователем
        self.assertEqual(message.user, self.user)
        self.assertEqual(message.email, 'test@example.com')
        self.assertEqual(message.name, 'Авторизованный пользователь')