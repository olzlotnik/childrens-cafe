from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import ContactForm

def contact_info(request):
    if request.method == 'POST':
        # Передаем request в форму
        form = ContactForm(request.POST, request=request)
        
        if form.is_valid():
            # Сохраняем сообщение в базу
            contact_message = form.save()
            
            # Получаем данные из формы
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            message = form.cleaned_data['message']
            
            # Выводим данные в консоль
            print("=" * 50)
            print("НОВАЯ ФОРМА КОНТАКТОВ:")
            print(f"Имя: {name}")
            print(f"Email: {email}")
            print(f"Сообщение: {message}")
            
            print("=" * 50)
            print("СОХРАНЕНО В БАЗУ ДАННЫХ:")
            print(f"ID записи: {contact_message.id}")
            print(f"Имя: {contact_message.name}")
            print(f"Email: {contact_message.email}")
            print(f"Сообщение: {contact_message.message}")
            print(f"Дата создания: {contact_message.created_at}")
            print(f"IP адрес: {contact_message.ip_address}")
            print(f"Пользователь: {contact_message.user}")
            print("=" * 50)
            
            # Добавляем сообщение об успехе
            messages.success(
                request, 
                'Ваше сообщение успешно отправлено! Мы свяжемся с вами в ближайшее время.'
            )
            
            # Перенаправляем на страницу успеха
            return redirect('contacts:success')
        else:
            # Показываем ошибки формы
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = ContactForm(request=request)
    
    return render(request, 'contacts.html', {'form': form})

def contact_success(request):
    return render(request, 'contact_success.html')