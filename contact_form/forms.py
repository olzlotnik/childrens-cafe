from django import forms
from django.contrib.auth import get_user_model
from .models import ContactMessage

User = get_user_model()

class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите ваше имя'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите ваш email'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Введите ваше сообщение',
                'rows': 5
            }),
        }
        labels = {
            'name': 'Ваше имя',
            'email': 'Ваш email',
            'message': 'Сообщение',
        }
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        # Если пользователь авторизован, предзаполняем поля
        if self.request and self.request.user.is_authenticated:
            user = self.request.user
            if user.username:
                self.fields['name'].initial = user.username
            else:
                self.fields['name'].initial = user.email.split('@')[0]
            
            self.fields['email'].initial = user.email
            # Делаем поле email только для чтения
            self.fields['email'].widget.attrs['readonly'] = True
            self.fields['email'].widget.attrs['class'] = 'form-control readonly-field'
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        
        # Проверка, если пользователь авторизован
        if self.request and self.request.user.is_authenticated:
            if email != self.request.user.email:
                raise forms.ValidationError(
                    f'Вы должны использовать email, под которым вошли в систему. '
                    f'Текущий email: {self.request.user.email}'
                )
        
        return email
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Если пользователь авторизован, связываем сообщение с ним
        if self.request and self.request.user.is_authenticated:
            instance.user = self.request.user
        
        # Сохраняем IP адрес
        if self.request:
            x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = self.request.META.get('REMOTE_ADDR')
            instance.ip_address = ip
        
        if commit:
            instance.save()
        
        return instance