from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models
from datetime import datetime
from .models import Product, Order, OrderItem
from .utils import validate_phone_number, format_phone_number

DELIVERY_CITIES = {
    'tula': {
        'name': 'Тула',
        'base_price': 100,
        'is_main_city': True,
        'price_per_km': 10
    },
    'moscow': {
        'name': 'Москва',
        'base_price': 300,
        'is_main_city': False,
        'price_per_km': 15
    },
    'other': {
        'name': 'Другой город',
        'base_price': 200,
        'is_main_city': False,
        'price_per_km': 20
    }
}

def calculate_delivery_price(city_key, distance_km=0):
    """Рассчитывает стоимость доставки"""
    if city_key not in DELIVERY_CITIES:
        city_key = 'other'
    
    city = DELIVERY_CITIES[city_key]
    
    if city['is_main_city']:
        # Для основного города - фиксированная цена
        return city['base_price']
    else:
        # Для других городов - базовая цена + цена за км
        return city['base_price'] + (distance_km * city['price_per_km'])

def get_delivery_cities():
    """Возвращает список городов для выбора"""
    return [
        {'key': 'tula', 'name': 'Тула (доставка 100 руб)'},
        {'key': 'moscow', 'name': 'Москва (от 300 руб)'},
        {'key': 'other', 'name': 'Другой город (расчет по расстоянию)'}
    ]

def cart_view(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total_price = 0
    
    # Получаем продукты из БД
    for product_id, quantity in cart.items():
        try:
            product = Product.objects.get(id=int(product_id), is_available=True)
            item_total = float(product.price) * quantity
            cart_items.append({
                'product': {
                    'id': product.id,
                    'title': product.title,
                    'price': float(product.price),
                    'image': product.image
                },
                'quantity': quantity,
                'total': item_total
            })
            total_price += item_total
        except Product.DoesNotExist:
            # Если товар не найден, удаляем его из корзины
            cart.pop(product_id, None)
            request.session['cart'] = cart
            request.session.modified = True
    
    # Получаем информацию о доставке из сессии
    delivery_city = request.session.get('delivery_city', 'tula')
    delivery_distance = request.session.get('delivery_distance', 0)
    delivery_price = calculate_delivery_price(delivery_city, delivery_distance)
    
    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'cart_count': sum(cart.values()),
        'delivery_cities': get_delivery_cities(),
        'delivery_city': delivery_city,
        'delivery_distance': delivery_distance,
        'delivery_price': delivery_price,
        'final_total': total_price + delivery_price
    }
    return render(request, 'cart.html', context)

def update_delivery_info(request):
    """Обновляет информацию о доставке через AJAX"""
    if request.method == 'POST':
        city = request.POST.get('city', 'tula')
        distance = int(request.POST.get('distance', 0))
        
        # Сохраняем в сессии
        request.session['delivery_city'] = city
        request.session['delivery_distance'] = distance
        request.session.modified = True
        
        # Рассчитываем цену доставки
        delivery_price = calculate_delivery_price(city, distance)
        
        return JsonResponse({
            'success': True,
            'delivery_price': delivery_price,
            'city_name': DELIVERY_CITIES.get(city, DELIVERY_CITIES['other'])['name']
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

def add_to_cart(request, product_id):
    try:
        # Принудительно создаем сессию если ее нет
        if not request.session.session_key:
            request.session.create()
            request.session.modified = True
        
        # Убедимся, что сессия активна
        if not request.session.session_key:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Ошибка сессии'
                })
            messages.error(request, 'Ошибка сессии')
            return redirect('menu:menu_list')
        
        # Проверяем существование продукта в БД
        try:
            product = Product.objects.get(id=product_id, is_available=True)
        except Product.DoesNotExist:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Товар не найден или недоступен'
                })
            messages.error(request, 'Товар не найден или недоступен')
            return redirect('menu:menu_list')
        
        cart = request.session.get('cart', {})
        product_id_str = str(product_id)
        
        if product_id_str in cart:
            cart[product_id_str] += 1
        else:
            cart[product_id_str] = 1
        
        # Сохраняем корзину в сессии
        request.session['cart'] = cart
        request.session.modified = True
        
        # Принудительно сохраняем сессию
        request.session.save()

        cart_count = sum(cart.values())
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'cart_count': cart_count,
                'message': f'{product.title} добавлен в корзину'
            })
        
        messages.success(request, f'{product.title} добавлен в корзину')
        return redirect('menu:menu_list')
    
    except Exception as e:
        print(f"Error in add_to_cart: {e}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': 'Ошибка при добавлении в корзину'
            })
        messages.error(request, 'Ошибка при добавлении в корзину')
        return redirect('menu:menu_list')

