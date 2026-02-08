from django.contrib import admin
from django.urls import path, include
from home import views

urlpatterns = [
    # Customer routes
    path('', views.index, name='home'),
    path('menu/', views.menu, name='menu'),
    path('add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('clear-cart/', views.clear_cart, name='clear_cart'),
    path('place-order/', views.place_order, name='place_order'),
    path('order-confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    
    # API endpoints
    path('api/update-cart-quantity/', views.update_cart_quantity, name='update_cart_quantity'),
    path('api/remove-from-cart/', views.remove_from_cart, name='remove_from_cart'),
    
    # Reservations
    path('reservations/', views.reservations, name='reservations'),
    path('make-reservation/', views.make_reservation, name='make_reservation'),
    
    # Admin routes
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/orders/', views.admin_orders, name='admin_orders'),
    path('admin/update-order-status/<int:order_id>/', views.update_order_status, name='update_order_status'),
    path('admin/inventory/', views.admin_inventory, name='admin_inventory'),
    path('admin/tables/', views.admin_tables, name='admin_tables'),
    path('admin/update-table-status/<int:table_id>/', views.update_table_status, name='update_table_status'),
    path('admin/reservations/', views.admin_reservations, name='admin_reservations'),
    path('admin/confirm-reservation/<int:reservation_id>/', views.confirm_reservation, name='confirm_reservation'),
]
