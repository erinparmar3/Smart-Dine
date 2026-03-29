from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Sum, F, Q
from django.db import transaction
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import json

from .models import (
    MenuItem, Order, OrderItem, Reservation, Table,
    InventoryItem,
)
from .forms import (
    PlaceOrderForm, ReservationForm, InventoryUpdateForm, 
    OrderFilterForm, AddToCartForm, MenuItemForm, MenuItemIngredientFormSet
)


# ==================== AUTHENTICATION VIEWS ===================

def register_user(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Account created successfully! Welcome {user.username}.')
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})


def login_user(request):
    if request.user.is_authenticated:
        if request.user.is_superuser or request.user.is_staff:
            return redirect('/django-admin/')
        return redirect('home')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            next_url = request.GET.get('next', '')
            if next_url:
                return redirect(next_url)
            if user.is_superuser or user.is_staff:
                return redirect('/django-admin/')
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})


def logout_user(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('home')


# ==================== CUSTOMER PORTAL VIEWS ==================

from django.contrib.auth.decorators import login_required

@login_required(login_url='login')
def customer_dashboard(request):
    """Customer dashboard for viewing order history and reservations"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    reservations = Reservation.objects.filter(user=request.user).order_by('-date', '-time')
    
    return render(request, 'dashboard.html', {
        'orders': orders,
        'reservations': reservations
    })

@login_required(login_url='login')
def cancel_order_customer(request, order_id):
    """Allow customer to cancel a pending order and restore inventory"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.status == 'Pending':
        with transaction.atomic():
            order.status = 'Cancelled'
            order.save()
            
            # Restore inventory (MenuItemIngredient only)
            for item in order.items.all():
                recipe_items = item.menu_item.recipe_items.all()
                if recipe_items.exists():
                    for recipe_item in recipe_items:
                        inv = recipe_item.inventory_item
                        restored_qty = recipe_item.quantity_required * item.quantity
                        inv.refill_inventory(restored_qty, notes=f"Restored from cancelled order #{order.id}")

        messages.success(request, f'Order #{order.id} has been cancelled.')
    else:
        messages.error(request, 'You can only cancel pending orders.')
    return redirect('dashboard')

@login_required(login_url='login')
def cancel_reservation_customer(request, reservation_id):
    """Allow customer to cancel a reservation"""
    reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)
    if not reservation.confirmed:
        reservation.delete()
        messages.success(request, 'Reservation has been cancelled.')
    else:
        # Confirmed reservations might require calling the restaurant
        messages.info(request, 'This reservation is already confirmed. Please call the restaurant to cancel.')
    return redirect('dashboard')

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
    from .models import Category
    categories = Category.objects.all()
    
    # Base queryset: only active items
    base_qs = MenuItem.objects.filter(is_active=True).order_by('id')

    # Get menu items, optionally filtered by category, limited to 25
    if selected_category:
        try:
            category_id = int(selected_category)
            menu_items = base_qs.filter(category_id=category_id)[:25]
        except ValueError:
            menu_items = base_qs[:25]
    else:
        menu_items = base_qs[:25]
    
    available_tables = Table.objects.filter(status='Available')
    reserved_table_ids = []

    if request.user.is_authenticated:
        reserved_table_ids = list(
            Reservation.objects.filter(
                user=request.user,
                status='Approved',
                date__gte=timezone.now().date(),
                table__isnull=False
            )
            .values_list('table_id', flat=True)
            .distinct()
        )

    tables = Table.objects.filter(
        Q(id__in=reserved_table_ids) | Q(id__in=available_tables.values('id'))
    ).distinct().order_by('table_number')
    
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
        'reserved_table_ids': reserved_table_ids,
        'cart': cart,
        'total': float(round(total, 2)),
        'tax': float(round(tax, 2)),
        'total_with_tax': float(round(total_with_tax, 2)),
        'cart_count': cart_count,
    }
    return render(request, 'menu.html', context)


