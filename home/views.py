from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Sum, F, Q
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import json

from .models import (
    MenuItem, Order, OrderItem, Reservation, Table, 
    InventoryItem, Recipe, RecipeIngredient
)
from .forms import (
    PlaceOrderForm, ReservationForm, InventoryUpdateForm, 
    OrderFilterForm, AddToCartForm
)


# ==================== CUSTOMER VIEWS ====================

def index(request):
    """Home page"""
    total_orders = Order.objects.count()
    total_reservations = Reservation.objects.count()
    available_tables = Table.objects.filter(status='Available').count()
    
    context = {
        'total_orders': total_orders,
        'total_reservations': total_reservations,
        'available_tables': available_tables,
    }
    return render(request, 'index.html', context)


def menu(request):
    """Menu and ordering page - with category filtering"""
    # Get selected category from query params
    selected_category = request.GET.get('category', None)
    
    # Get all available categories
    categories = MenuItem.CATEGORY_CHOICES
    
    # Get menu items, optionally filtered by category
    if selected_category:
        menu_items = MenuItem.objects.filter(category=selected_category)
    else:
        menu_items = MenuItem.objects.all()
    
    tables = Table.objects.filter(status='Available')
    
    # Get cart from session
    cart = request.session.get('cart', [])
    
    # Calculate subtotal for each cart item
    for item in cart:
        item['subtotal'] = item['price'] * item['qty']
    
    total = Decimal(str(sum(item['price'] * item['qty'] for item in cart)))
    tax = total * Decimal('0.18')  # 18% GST
    total_with_tax = total + tax
    cart_count = len(cart)
    
    context = {
        'menu_items': menu_items,
        'categories': categories,
        'selected_category': selected_category,
        'tables': tables,
        'cart': cart,
        'total': float(round(total, 2)),
        'tax': float(round(tax, 2)),
        'total_with_tax': float(round(total_with_tax, 2)),
        'cart_count': cart_count,
    }
    return render(request, 'menu.html', context)


@require_http_methods(["POST"])
def add_to_cart(request):
    """Add item to cart (session-based)"""
    try:
        item_id = int(request.POST.get('item_id'))
        qty = int(request.POST.get('quantity', 1))
        
        menu_item = get_object_or_404(MenuItem, id=item_id)
        
        cart = request.session.get('cart', [])
        
        # Check if item already in cart
        item_in_cart = next((i for i in cart if i['id'] == item_id), None)
        
        if item_in_cart:
            item_in_cart['qty'] += qty
        else:
            cart.append({
                'id': menu_item.id,
                'name': menu_item.name,
                'price': float(menu_item.price),
                'qty': qty,
                'image': menu_item.image,
            })
        
        request.session['cart'] = cart
        messages.success(request, f'Added {qty}x {menu_item.name} to cart')
        
    except Exception as e:
        messages.error(request, f'Error adding to cart: {str(e)}')
    
    return redirect('menu')


def clear_cart(request):
    """Clear shopping cart"""
    request.session.pop('cart', None)
    messages.info(request, 'Cart cleared')
    return redirect('menu')


