from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from .models import CafeRating
from menu.models import Order
from .forms import CustomUserCreationForm, CustomAuthenticationForm
from django.contrib.auth import update_session_auth_hash
from .forms import CustomPasswordChangeForm, CustomPasswordResetForm, CustomSetPasswordForm
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string
from .models import Booking
from .forms import BookingForm
from django.http import JsonResponse
import json
from datetime import datetime, date, timedelta

User = get_user_model()

def index(request):
    # Показываем все отзывы на главной
    ratings = CafeRating.objects.all().order_by('-created_at')[:10]

    # Для формы бронирования
    today = date.today()
    max_date = today + timedelta(days=90)

    context = {
        'ratings': ratings,
        'today': today,
        'max_date': max_date,
    }
    return render(request, 'index.html', context)

@login_required
def rate_cafe(request):
    if request.method == 'POST':
        try:
            # Получаем все данные из формы
            rating_data = {
                'food_quality': int(request.POST.get('food_quality')),
                'service_quality': int(request.POST.get('service_quality')),
                'atmosphere': int(request.POST.get('atmosphere')),
                'cleanliness': int(request.POST.get('cleanliness')),
                'food_taste': request.POST.get('food_taste', ''),
                'portion_size': request.POST.get('portion_size', ''),
                'speed_service': request.POST.get('speed_service', ''),
                'staff_friendliness': request.POST.get('staff_friendliness', ''),
                'price_quality': request.POST.get('price_quality', ''),
                'child_friendly': request.POST.get('child_friendly', ''),
                'recommend': request.POST.get('recommend'),
                'comment': request.POST.get('comment', ''),
            }
            
            # Сохраняем оценку в БД
            rating = CafeRating.objects.create(
                user=request.user,
                **rating_data
            )
            
            messages.success(request, 'Спасибо за вашу оценку!')
            return redirect('homepage:profile')
            
        except Exception as e:
            messages.error(request, f'Произошла ошибка: {str(e)}')
            return render(request, 'rate_cafe.html')
    
    return render(request, 'rate_cafe.html')

@login_required
def profile(request):
    if request.method == 'POST':
        # Обновление профиля
        new_username = request.POST.get('username', '').strip()
        if new_username:
            request.user.username = new_username
            request.user.save()
            messages.success(request, 'Имя пользователя успешно обновлено!')
        return redirect('homepage:profile')
    
    # Получаем отзывы, заказы и бронирования
    user_ratings = CafeRating.objects.filter(user=request.user).order_by('-created_at')
    user_orders = Order.objects.filter(user=request.user).order_by('-created_at')
    user_bookings = Booking.objects.filter(user=request.user).order_by('-created_at')
    
    # Получаем элементы заказов с продуктами
    orders_with_items = []
    for order in user_orders:
        items = OrderItem.objects.filter(order=order).select_related('product')
        orders_with_items.append({
            'order': order,
            'items': items
        })
    
    context = {
        'user': request.user,
        'ratings': user_ratings,
        'orders_with_items': orders_with_items,  # Используем новую структуру
        'bookings': user_bookings
    }
    
    return render(request, 'profile.html', context)

def reviews(request):
    # Показываем все отзывы
    ratings = CafeRating.objects.all().order_by('-created_at')
    
    # Рассчитываем средние оценки
    if ratings:
        total_food = sum(r.food_quality for r in ratings)
        total_service = sum(r.service_quality for r in ratings)
        total_atmosphere = sum(r.atmosphere for r in ratings)
        total_cleanliness = sum(r.cleanliness for r in ratings)
        
        avg_ratings = {
            'food_quality': total_food / len(ratings),
            'service_quality': total_service / len(ratings),
            'atmosphere': total_atmosphere / len(ratings),
            'cleanliness': total_cleanliness / len(ratings),
            'overall': (total_food + total_service + total_atmosphere + total_cleanliness) / (len(ratings) * 4)
        }
    else:
        avg_ratings = None
    
    context = {
        'ratings': ratings,
        'avg_ratings': avg_ratings,
        'total_reviews': len(ratings)
    }
    
    return render(request, 'reviews.html', context)

