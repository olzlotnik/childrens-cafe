from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Product, Order
from .utils import validate_phone_number, format_phone_number

User = get_user_model()

class MenuTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.product = Product.objects.create(
            title='Детский завтрак',
            description='Каша молочная с ягодами',
            price=250.00,
            category='breakfast',
            is_available=True
        )
    
    def test_add_to_cart_session(self):
        """Тест добавления товара в корзину через сессию"""
        url = reverse('menu:add_to_cart', args=[self.product.id])
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 302)
        
        # Проверяем сессию
        cart = self.client.session.get('cart', {})
        self.assertEqual(cart.get(str(self.product.id)), 1)
    
    def test_cart_clearing(self):
        """Тест очистки корзины"""
        session = self.client.session
        session['cart'] = {str(self.product.id): 2}
        session.save()
        
        url = reverse('menu:clear_cart')
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 302)
        self.assertNotIn('cart', self.client.session)
    
    def test_order_creation(self):
        """Тест создания заказа с доставкой"""
        self.client.login(email='test@example.com', password='testpass123')
        
        # Добавляем товар в корзину
        session = self.client.session
        session['cart'] = {str(self.product.id): 2}
        session['delivery_city'] = 'tula'
        session['delivery_distance'] = 0
        session.save()
        
        url = reverse('menu:create_order')
        response = self.client.post(url, {
            'delivery_method': 'delivery',
            'delivery_city': 'tula',
            'delivery_distance': 0,
            'customer_name': 'Иван Иванов',
            'customer_phone': '+7 (999) 123-45-67',
            'customer_address': 'ул. Ленина, д. 10, кв. 5',
            'payment_method': 'cash'
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Order.objects.filter(customer_name='Иван Иванов').exists())
    
    def test_phone_validation(self):
        """Тест валидации телефона"""
        valid_phones = [
            '+79991234567',
            '89991234567',
            '7 999 123-45-67',
            '+7 (999) 123-45-67'
        ]
        
        invalid_phones = [
            '12345',
            'abcde',
            '+7999123456789',  # Слишком длинный
            '+79991234'        # Слишком короткий
        ]
        
        for phone in valid_phones:
            is_valid, _ = validate_phone_number(phone)
            self.assertTrue(is_valid, f"Телефон {phone} должен быть валидным")
        
        for phone in invalid_phones:
            is_valid, _ = validate_phone_number(phone)
            self.assertFalse(is_valid, f"Телефон {phone} должен быть невалидным")
    
    def test_delivery_calculation(self):
        """Тест расчета стоимости доставки"""
        from .views import calculate_delivery_price
        
        # Доставка по Туле (основной город)
        tula_price = calculate_delivery_price('tula', 0)
        self.assertEqual(tula_price, 100)
        
        # Доставка в Москву (базовая цена + за км)
        moscow_price = calculate_delivery_price('moscow', 10)
        self.assertEqual(moscow_price, 300 + (10 * 15))  # 450
        
        # Доставка в другой город
        other_price = calculate_delivery_price('other', 5)
        self.assertEqual(other_price, 200 + (5 * 20))  # 300
    
    def test_menu_view(self):
        """Тест отображения меню"""
        url = reverse('menu:menu_list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Детский завтрак')
    
    def test_product_detail_view(self):
        """Тест детальной страницы товара"""
        url = reverse('menu:product_detail', args=[self.product.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Детский завтрак')
        self.assertContains(response, '250')