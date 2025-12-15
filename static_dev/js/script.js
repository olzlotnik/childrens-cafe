// Основные функции для сайта

// Функция для кнопки "Наверх"
window.onscroll = function() {
    const backToTopButton = document.querySelector('.back-to-top');
    if (document.body.scrollTop > 300 || document.documentElement.scrollTop > 300) {
        backToTopButton.classList.add('show');
    } else {
        backToTopButton.classList.remove('show');
    }
};

function scrollToTop() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

// Функции для корзины
function updateCartCount(count) {
    const cartCountElements = document.querySelectorAll('#cart-count, .cart-count');
    cartCountElements.forEach(element => {
        element.textContent = count;
    });
    
    // Также обновляем текст в навигации
    const navLinks = document.querySelectorAll('nav a');
    navLinks.forEach(link => {
        if (link.textContent.includes('Корзина')) {
            link.textContent = `Корзина (${count})`;
        }
    });
}

function getCSRFToken() {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
    if (csrfToken) {
        return csrfToken.value;
    }
    return '';
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    // Инициализация минимальной даты для формы бронирования
    const today = new Date().toISOString().split('T')[0];
    const dateInput = document.getElementById('eventDate');
    if (dateInput) {
        dateInput.min = today;
    }
    
    // Обработчики для формы бронирования
    const guestsCountInput = document.getElementById('guestsCount');
    const serviceCheckboxes = document.querySelectorAll('input[name="services"]');
    const bookingForm = document.getElementById('bookingForm');
    const phoneInput = document.getElementById('phone');
    
    if (guestsCountInput) {
        guestsCountInput.addEventListener('input', calculateBudget);
    }
    
    if (serviceCheckboxes.length > 0) {
        serviceCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', calculateBudget);
        });
    }
    
    if (phoneInput) {
        phoneInput.addEventListener('input', function(e) {
            let input = e.target.value.replace(/\D/g, '');
            
            if (input.length > 11) {
                input = input.substring(0, 11);
            }
            
            if (input.length > 0) {
                let formatted = '';
                
                if (input.length <= 1) {
                    formatted = '+7 ' + input;
                } else if (input.length <= 4) {
                    formatted = '+7 (' + input.substring(1, 4);
                } else if (input.length <= 7) {
                    formatted = '+7 (' + input.substring(1, 4) + ') ' + input.substring(4, 7);
                } else if (input.length <= 9) {
                    formatted = '+7 (' + input.substring(1, 4) + ') ' + input.substring(4, 7) + '-' + input.substring(7, 9);
                } else {
                    formatted = '+7 (' + input.substring(1, 4) + ') ' + input.substring(4, 7) + '-' + input.substring(7, 9) + '-' + input.substring(9, 11);
                }
                
                e.target.value = formatted;
            }
            
            const errorElement = document.getElementById('phoneError');
            if (errorElement) {
                errorElement.style.display = 'none';
                e.target.style.borderColor = '#ffd166';
            }
        });
    }
    
    if (bookingForm) {
        bookingForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            clearErrors();
            
            let hasErrors = false;
            
            const phone = document.getElementById('phone').value;
            if (!validatePhone(phone)) {
                showError('phone', 'Пожалуйста, введите корректный номер телефона (минимум 10 цифр)');
                hasErrors = true;
            }
            
            const eventDate = document.getElementById('eventDate').value;
            if (eventDate) {
                const selectedDate = new Date(eventDate);
                const today = new Date();
                today.setHours(0, 0, 0, 0);
                
                if (selectedDate < today) {
                    showError('eventDate', 'Нельзя выбрать прошедшую дату');
                    hasErrors = true;
                }
            }
            
            if (hasErrors) {
                return;
            }
            
            showSuccessMessage();
            closeBookingForm();
            this.reset();
            calculateBudget();
        });
    }
    
    // Закрытие формы при клике вне ее
    window.onclick = function(event) {
        const modal = document.getElementById('bookingModal');
        if (event.target == modal) {
            closeBookingForm();
        }
    }
    
    // Инициализация звезд рейтинга
    initializeStarRating();
});