@require_http_methods(["POST"])
def add_to_cart(request):
    """Add item to cart (session-based) with availability validation"""
    try:
        item_id = int(request.POST.get('item_id'))
        qty = int(request.POST.get('quantity', 1))
        instructions = request.POST.get('instructions', '').strip()
        
        menu_item = get_object_or_404(MenuItem, id=item_id)
        
        # Check if item is currently available
        if not menu_item.is_available():
            missing = menu_item.get_missing_ingredients()
            msg = f"Cannot add to cart: {menu_item.name} is unavailable. "
            msg += "Missing: " + ", ".join([
                f"{m['name']} ({m['current']}/{m['required']}{m['unit']})"
                for m in missing
            ])
            messages.error(request, msg)
            return redirect('menu')
        
        # Check availability for the requested quantity (including existing qty in cart)
        cart = request.session.get('cart', [])
        item_in_cart = next((i for i in cart if i['id'] == item_id), None)
        existing_qty = item_in_cart['qty'] if item_in_cart else 0
        total_requested = existing_qty + qty
        
        ok, msg = menu_item.can_fulfill_order(quantity=total_requested)
        if not ok:
            messages.error(request, f"Cannot add to cart: {msg} - Requested {total_requested} but insufficient inventory")
            return redirect('menu')
        
        # Create a unique ID for the cart item based on item ID and customizations
        cart_item_id = f"{item_id}_{instructions}"
        
        item_in_cart = next((i for i in cart if i.get('cart_id') == cart_item_id), None)
        
        # Add to cart
        if item_in_cart:
            item_in_cart['qty'] += qty
        else:
            cart.append({
                'cart_id': cart_item_id,
                'id': menu_item.id,
                'name': menu_item.name,
                'price': float(menu_item.price),
                'qty': qty,
                'image': menu_item.image.url if menu_item.image else '',
                'instructions': instructions,
            })
        
        request.session['cart'] = cart
        messages.success(request, f'✅ Added {qty}x {menu_item.name} to cart')
        
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
        cart_id = data.get('cart_id')
        change = int(data.get('change', 1))  # +1 or -1
        
        cart = request.session.get('cart', [])
        
        # Find item in cart
        item_in_cart = next((i for i in cart if i.get('cart_id') == cart_id), None)
        
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
        cart_id = data.get('cart_id')
        
        cart = request.session.get('cart', [])
        
        # Find item in cart
        item_in_cart = next((i for i in cart if i.get('cart_id') == cart_id), None)
        
        # Remove item from cart
        if item_in_cart:
            cart.remove(item_in_cart)
        
        request.session['cart'] = cart
        request.session.modified = True
        
        return JsonResponse({'status': 'success', 'cart': cart})
    
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@require_http_methods(["POST", "GET"])
def checkout(request):
    """Checkout page showing final bill and payment options"""
    cart = request.session.get('cart', [])
    if not cart:
        messages.error(request, 'Your cart is empty!')
        return redirect('menu')
        
    if request.method == "POST":
        # Save order preferences into session before payment
        request.session['order_prefs'] = {
            'order_type': request.POST.get('order_type', 'Dine-in'),
            'table_id': request.POST.get('table', ''),
        }
    
    prefs = request.session.get('order_prefs', {'order_type': 'Dine-in'})
    
    total = Decimal(str(sum(item['price'] * item['qty'] for item in cart)))
    tax = total * Decimal('0.18')  # 18% GST
    total_with_tax = total + tax

    context = {
        'cart': cart,
        'total': float(round(total, 2)),
        'tax': float(round(tax, 2)),
        'total_with_tax': float(round(total_with_tax, 2)),
        'prefs': prefs,
    }
    return render(request, 'checkout.html', context)