def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    product_id_str = str(product_id)
    
    # Получаем информацию о продукте для сообщения
    product_name = "Товар"
    try:
        product = Product.objects.get(id=product_id)
        product_name = product.title
    except Product.DoesNotExist:
        pass
    
    if product_id_str in cart:
        del cart[product_id_str]
        request.session['cart'] = cart
        request.session.modified = True
    
    cart_count = sum(cart.values())
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'cart_count': cart_count,
            'message': f'{product_name} удален из корзины'
        })
    
    messages.success(request, f'{product_name} удален из корзины')
    return redirect('menu:cart_view')

def update_cart(request, product_id):
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        cart = request.session.get('cart', {})
        product_id_str = str(product_id)
        
        # Проверяем существование продукта
        try:
            product = Product.objects.get(id=product_id, is_available=True)
        except Product.DoesNotExist:
            messages.error(request, 'Товар не найден или недоступен')
            return redirect('menu:cart_view')
        
        if quantity > 0:
            cart[product_id_str] = quantity
        else:
            if product_id_str in cart:
                del cart[product_id_str]
        
        request.session['cart'] = cart
        request.session.modified = True
    
    cart_count = sum(cart.values())
    return redirect('menu:cart_view')

def clear_cart(request):
    if 'cart' in request.session:
        del request.session['cart']
    
    messages.success(request, 'Корзина очищена')
    return redirect('menu:cart_view')