@require_http_methods(["POST"])
def update_cart_quantity(request):
    """API endpoint to update item quantity in cart"""
    try:
        data = json.loads(request.body)
        item_id = int(data.get('item_id'))
        change = int(data.get('change', 1))  # +1 or -1
        
        cart = request.session.get('cart', [])
        
        # Find item in cart
        item_in_cart = next((i for i in cart if i['id'] == item_id), None)
        
        if item_in_cart:
            item_in_cart['qty'] += change
            
            # Remove if quantity becomes 0
            if item_in_cart['qty'] <= 0:
                cart.remove(item_in_cart)
            
            request.session['cart'] = cart
            request.session.modified = True
            
            return JsonResponse({'status': 'success', 'cart': cart})
        else:
            return JsonResponse({'status': 'error', 'message': 'Item not in cart'}, status=404)
    
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@require_http_methods(["POST"])
def remove_from_cart(request):
    """API endpoint to remove item from cart"""
    try:
        data = json.loads(request.body)
        item_id = int(data.get('item_id'))
        
        cart = request.session.get('cart', [])
        
        # Remove item from cart
        cart = [item for item in cart if item['id'] != item_id]
        
        request.session['cart'] = cart
        request.session.modified = True
        
        return JsonResponse({'status': 'success', 'cart': cart})
    
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@require_http_methods(["POST"])
def place_order(request):
    """Place an order"""
    cart = request.session.get('cart', [])
    
    if not cart:
        messages.error(request, 'Your cart is empty!')
        return redirect('menu')
    
    try:
        # Get form data
        order_type = request.POST.get('order_type', 'Dine-in')
        table_id = request.POST.get('table')
        payment_method = request.POST.get('payment_method', 'Card')
        
        # Validate cart items exist in DB
        menu_items_dict = {}
        for cart_item in cart:
            item = MenuItem.objects.get(id=cart_item['id'])
            menu_items_dict[item.id] = item
        
        # Check inventory
        for cart_item in cart:
            menu_item = menu_items_dict[cart_item['id']]
            qty = cart_item['qty']
            
            # Check if recipe exists and ingredients are available
            if hasattr(menu_item, 'recipe'):
                for ingredient in menu_item.recipe.ingredients.all():
                    needed = ingredient.quantity * qty
                    inv_item = InventoryItem.objects.filter(
                        name__iexact=ingredient.ingredient
                    ).first()
                    
                    if not inv_item or inv_item.quantity < needed:
                        messages.error(
                            request,
                            f'Low stock: Not enough {ingredient.ingredient} for {menu_item.name}'
                        )
                        return redirect('menu')
        
        # Calculate total
        total = sum(Decimal(str(item['price'])) * item['qty'] for item in cart)
        
        # Get table if dine-in
        table = None
        if order_type == 'Dine-in' and table_id:
            table = get_object_or_404(Table, id=table_id)
            table.status = 'Occupied'
            table.save()
        
        # Create order
        order = Order.objects.create(
            order_type=order_type,
            table=table,
            payment_method=payment_method,
            total=total,
            status='Pending'
        )
        
        # Create order items and deduct inventory
        for cart_item in cart:
            menu_item = menu_items_dict[cart_item['id']]
            qty = cart_item['qty']
            
            OrderItem.objects.create(
                order=order,
                menu_item=menu_item,
                quantity=qty,
                price=menu_item.price
            )
            
            # Deduct from inventory
            if hasattr(menu_item, 'recipe'):
                for ingredient in menu_item.recipe.ingredients.all():
                    needed = ingredient.quantity * qty
                    inv_item = InventoryItem.objects.filter(
                        name__iexact=ingredient.ingredient
                    ).first()
                    if inv_item:
                        inv_item.quantity -= needed
                        inv_item.save()
        
        # Clear cart
        request.session.pop('cart', None)
        
        messages.success(
            request,
            f'Order #{order.order_id} placed successfully! Kitchen has been notified.'
        )
        return redirect('order_confirmation', order_id=order.order_id)
        
    except MenuItem.DoesNotExist:
        messages.error(request, 'One or more items in your cart are no longer available')
        return redirect('menu')
    except Exception as e:
        messages.error(request, f'Error placing order: {str(e)}')
        return redirect('menu')


def order_confirmation(request, order_id):
    """Order confirmation page"""
    order = get_object_or_404(Order, order_id=order_id)
    context = {'order': order}
    return render(request, 'order_confirmation.html', context)


def reservations(request):
    """Reservations page"""
    form = ReservationForm()
    upcoming_reservations = Reservation.objects.filter(
        date__gte=timezone.now().date(),
        confirmed=True
    ).order_by('date', 'time')[:10]
    
    context = {
        'form': form,
        'upcoming_reservations': upcoming_reservations,
    }
    return render(request, 'reservations.html', context)


@require_http_methods(["POST"])
def make_reservation(request):
    """Process reservation"""
    form = ReservationForm(request.POST)
    
    if form.is_valid():
        # Find available table
        table = Table.objects.filter(
            capacity__gte=form.cleaned_data['guests'],
            status='Available'
        ).first()
        
        reservation = form.save(commit=False)
        reservation.table = table
        reservation.confirmed = True if table else False
        reservation.save()
        
        if table:
            messages.success(request, 'Reservation confirmed! Table reserved.')
        else:
            messages.warning(request, 'Reservation pending. No tables available. Staff will contact you.')
        
        return redirect('reservations')
    
    context = {'form': form}
    return render(request, 'reservations.html', context)


# ==================== ADMIN VIEWS ====================