@require_http_methods(["POST"])
def place_order(request):
    """Place an order with atomic transaction and inventory deduction"""
    cart = request.session.get('cart', [])
    prefs = request.session.get('order_prefs', {})
    
    if not cart:
        messages.error(request, 'Your cart is empty!')
        return redirect('menu')
    
    try:
        # Get form data from checkout page
        payment_method = request.POST.get('payment_method', 'Card')
        customer_name = request.POST.get('customer_name', '')
        customer_phone = request.POST.get('customer_phone', '')
        
        order_type = prefs.get('order_type', 'Dine-in')
        table_id = prefs.get('table_id', '')

        # For dine-in orders, a table number is required
        if order_type == 'Dine-in' and not table_id:
            messages.error(request, 'Please select a table number for dine-in orders.')
            return redirect('checkout')
        
        # Calculate final amounts
        total = Decimal(str(sum(item['price'] * item['qty'] for item in cart)))
        tax = total * Decimal('0.18')
        total_with_tax = total + tax
        
        # Validate cart items exist in DB
        menu_items_dict = {}
        for cart_item in cart:
            item = MenuItem.objects.get(id=cart_item['id'])
            menu_items_dict[item.id] = item
        
        # PRE-CHECK: Verify availability for each cart item before creating order
        for cart_item in cart:
            menu_item = menu_items_dict[cart_item['id']]
            qty = cart_item['qty']
            
            # Check if item is currently available
            if not menu_item.is_available():
                messages.error(
                    request, 
                    f'❌ {menu_item.name} is currently unavailable - missing required ingredients'
                )
                return redirect('menu')
            
            # Check if we can fulfill the specific order quantity
            ok, msg = menu_item.can_fulfill_order(quantity=qty)
            if not ok:
                messages.error(request, f'❌ Cannot place order: {msg}')
                return redirect('menu')
        
        # Get table if dine-in
        table = None
        if order_type == 'Dine-in' and table_id:
            table = get_object_or_404(Table, id=table_id)
            if table.status != 'Available':
                has_valid_reservation = False
                if request.user.is_authenticated:
                    has_valid_reservation = Reservation.objects.filter(
                        user=request.user,
                        table=table,
                        status='Approved',
                        date=timezone.now().date()
                    ).exists()

                if not has_valid_reservation:
                    messages.error(
                        request,
                        'Selected table is not currently available for dine-in ordering.'
                    )
                    return redirect('menu')

            table.status = 'Occupied'
            table.save()
        
        # ATOMIC TRANSACTION: Create order and deduct inventory
        try:
            with transaction.atomic():
                # Create order
                order = Order.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    customer_name=customer_name or (request.user.get_full_name() if request.user.is_authenticated else ''),
                    customer_phone=customer_phone,
                    order_type=order_type,
                    table=table,
                    payment_method=payment_method,
                    payment_status='Completed',
                    total_amount=total,
                    tax_amount=tax,
                    final_amount=total_with_tax,
                    status='Pending'
                )

                # Create order items and deduct inventory
                for cart_item in cart:
                    menu_item = menu_items_dict[cart_item['id']]
                    qty = cart_item['qty']
                    instructions = cart_item.get('instructions', '')

                    # This creates the OrderItem
                    OrderItem.objects.create(
                        order=order,
                        menu_item=menu_item,
                        quantity=qty,
                        price=menu_item.price,
                        special_instructions=instructions
                    )
                    
                    # Deduct inventory explicitly and atomically for each order item
                    menu_item.deduct_inventory(qty)
                
                # Clear session
                request.session.pop('cart', None)
                request.session.pop('order_prefs', None)
                
                messages.success(
                    request,
                    f'✅ Payment successful! Order #{order.id} placed successfully! '
                )
                return redirect('order_confirmation', order_id=order.id)
                
        except ValueError as e:
            messages.error(request, f'❌ Order Failed - {str(e)}')
            return redirect('menu')
        
    except MenuItem.DoesNotExist:
        messages.error(request, '❌ One or more items in your cart are no longer available')
        return redirect('menu')
    except Exception as e:
        messages.error(request, f'❌ Error placing order: {str(e)}')
        return redirect('menu')


def order_confirmation(request, order_id):
    """Order confirmation page"""
    order = get_object_or_404(Order, id=order_id)
    context = {'order': order}
    return render(request, 'order_confirmation.html', context)


