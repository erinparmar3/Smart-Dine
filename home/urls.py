from django.contrib import admin
from django.urls import path, include
from home import views

urlpatterns = [
    # Auth routes
    path('register/', views.register_user, name='register'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),

    # Customer routes
    path('', views.index, name='home'),
    path('dashboard/', views.customer_dashboard, name='dashboard'),
    path('dashboard/cancel-order/<int:order_id>/', views.cancel_order_customer, name='cancel_order_customer'),
    path('dashboard/cancel-reservation/<int:reservation_id>/', views.cancel_reservation_customer, name='cancel_reservation_customer'),
    path('menu/', views.menu, name='menu'),
    path('add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('clear-cart/', views.clear_cart, name='clear_cart'),
    path('update-cart-quantity/', views.update_cart_quantity, name='update_cart_quantity'),
    path('remove-from-cart/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('place-order/', views.place_order, name='place_order'),
    path('order-confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    
    # API endpoints
    path('api/update-cart-quantity/', views.update_cart_quantity, name='update_cart_quantity'),
    path('api/remove-from-cart/', views.remove_from_cart, name='remove_from_cart'),
    path('api/menu/availability/', views.menu_availability_api, name='menu_availability_api'),
    
    # Reservations
    path('reservations/', views.reservations, name='reservations'),
    path('make-reservation/', views.make_reservation, name='make_reservation'),
    
]