def admin_dashboard(request):
    """Admin dashboard"""
    # Get recent orders
    recent_orders = Order.objects.all().order_by('-created_at')[:10]
    pending_orders = Order.objects.filter(status='Pending').count()
    
    # Get inventory
    low_stock_items = InventoryItem.objects.filter(
        quantity__lt=F('reorder_level')
    )
    
    # Get tables
    tables = Table.objects.all()
    occupied_tables = tables.filter(status='Occupied').count()
    
    # Get reservations
    upcoming_reservations = Reservation.objects.filter(
        date__gte=timezone.now().date()
    ).order_by('date', 'time')[:5]
    
    # Calculate stats
    today_orders = Order.objects.filter(
        created_at__date=timezone.now().date()
    ).count()
    
    today_revenue = Order.objects.filter(
        created_at__date=timezone.now().date(),
        status__in=['Completed', 'Ready']
    ).aggregate(total=Sum('total'))['total'] or 0
    
    context = {
        'recent_orders': recent_orders,
        'pending_orders': pending_orders,
        'low_stock_items': low_stock_items,
        'tables': tables,
        'occupied_tables': occupied_tables,
        'upcoming_reservations': upcoming_reservations,
        'today_orders': today_orders,
        'today_revenue': today_revenue,
    }
    return render(request, 'admin/dashboard.html', context)


def admin_orders(request):
    """Admin orders management"""
    orders = Order.objects.all().order_by('-created_at')
    filter_form = OrderFilterForm(request.GET)
    
    if filter_form.is_valid():
        status = filter_form.cleaned_data.get('status')
        order_type = filter_form.cleaned_data.get('order_type')
        
        if status:
            orders = orders.filter(status=status)
        if order_type:
            orders = orders.filter(order_type=order_type)
    
    context = {
        'orders': orders,
        'filter_form': filter_form,
    }
    return render(request, 'admin/orders.html', context)


@require_http_methods(["POST"])
def update_order_status(request, order_id):
    """Update order status"""
    order = get_object_or_404(Order, order_id=order_id)
    status = request.POST.get('status', 'Pending')
    
    if status in dict(Order.STATUS_CHOICES):
        order.status = status
        if status == 'Completed':
            order.completed_at = timezone.now()
        order.save()
        messages.success(request, f'Order #{order_id} status updated to {status}')
    
    return redirect('admin_orders')


def admin_inventory(request):
    """Admin inventory management"""
    inventory_items = InventoryItem.objects.all().order_by('name')
    low_stock = inventory_items.filter(quantity__lt=F('reorder_level'))
    
    if request.method == 'POST':
        form = InventoryUpdateForm(request.POST)
        if form.is_valid():
            ingredient = form.cleaned_data['ingredient']
            quantity = form.cleaned_data['quantity']
            action = form.cleaned_data['action']
            
            inv_item, created = InventoryItem.objects.get_or_create(
                name__iexact=ingredient,
                defaults={'name': ingredient}
            )
            
            if action == 'add':
                inv_item.quantity += quantity
            else:  # action == 'set'
                inv_item.quantity = quantity
            
            inv_item.save()
            messages.success(request, f'Inventory updated: {ingredient}')
            return redirect('admin_inventory')
    else:
        form = InventoryUpdateForm()
    
    context = {
        'inventory_items': inventory_items,
        'low_stock': low_stock,
        'form': form,
    }
    return render(request, 'admin/inventory.html', context)


def admin_tables(request):
    """Admin table management"""
    tables = Table.objects.all().order_by('table_number')
    reservations = Reservation.objects.filter(
        confirmed=True,
        date__gte=timezone.now().date()
    ).order_by('date', 'time')
    
    context = {
        'tables': tables,
        'reservations': reservations,
    }
    return render(request, 'admin/tables.html', context)


@require_http_methods(["POST"])
def update_table_status(request, table_id):
    """Update table status"""
    table = get_object_or_404(Table, id=table_id)
    status = request.POST.get('status', 'Available')
    
    if status in dict(Table._meta.get_field('status').choices):
        table.status = status
        table.save()
        messages.success(request, f'Table {table.table_number} status updated')
    
    return redirect('admin_tables')


def admin_reservations(request):
    """Admin reservations management"""
    reservations = Reservation.objects.all().order_by('-created_at')
    
    context = {
        'reservations': reservations,
    }
    return render(request, 'admin/reservations.html', context)


@require_http_methods(["POST"])
def confirm_reservation(request, reservation_id):
    """Confirm reservation"""
    reservation = get_object_or_404(Reservation, id=reservation_id)
    
    # Find available table
    table = Table.objects.filter(
        capacity__gte=reservation.guests,
        status='Available'
    ).first()
    
    if table:
        reservation.table = table
        reservation.confirmed = True
        reservation.save()
        messages.success(request, f'Reservation confirmed for {reservation.name}')
    else:
        messages.error(request, 'No available tables for this reservation')
    
    return redirect('admin_reservations')