@login_required
def create_order(request):
    cart = request.session.get('cart', {})
    
    if not cart:
        messages.error(request, 'Корзина пуста')
        return redirect('menu:cart_view')
    
    if request.method != 'POST':
        return redirect('menu:cart_view')
    
    # Получаем информацию о доставке из формы
    delivery_method = request.POST.get('delivery_method', 'pickup')
    delivery_city = request.POST.get('delivery_city', '')
    delivery_distance = int(request.POST.get('delivery_distance', 0))
    customer_name = request.POST.get('customer_name', '').strip()
    customer_phone_raw = request.POST.get('customer_phone', '').strip()
    customer_address = request.POST.get('customer_address', '').strip()
    payment_method = request.POST.get('payment_method', 'cash')
    
    # ВАЛИДАЦИЯ ДАННЫХ
    
    # Проверка имени
    if not customer_name:
        messages.error(request, 'Укажите ваше имя')
        return redirect('menu:cart_view')
    
    if len(customer_name) < 2:
        messages.error(request, 'Имя должно содержать минимум 2 символа')
        return redirect('menu:cart_view')
    
    # Проверка телефона
    is_valid_phone, phone_message = validate_phone_number(customer_phone_raw)
    if not is_valid_phone:
        messages.error(request, f'Ошибка в номере телефона: {phone_message}')
        return redirect('menu:cart_view')
    
    # Форматируем телефон
    customer_phone = format_phone_number(customer_phone_raw)
    
    # Проверка адреса для доставки
    if delivery_method == 'delivery' and not customer_address:
        messages.error(request, 'Укажите адрес доставки')
        return redirect('menu:cart_view')
    
    if delivery_method == 'delivery' and len(customer_address) < 10:
        messages.error(request, 'Адрес доставки должен содержать минимум 10 символов')
        return redirect('menu:cart_view')
    
    # Если пользователь авторизован, используем его данные если не указаны
    if request.user.is_authenticated:
        if not customer_name:
            customer_name = request.user.username or request.user.email.split('@')[0]
    
    # Рассчитываем стоимость доставки
    if delivery_method == 'delivery':
        delivery_price = calculate_delivery_price(delivery_city, delivery_distance)
    else:
        delivery_price = 0
    
    # Рассчитываем общую стоимость товаров из БД
    total_price = 0
    order_items_data = []
    order_items_for_session = []  # Для сохранения в сессии
    
    for product_id, quantity in cart.items():
        try:
            product = Product.objects.get(id=int(product_id), is_available=True)
            item_total = float(product.price) * quantity
            order_items_data.append({
                'product': product,
                'quantity': quantity,
                'total': item_total
            })
            # Сохраняем информацию для сессии
            order_items_for_session.append({
                'product_id': product.id,
                'product_title': product.title,
                'product_price': float(product.price),
                'quantity': quantity,
                'total': item_total
            })
            total_price += item_total
        except Product.DoesNotExist:
            # Пропускаем недоступные товары
            continue
    
    if not order_items_data:
        messages.error(request, 'Все товары в корзине недоступны')
        return redirect('menu:cart_view')
    
    final_total = total_price + delivery_price
    
    # СОХРАНЕНИЕ В БАЗУ ДАННЫХ
    try:
        # Создаем заказ
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            customer_name=customer_name,
            customer_phone=customer_phone,  # Используем отформатированный номер
            customer_address=customer_address,
            payment_method=payment_method,
            delivery_method=delivery_method,
            delivery_city=delivery_city,
            delivery_distance=delivery_distance,
            delivery_price=delivery_price,
            total_price=final_total
        )
        
        # Создаем элементы заказа с ссылкой на продукт
        for item_data in order_items_data:
            OrderItem.objects.create(
                order=order,
                product=item_data['product'],
                product_title=item_data['product'].title,
                product_price=item_data['product'].price,
                quantity=item_data['quantity']
            )
        
        # ВЫВОД В КОНСОЛЬ
        print("=" * 60)
        print("НОВЫЙ ЗАКАЗ СОХРАНЕН В БАЗУ ДАННЫХ:")
        print(f"Номер заказа: #{order.id}")
        print(f"Пользователь: {request.user.email if request.user.is_authenticated else 'Гость'}")
        print(f"Клиент: {customer_name}")
        print(f"Телефон: {customer_phone}")
        print(f"Способ оплаты: {payment_method}")
        print(f"Способ получения: {delivery_method}")
        if delivery_method == 'delivery':
            print(f"Адрес доставки: {customer_address}")
            print(f"Город: {delivery_city}")
            print(f"Расстояние: {delivery_distance} км")
            print(f"Стоимость доставки: {delivery_price} руб.")
        print("Товары:")
        for item in order_items_data:
            print(f"  - {item['product'].title} x {item['quantity']} = {item['total']} руб.")
        print(f"Общая стоимость: {final_total} руб.")
        print(f"Дата заказа: {order.created_at}")
        print("=" * 60)
        
        # Сохраняем заказ в сессии для страницы успеха
        request.session['last_order'] = {
            'id': order.id,
            'customer_name': customer_name,
            'customer_phone': customer_phone,
            'payment_method': payment_method,
            'delivery_method': delivery_method,
            'delivery_city': delivery_city,
            'delivery_distance': delivery_distance,
            'delivery_price': delivery_price,
            'customer_address': customer_address,
            'items': order_items_for_session,
            'total_price': total_price,
            'final_total': final_total,
            'created_at': str(datetime.now())
        }
        request.session.modified = True
        
        # Очищаем корзину после создания заказа
        if 'cart' in request.session:
            del request.session['cart']
        
        messages.success(request, f'Заказ #{order.id} успешно оформлен! Мы свяжемся с вами по телефону {customer_phone} для подтверждения.')
        return redirect('menu:order_success')
        
    except Exception as e:
        print(f"Ошибка при сохранении заказа в БД: {e}")
        messages.error(request, f'Произошла ошибка при оформлении заказа: {str(e)}')
        return redirect('menu:cart_view')