def register_user(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Регистрация прошла успешно! Добро пожаловать, {user.email}!')
            return redirect('homepage:profile')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{error}')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'register.html', {'form': form})

def login_user(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')  # username здесь - это email
            password = form.cleaned_data.get('password')
            user = authenticate(request, email=email, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f'Добро пожаловать, {user.email}!')
                return redirect('homepage:profile')
        else:
            messages.error(request, 'Неверный email или пароль')
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'login.html', {'form': form})

def logout_user(request):
    logout(request)
    messages.success(request, 'Вы успешно вышли из системы')
    return redirect('homepage:home')

@login_required
def password_change(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            messages.success(request, 'Ваш пароль был успешно изменен!')
            return redirect('homepage:password_change_done')
    else:
        form = CustomPasswordChangeForm(request.user)
    
    return render(request, 'registration/password_change_form.html', {'form': form})

@login_required
def password_change_done(request):
    return render(request, 'registration/password_change_done.html')

def password_reset(request):
    if request.method == 'POST':
        form = CustomPasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            associated_users = User.objects.filter(email=email)
            
            if associated_users.exists():
                for user in associated_users:
                    # Генерируем токен и uid
                    token = default_token_generator.make_token(user)
                    uid = urlsafe_base64_encode(force_bytes(user.pk))
                    
                    # Получаем текущий сайт
                    current_site = get_current_site(request)
                    domain = current_site.domain
                    
                    # Создаем ссылку для сброса пароля
                    reset_url = f"http://{domain}/reset/{uid}/{token}/"
                    
                    # Создаем email сообщение
                    subject = 'Сброс пароля для Детского кафе "Радуга"'
                    
                    message = render_to_string('registration/password_reset_email.html', {
                        'user': user,
                        'reset_url': reset_url,
                        'domain': domain,
                        'protocol': 'http',
                    })
                    
                    # Отправляем email
                    send_mail(
                        subject,
                        message,
                        'noreply@cafe-rainbow.ru',
                        [email],
                        fail_silently=False,
                    )
            
            messages.success(request, 'Инструкции по сбросу пароля отправлены на ваш email.')
            return redirect('homepage:password_reset_done')
    else:
        form = CustomPasswordResetForm()
    
    return render(request, 'registration/password_reset_form.html', {'form': form})

def password_reset_done(request):
    return render(request, 'registration/password_reset_done.html')

def password_reset_confirm(request, uidb64=None, token=None):
    try:
        # Декодируем uid
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    # Проверяем токен
    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            form = CustomSetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Пароль успешно изменен. Теперь вы можете войти с новым паролем.')
                return redirect('homepage:password_reset_complete')  # Убедитесь, что это правильный URL
        else:
            form = CustomSetPasswordForm(user)
        
        return render(request, 'registration/password_reset_confirm.html', {
            'form': form,
            'validlink': True
        })
    else:
        return render(request, 'registration/password_reset_confirm.html', {
            'form': None,
            'validlink': False
        })

def password_reset_complete(request):
    return render(request, 'registration/password_reset_complete.html')

@login_required
def create_booking(request):
    """Создание бронирования через AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Валидация телефона
            phone = data.get('phone', '')
            phone_digits = ''.join(filter(str.isdigit, phone))
            
            if not phone or len(phone_digits) < 10:
                return JsonResponse({
                    'success': False,
                    'errors': {'phone': [{'message': 'Введите корректный номер телефона (минимум 10 цифр)'}]}
                })
            
            # Создаем объект Booking
            from datetime import datetime  # Импортируем здесь
            booking = Booking(
                user=request.user,
                event_date=datetime.strptime(data['eventDate'], '%Y-%m-%d').date(),
                event_time=datetime.strptime(data['eventTime'], '%H:%M').time(),
                event_duration=int(data.get('eventDuration', 2)),
                guests_count=int(data['guestsCount']),
                event_type=data['eventType'],
                phone=phone,
                comments=data.get('comments', ''),
                services=data.get('services', [])
            )
            
            # Проверяем доступность времени
            if not booking.is_time_slot_available():
                return JsonResponse({
                    'success': False,
                    'errors': {'eventTime': [{'message': 'Выбранное время уже занято. Пожалуйста, выберите другое время.'}]}
                })
            
            # Сохраняем бронирование
            booking.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Бронирование #{booking.id} успешно создано! Мы свяжемся с вами по телефону {phone} для подтверждения.',
                'booking_id': booking.id
            })
            
        except KeyError as e:
            return JsonResponse({
                'success': False,
                'errors': {str(e): [{'message': 'Обязательное поле'}]}
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Неверный метод запроса'})

def check_time_availability(request):
    """Проверка доступности времени через AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Проверяем обязательные поля
            if not data.get('eventDate') or not data.get('eventTime'):
                return JsonResponse({
                    'available': False,
                    'message': 'Укажите дату и время'
                })
            
            # Парсим дату и время
            from datetime import datetime, timedelta  # Импортируем здесь
            
            event_date = datetime.strptime(data['eventDate'], '%Y-%m-%d').date()
            event_time = datetime.strptime(data['eventTime'], '%H:%M').time()
            event_duration = int(data.get('eventDuration', 2))
            
            # Проверяем рабочее время (10:00 - 22:00)
            if event_time < datetime.strptime('10:00', '%H:%M').time():
                return JsonResponse({
                    'available': False,
                    'message': 'Кафе открывается в 10:00'
                })
            
            # Создаем временный объект для проверки
            booking = Booking(
                event_date=event_date,
                event_time=event_time,
                event_duration=event_duration
            )
            
            # Проверяем доступность
            if booking.is_time_slot_available():
                # Проверяем, не слишком ли поздно
                check_time = datetime.combine(event_date, event_time)
                end_time = check_time + timedelta(hours=event_duration)
                cafe_closes = datetime.combine(event_date, datetime.strptime('22:00', '%H:%M').time())
                
                if end_time > cafe_closes:
                    return JsonResponse({
                        'available': False,
                        'message': f'Кафе закрывается в 22:00. Мероприятие закончится в {end_time.time().strftime("%H:%M")}'
                    })
                
                return JsonResponse({
                    'available': True,
                    'message': f'Время доступно! Мероприятие продлится до {end_time.time().strftime("%H:%M")}'
                })
            else:
                return JsonResponse({
                    'available': False,
                    'message': 'Выбранное время занято. Попробуйте другое время'
                })
                
        except Exception as e:
            return JsonResponse({
                'available': False,
                'message': f'Ошибка проверки: {str(e)}'
            })
    
    return JsonResponse({'available': False, 'message': 'Неверный метод запроса'})

# Обновить функцию profile для отображения бронирований
@login_required
def profile(request):
    if request.method == 'POST':
        # Обновление профиля
        new_username = request.POST.get('username', '').strip()
        if new_username:
            request.user.username = new_username
            request.user.save()
            messages.success(request, 'Имя пользователя успешно обновлено!')
        return redirect('homepage:profile')
    
    # Получаем отзывы, заказы и бронирования
    user_ratings = CafeRating.objects.filter(user=request.user).order_by('-created_at')
    user_orders = Order.objects.filter(user=request.user).order_by('-created_at')
    user_bookings = Booking.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'user': request.user,
        'ratings': user_ratings,
        'orders': user_orders,
        'bookings': user_bookings
    }
    
    return render(request, 'profile.html', context)

@login_required
def cancel_booking(request, booking_id):
    """Отмена бронирования"""
    try:
        booking = Booking.objects.get(id=booking_id, user=request.user)
        
        if booking.status == 'pending':
            booking.status = 'cancelled'
            booking.save()
            
            # Отправляем email уведомление (если настроена отправка)
            try:
                send_mail(
                    subject=f'Отмена бронирования #{booking.id}',
                    message=f'''Бронирование #{booking.id} отменено.
                    
Детали бронирования:
Дата: {booking.event_date}
Время: {booking.event_time}
Тип мероприятия: {booking.get_event_type_display()}
Гостей: {booking.guests_count}
Стоимость: {booking.total_cost} руб.

Если у вас есть вопросы, свяжитесь с нами.''',
                    from_email='noreply@cafe-rainbow.ru',
                    recipient_list=[request.user.email],
                    fail_silently=True,
                )
            except:
                pass  # Игнорируем ошибки отправки email
            
            return JsonResponse({
                'success': True,
                'message': 'Бронирование успешно отменено! Средства будут возвращены в течение 3-5 рабочих дней.'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Нельзя отменить подтвержденное или уже отмененное бронирование'
            })
            
    except Booking.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Бронирование не найдено'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })