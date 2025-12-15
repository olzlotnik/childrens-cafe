from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta, date
from .models import Booking

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        label='Email адрес',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите ваш email'
        })
    )
    username = forms.CharField(
        required=False,
        label='Имя пользователя (необязательно)',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите ваше имя'
        })
    )
    password1 = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )
    password2 = forms.CharField(
        label='Подтверждение пароля',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Повторите пароль'
        })
    )
    
    class Meta:
        model = User
        fields = ('email', 'username', 'password1', 'password2')
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Пользователь с таким email уже существует')
        return email
    
    def save(self, commit=True):
        user = super().save(commit=False)
        # Если username не указан, используем часть email до @
        if not user.username:
            user.username = user.email.split('@')[0]
        if commit:
            user.save()
        return user

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label='Email адрес',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите ваш email'
        })
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )

class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Убираем ошибки по умолчанию при создании формы
        for field in self.fields.values():
            field.error_messages = {'required': 'Это поле обязательно'}

    old_password = forms.CharField(
        label="Текущий пароль",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите текущий пароль'
        }),
        error_messages={
            'required': 'Пожалуйста, введите текущий пароль'
        }
    )
    
    new_password1 = forms.CharField(
        label="Новый пароль",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите новый пароль'
        }),
        error_messages={
            'required': 'Пожалуйста, введите новый пароль'
        }
    )
    
    new_password2 = forms.CharField(
        label="Подтверждение пароля",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Повторите новый пароль'
        }),
        error_messages={
            'required': 'Пожалуйста, подтвердите новый пароль'
        }
    )

class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        label="Email",
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите ваш email',
            'autocomplete': 'email'
        }),
        error_messages={
            'required': 'Пожалуйста, введите email адрес',
            'invalid': 'Введите корректный email адрес'
        }
    )

class CustomSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label="Новый пароль",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите новый пароль',
            'autocomplete': 'new-password'
        }),
        help_text="Пароль должен содержать не менее 8 символов."
    )
    
    new_password2 = forms.CharField(
        label="Подтверждение пароля",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Повторите новый пароль',
            'autocomplete': 'new-password'
        })
    )

class BookingForm(forms.ModelForm):
    SERVICES_CHOICES = [
        ('animator', 'Аниматор (+1000 руб)'),
        ('cake', 'Торт (+1500 руб)'),
        ('decorations', 'Украшение зала (+2000 руб)'),
        ('photographer', 'Фотограф (+2500 руб)'),
    ]
    
    # Поля для динамической валидации
    event_duration = forms.IntegerField(
        min_value=1,
        max_value=8,
        initial=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1',
            'max': '8',
            'id': 'eventDuration'
        })
    )
    
    # Чекбоксы для услуг
    services = forms.MultipleChoiceField(
        choices=SERVICES_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'checkbox-group'
        })
    )
    
    class Meta:
        model = Booking
        fields = [
            'event_date', 'event_time', 'event_duration',
            'guests_count', 'event_type', 'phone', 'comments'
        ]
        widgets = {
            'event_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'id': 'eventDate',
                'min': datetime.now().strftime('%Y-%m-%d')
            }),
            'event_time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-control',
                'id': 'eventTime'
            }),
            'guests_count': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '50',
                'id': 'guestsCount'
            }),
            'event_type': forms.Select(attrs={
                'class': 'form-control',
                'id': 'eventType'
            }),
            'phone': forms.TextInput(attrs={
                'type': 'tel',
                'class': 'form-control',
                'id': 'phone',
                'placeholder': '+7 (XXX) XXX-XX-XX'
            }),
            'comments': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '4',
                'id': 'comments'
            }),
        }
    
    def clean_event_date(self):
        event_date = self.cleaned_data.get('event_date')
        
        # Проверяем, что дата не в прошлом
        if event_date < date.today():
            raise ValidationError('Нельзя выбрать прошедшую дату')
        
        # Проверяем, что не слишком далеко в будущем (максимум 3 месяца)
        max_date = date.today() + timedelta(days=90)
        if event_date > max_date:
            raise ValidationError('Бронирование доступно максимум на 3 месяца вперед')
        
        return event_date
    
    def clean_event_time(self):
        event_time = self.cleaned_data.get('event_time')
        event_date = self.cleaned_data.get('event_date')
        
        # Проверяем рабочее время кафе (10:00 - 22:00)
        if event_time < datetime.strptime('10:00', '%H:%M').time():
            raise ValidationError('Кафе открывается в 10:00')
        
        if event_time > datetime.strptime('20:00', '%H:%M').time():
            raise ValidationError('Последнее бронирование принимается на 20:00')
        
        return event_time
    
    def clean(self):
        cleaned_data = super().clean()
        event_date = cleaned_data.get('event_date')
        event_time = cleaned_data.get('event_time')
        event_duration = cleaned_data.get('event_duration')
        
        if event_date and event_time and event_duration:
            # Создаем временный объект для проверки
            booking = Booking(
                event_date=event_date,
                event_time=event_time,
                event_duration=event_duration
            )
            
            # Проверяем доступность времени
            if not booking.is_time_slot_available():
                raise ValidationError('Выбранное время уже занято. Пожалуйста, выберите другое время.')
        
        return cleaned_data