def order_success(request):
    order_data = request.session.get('last_order', {})
    
    if not order_data:
        messages.warning(request, 'Информация о заказе не найдена')
        return redirect('menu:menu_list')
    
    # Формируем данные для шаблона
    order_id = order_data.get('id')
    if order_id:
        try:
            order = Order.objects.get(id=order_id)
            order_items = OrderItem.objects.filter(order=order).select_related('product')
            
            # Используем данные из БД
            order_items_for_template = []
            total_price = 0
            
            for item in order_items:
                item_total = float(item.product_price) * item.quantity
                order_items_for_template.append({
                    'product': {
                        'id': item.product.id if item.product else None,
                        'title': item.product_title,
                        'price': float(item.product_price),
                        'image': item.product.image if item.product else None
                    },
                    'quantity': item.quantity,
                    'total': item_total
                })
                total_price += item_total
            
            # Обновляем данные в сессии
            order_data['total_price'] = total_price
            order_data['final_total'] = float(order.total_price)
            request.session['last_order'] = order_data
            request.session.modified = True
            
            delivery_price = order_data.get('delivery_price', 0)
            final_total = order_data.get('final_total', total_price + delivery_price)
            
        except Order.DoesNotExist:
            # Если заказ не найден в БД, используем данные из сессии
            return get_order_from_session(order_data)
    else:
        # Если нет ID заказа, используем данные из сессии
        return get_order_from_session(order_data)
    
    context = {
        'order': order_data,
        'order_items': order_items_for_template,
        'total_price': total_price,
        'delivery_price': delivery_price,
        'final_total': final_total
    }
    
    return render(request, 'order_success.html', context)

def get_order_from_session(order_data):
    """Получает данные заказа из сессии (запасной вариант)"""
    order_items_for_template = []
    total_price = order_data.get('total_price', 0)
    
    # Получаем информацию о товарах из сессии
    items_from_session = order_data.get('items', [])
    for item in items_from_session:
        # Пытаемся получить продукт из БД по ID
        product = None
        if item.get('product_id'):
            try:
                product = Product.objects.get(id=item['product_id'])
            except Product.DoesNotExist:
                pass
        
        order_items_for_template.append({
            'product': {
                'id': item.get('product_id'),
                'title': item.get('product_title', 'Товар'),
                'price': item.get('product_price', 0),
                'image': product.image if product else None
            },
            'quantity': item.get('quantity', 0),
            'total': item.get('total', 0)
        })
    
    delivery_price = order_data.get('delivery_price', 0)
    final_total = order_data.get('final_total', total_price + delivery_price)
    
    return {
        'order': order_data,
        'order_items': order_items_for_template,
        'total_price': total_price,
        'delivery_price': delivery_price,
        'final_total': final_total
    }

def menu_list(request):
    # Получаем продукты из БД
    products = Product.objects.filter(is_available=True)
    
    # Обработка поиска
    search_query = request.GET.get('search', '')
    filtered_products = products
    
    if search_query:
        filtered_products = products.filter(
            models.Q(title__icontains=search_query) |
            models.Q(description__icontains=search_query) |
            models.Q(full_description__icontains=search_query)
        )
    
    # Форматируем для шаблона
    products_for_template = []
    for product in filtered_products:
        products_for_template.append({
            'id': product.id,
            'title': product.title,
            'description': product.description,
            'price': float(product.price),
            'image': product.image,
            'full_description': product.full_description,
            'ingredients': product.get_ingredients_list(),
            'nutrition': product.get_nutrition_info()
        })
    
    context = {
        'products': products_for_template,
        'title': 'Меню детского кафе "Радуга"',
        'search_query': search_query,
    }
    
    return render(request, 'menu.html', context)

def product_detail(request, product_id):
    try:
        product = Product.objects.get(id=product_id, is_available=True)
        
        context = {
            'product': {
                'id': product.id,
                'title': product.title,
                'description': product.description,
                'price': float(product.price),
                'image': product.image,
                'full_description': product.full_description,
                'ingredients': product.get_ingredients_list(),
                'nutrition': product.get_nutrition_info()
            }
        }
        
        return render(request, 'product_detail.html', context)
        
    except Product.DoesNotExist:
        context = {
            'error_message': 'Товар не найден или временно недоступен'
        }
        return render(request, 'product_not_found.html', context)

# Вспомогательная функция для получения продуктов из БД (для совместимости со старым кодом)
def get_products_from_db():
    """Получает список продуктов из БД (для обратной совместимости)"""
    products = Product.objects.filter(is_available=True)
    return [
        {
            'id': product.id,
            'title': product.title,
            'description': product.description,
            'price': float(product.price),
            'image': product.image,
            'full_description': product.full_description,
            'ingredients': product.get_ingredients_list(),
            'nutrition': product.get_nutrition_info()
        }
        for product in products
    ]

# Псевдоним для обратной совместимости
get_products_list = get_products_from_db