function initializeStarRating() {
    const starsContainers = document.querySelectorAll('.stars');
    
    starsContainers.forEach(container => {
        const stars = container.querySelectorAll('input[type="radio"]');
        const labels = container.querySelectorAll('label');
        
        labels.forEach((label, index) => {
            label.addEventListener('mouseenter', () => {
                // Подсвечиваем звезды при наведении
                for (let i = labels.length - 1; i >= index; i--) {
                    labels[i].style.color = '#ffd166';
                }
            });
            
            label.addEventListener('mouseleave', () => {
                // Сбрасываем цвет при уходе мыши
                resetStarsColor(container);
            });
        });
        
        stars.forEach(star => {
            star.addEventListener('change', () => {
                resetStarsColor(container);
                const value = parseInt(star.value);
                // Подсвечиваем выбранные звезды
                for (let i = 0; i < value; i++) {
                    labels[labels.length - 1 - i].style.color = '#ffd166';
                }
            });
        });
    });
}

function resetStarsColor(container) {
    const labels = container.querySelectorAll('label');
    const checkedStar = container.querySelector('input[type="radio"]:checked');
    
    labels.forEach(label => {
        label.style.color = '#ddd';
    });
    
    if (checkedStar) {
        const value = parseInt(checkedStar.value);
        for (let i = 0; i < value; i++) {
            labels[labels.length - 1 - i].style.color = '#ffd166';
        }
    }
}

// Константы для бронирования
const BOOKING_PRICES = {
    base_per_guest_hour: 500,
    services: {
        animator: 1000,
        cake: 1500,
        decorations: 2000,
        photographer: 2500
    }
};

// Функция для проверки доступности времени
// Заменить функцию checkAvailability на эту:

function checkAvailability() {
    const date = document.getElementById('check_date').value;
    const startTime = document.getElementById('check_start_time').value;
    const duration = document.getElementById('check_duration').value || 2;
    
    if (!date || !startTime) {
        alert('Пожалуйста, выберите дату и время');
        return;
    }
    
    const resultDiv = document.getElementById('availabilityResult');
    const slotsDiv = document.getElementById('bookedSlots');
    
    // Показываем индикатор загрузки
    resultDiv.innerHTML = '<div style="color: #ffd166; padding: 10px;">⌛ Проверяем доступность...</div>';
    resultDiv.style.display = 'block';
    resultDiv.style.backgroundColor = '#fff3cd';
    resultDiv.style.border = '1px solid #ffeaa7';
    resultDiv.style.borderRadius = '5px';
    resultDiv.style.marginTop = '10px';
    
    slotsDiv.style.display = 'none';
    
    // Отправляем запрос на сервер
    fetch(`/bookings/check/?date=${date}&start_time=${startTime}&duration=${duration}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Ошибка сети');
            }
            return response.json();
        })
        .then(data => {
            console.log('Ответ сервера:', data); // Для отладки
            
            if (data.success) {
                if (data.is_available) {
                    resultDiv.innerHTML = `<div style="color: #4ecdc4; font-weight: bold; padding: 10px;">✓ ${data.message || 'Время доступно!'}</div>`;
                    resultDiv.style.backgroundColor = '#d4edda';
                    resultDiv.style.border = '1px solid #c3e6cb';
                    
                    // Автоматически заполняем основную форму
                    document.getElementById('eventDate').value = date;
                    document.getElementById('startTime').value = startTime;
                    document.getElementById('durationHours').value = duration;
                } else {
                    resultDiv.innerHTML = `<div style="color: #ff6b6b; font-weight: bold; padding: 10px;">✗ ${data.message || 'Время занято!'}</div>`;
                    resultDiv.style.backgroundColor = '#f8d7da';
                    resultDiv.style.border = '1px solid #f5c6cb';
                    
                    // Показываем занятые слоты
                    if (data.booked_slots && data.booked_slots.length > 0) {
                        slotsDiv.innerHTML = '<strong>Занятые слоты на этот день:</strong><br>';
                        data.booked_slots.forEach(slot => {
                            slotsDiv.innerHTML += `• ${slot.start} - ${slot.end}<br>`;
                        });
                        slotsDiv.style.display = 'block';
                        slotsDiv.style.backgroundColor = '#fff3cd';
                        slotsDiv.style.border = '1px solid #ffeaa7';
                        slotsDiv.style.padding = '10px';
                        slotsDiv.style.borderRadius = '5px';
                        slotsDiv.style.marginTop = '10px';
                    }
                }
            } else {
                resultDiv.innerHTML = `<div style="color: #ff6b6b; padding: 10px;">Ошибка: ${data.message || 'Неизвестная ошибка'}</div>`;
                resultDiv.style.backgroundColor = '#f8d7da';
                resultDiv.style.border = '1px solid #f5c6cb';
            }
        })
        .catch(error => {
            console.error('Ошибка при проверке доступности:', error);
            resultDiv.innerHTML = `<div style="color: #ff6b6b; padding: 10px;">Ошибка сети. Попробуйте позже.</div>`;
            resultDiv.style.backgroundColor = '#f8d7da';
            resultDiv.style.border = '1px solid #f5c6cb';
        });
}

// Функция для расчета стоимости бронирования
function calculateBookingPrice() {
    const guests = parseInt(document.getElementById('guestsCount').value) || 0;
    const duration = parseInt(document.getElementById('durationHours').value) || 2;
    const services = document.querySelectorAll('input[name="services"]:checked');
    
    const baseCost = guests * BOOKING_PRICES.base_per_guest_hour * duration;
    let servicesCost = 0;
    
    services.forEach(checkbox => {
        servicesCost += BOOKING_PRICES.services[checkbox.value] || 0;
    });
    
    const totalCost = baseCost + servicesCost;
    
    document.getElementById('baseCost').textContent = baseCost;
    document.getElementById('servicesCost').textContent = servicesCost;
    document.getElementById('totalCost').textContent = totalCost;
}

// Обновляем расчет стоимости при изменениях
document.addEventListener('DOMContentLoaded', function() {
    // Инициализируем даты
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('eventDate').min = today;
    document.getElementById('check_date').min = today;
    
    // Устанавливаем разумные значения по умолчанию
    const now = new Date();
    const defaultTime = '14:00';
    document.getElementById('startTime').value = defaultTime;
    document.getElementById('check_start_time').value = defaultTime;
    
    // Добавляем обработчики для расчета стоимости
    document.getElementById('guestsCount').addEventListener('input', calculateBookingPrice);
    document.getElementById('durationHours').addEventListener('input', calculateBookingPrice);
    document.querySelectorAll('input[name="services"]').forEach(checkbox => {
        checkbox.addEventListener('change', calculateBookingPrice);
    });
    
    // Инициализируем расчет
    calculateBookingPrice();
    
    // Обновляем обработчик отправки формы
    const bookingForm = document.getElementById('bookingForm');
    if (bookingForm) {
        bookingForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Проверяем авторизацию
            if (!isUserAuthenticated()) {
                alert('Для бронирования необходимо войти в систему');
                window.location.href = '/login/';
                return;
            }
            
            // Собираем данные формы
            const formData = new FormData(this);
            
            // Отправляем запрос на сервер
            fetch('/bookings/create/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCSRFToken()
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showBookingSuccess(data.message, data.booking_id);
                    closeBookingForm();
                    this.reset();
                    calculateBookingPrice();
                } else {
                    if (data.errors) {
                        // Показываем ошибки валидации
                        let errorMessages = '';
                        for (const field in data.errors) {
                            errorMessages += `${data.errors[field]}\n`;
                        }
                        alert(`Ошибки:\n${errorMessages}`);
                    } else {
                        alert(data.message);
                    }
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Произошла ошибка при отправке формы');
            });
        });
    }
});

// Функция проверки авторизации
function isUserAuthenticated() {
    // Проверяем наличие элементов, которые показывают авторизацию
    const profileLink = document.querySelector('a[href*="profile"]');
    const logoutLink = document.querySelector('a[href*="logout"]');
    return profileLink && logoutLink;
}

// Функция для показа успешного бронирования
function showBookingSuccess(message, bookingId) {
    const successModal = document.createElement('div');
    successModal.className = 'success-modal';
    successModal.innerHTML = `
        <div class="success-content">
            <div class="success-icon">🎉</div>
            <h3>Бронирование создано!</h3>
            <p>${message}</p>
            <div class="success-buttons">
                <button class="success-button" onclick="window.location.href='/bookings/'">Мои бронирования</button>
                <button class="success-button" onclick="closeSuccessMessage()">ОК</button>
            </div>
        </div>
    `;
    document.body.appendChild(successModal);
}

// Обновляем функцию openBookingForm для проверки авторизации
function openBookingForm() {
    if (!isUserAuthenticated()) {
        alert('Для бронирования мероприятия необходимо войти в систему');
        window.location.href = '/login/';
        return;
    }
    document.getElementById('bookingModal').style.display = 'block';
    calculateBookingPrice();
}