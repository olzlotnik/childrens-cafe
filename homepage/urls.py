from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'homepage'

urlpatterns = [
    path('', views.index, name='home'),
    path('rate/', views.rate_cafe, name='rate_cafe'),
    path('profile/', views.profile, name='profile'),
    path('reviews/', views.reviews, name='reviews'),
    path('register/', views.register_user, name='register'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),

    # Бронирование мероприятий
    path('booking/create/', views.create_booking, name='create_booking'),
    path('booking/check_availability/', views.check_time_availability, name='check_availability'),
    path('booking/<int:booking_id>/cancel/', views.cancel_booking, name='cancel_booking'),
    
    # Восстановление пароля (используем свои вьюшки)
    path('password_reset/', views.password_reset, name='password_reset'),
    path('password_reset/done/', views.password_reset_done, name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('reset/done/', views.password_reset_complete, name='password_reset_complete'),
    
    # Смена пароля из личного кабинета
    path('password_change/', views.password_change, name='password_change'),
    path('password_change/done/', views.password_change_done, name='password_change_done'),
]