def menu_availability_api(request):
    """API endpoint: Real-time menu availability based on inventory
    
    Returns JSON with availability status for all menu items
    Example: /api/menu/availability/
    """
    menu_items = MenuItem.objects.all()
    
    availability_data = []
    for item in menu_items:
        availability_data.append({
            'id': item.id,
            'name': item.name,
            'available': item.is_available(),
            'ingredients': [
                {
                    'name': ing.inventory_item.name,
                    'required': ing.quantity_required,
                    'current': ing.inventory_item.quantity,
                    'unit': ing.inventory_item.unit,
                    'sufficient': ing.inventory_item.quantity >= ing.quantity_required,
                }
                for ing in item.recipe_items.all()
            ]
        })
    
    return JsonResponse({
        'timestamp': timezone.now().isoformat(),
        'menu_items': availability_data,
        'summary': {
            'total_items': menu_items.count(),
            'available_count': sum(1 for item in menu_items if item.is_available()),
            'unavailable_count': sum(1 for item in menu_items if not item.is_available()),
        }
    })


def is_table_available(date, time, guests, exclude_reservation_id=None):
    """
    Check if there is an available table for the given capacity, date, and time.
    Assuming dining duration is max 2 hours.
    Locks the table temporarily if inside a transaction.
    """
    from datetime import datetime, timedelta
    
    # Calculate a 2-hour blocking window
    booking_time = datetime.combine(date, time)
    window_start = (booking_time - timedelta(hours=1, minutes=59)).time()
    window_end = (booking_time + timedelta(hours=1, minutes=59)).time()
    
    # strictly lock tables that we are checking to avoid race condition where two requests
    # find the same table available simultaneously
    eligible_tables = Table.objects.select_for_update().filter(
        capacity__gte=guests,
        status='Available'
    )
    
    for table in eligible_tables:
        # Check overlapping approved reservations for this specific table
        overlapping = Reservation.objects.filter(
            table=table,
            date=date,
            status='Approved',
            time__range=(window_start, window_end)
        )
        if exclude_reservation_id:
            overlapping = overlapping.exclude(id=exclude_reservation_id)
            
        if not overlapping.exists():
            return table  # Found a completely free table for this time slot
            
    return None

@login_required(login_url='login')
def reservations(request):
    """Reservations page"""
    form = ReservationForm()
    
    # Show active user reservations if logged in
    user_reservations = []
    if request.user.is_authenticated:
        user_reservations = Reservation.objects.filter(
            user=request.user,
            date__gte=timezone.now().date()
        ).exclude(status__in=['Completed', 'Cancelled']).order_by('date', 'time')
        
    context = {
        'form': form,
        'user_reservations': user_reservations,
    }
    return render(request, 'reservations.html', context)


@login_required(login_url='login')
@require_http_methods(["POST"])
def make_reservation(request):
    """Process reservation"""
    form = ReservationForm(request.POST)
    
    if form.is_valid():
        date = form.cleaned_data['date']
        time = form.cleaned_data['time']
        guests = form.cleaned_data['guests']
        
        # Don't allow booking in the past
        booking_datetime = datetime.combine(date, time)
        if booking_datetime < datetime.now():
            messages.error(request, '❌ Cannot make a reservation for a past date or time.')
            return redirect('reservations')
            
        try:
            with transaction.atomic():
                # Check if a table would be available (now properly locked against concurrent requests)
                table = is_table_available(date, time, guests)
                
                if not table:
                    messages.error(request, '❌ Sorry, no tables are available for that exact date, time, and party size. Please try another slot.')
                    return redirect('reservations')
                    
                reservation = form.save(commit=False)
                reservation.table = table
                reservation.status = 'Approved'
                reservation.confirmed = True
                
                if request.user.is_authenticated:
                    reservation.user = request.user
                    
                reservation.save()
                messages.success(
                    request,
                    f'Reservation confirmed. Table {table.table_number} has been allotted for your slot.'
                )
                return redirect('reservations')
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
            return redirect('reservations')
    
    messages.error(request, 'Failed to make reservation. Please check your inputs.')
    return redirect('reservations')


