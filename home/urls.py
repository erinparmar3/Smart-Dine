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
    
    # Admin routes
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/orders/', views.admin_orders, name='admin_orders'),
    path('admin/update-order-status/<int:order_id>/', views.update_order_status, name='update_order_status'),
    path('admin/inventory/', views.admin_inventory, name='admin_inventory'),
    path('admin/tables/', views.admin_tables, name='admin_tables'),
    path('admin/tables/<int:table_id>/status/', views.update_table_status, name='update_table_status'),
    path('admin/reservations/', views.admin_reservations, name='admin_reservations'),
    path('admin/reservations/<int:reservation_id>/confirm/', views.confirm_reservation, name='confirm_reservation'),
    path('admin/reservations/<int:reservation_id>/cancel/', views.cancel_reservation_admin, name='cancel_reservation_admin'),
    path('admin/reports/', views.admin_reports, name='admin_reports'),
    path('admin/menu/', views.admin_menu, name='admin_menu'),
    path('admin/menu/add/', views.admin_menu_add, name='admin_menu_add'),
    path('admin/menu/<int:item_id>/edit/', views.admin_menu_edit, name='admin_menu_edit'),
    path('admin/menu/<int:item_id>/delete/', views.admin_menu_delete, name='admin_menu_delete'),
]
