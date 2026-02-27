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
    InventoryItem, Recipe, RecipeIngredient
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
            
            # Restore inventory
            for item in order.items.all():
                recipe_items = item.menu_item.recipe_items.all()
                if recipe_items.exists():
                    for recipe_item in recipe_items:
                        inv = recipe_item.inventory_item
                        restored_qty = recipe_item.quantity_required * item.quantity
                        inv.refill_inventory(restored_qty, notes=f"Restored from cancelled order #{order.id}")
                elif hasattr(item.menu_item, 'recipe') and item.menu_item.recipe.ingredients.exists():
                    for ing in item.menu_item.recipe.ingredients.all():
                        if ing.inventory_item:
                            inv = ing.inventory_item
                            restored_qty = ing.quantity * item.quantity
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
    
    # Get menu items, optionally filtered by category
    if selected_category:
        try:
            category_id = int(selected_category)
            menu_items = MenuItem.objects.filter(category_id=category_id)
        except ValueError:
            menu_items = MenuItem.objects.all()
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
    eligible_tables = Table.objects.select_for_update().filter(capacity__gte=guests)
    
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
                reservation.status = 'Pending'  # Must be approved by admin
                
                if request.user.is_authenticated:
                    reservation.user = request.user
                    
                reservation.save()
                messages.success(request, '✅ Reservation request submitted! It is currently Pending and will appear in your dashboard.')
                return redirect('reservations')
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
            return redirect('reservations')
    
    messages.error(request, 'Failed to make reservation. Please check your inputs.')
    return redirect('reservations')


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
    ).exclude(status__in=['Pending', 'Cancelled', 'Rejected']).order_by('date', 'time')[:5]
    
    pending_reservations = Reservation.objects.filter(status='Pending').order_by('date', 'time')
    
    # Calculate stats
    today_orders = Order.objects.filter(
        created_at__date=timezone.now().date()
    ).count()
    
    today_revenue = Order.objects.filter(
        created_at__date=timezone.now().date(),
        status__in=['Completed', 'Ready']
    ).aggregate(total=Sum('final_amount'))['total'] or 0
    
    context = {
        'recent_orders': recent_orders,
        'pending_orders': pending_orders,
        'low_stock_items': low_stock_items,
        'tables': tables,
        'occupied_tables': occupied_tables,
        'upcoming_reservations': upcoming_reservations,
        'pending_reservations': pending_reservations,
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
    order = get_object_or_404(Order, id=order_id)
    status = request.POST.get('status', 'Pending')
    
    if status in dict(Order.STATUS_CHOICES):
        old_status = order.status
        order.status = status
        if status == 'Completed':
            order.completed_at = timezone.now()
        
        with transaction.atomic():
            order.save()
            
            # If changing to Cancelled from a non-cancelled state, restore inventory
            if status == 'Cancelled' and old_status != 'Cancelled':
                for item in order.items.all():
                    recipe_items = item.menu_item.recipe_items.all()
                    if recipe_items.exists():
                        for recipe_item in recipe_items:
                            inv = recipe_item.inventory_item
                            restored_qty = recipe_item.quantity_required * item.quantity
                            inv.refill_inventory(restored_qty, notes=f"Restored from cancelled order #{order.id} by admin")
                    elif hasattr(item.menu_item, 'recipe') and item.menu_item.recipe.ingredients.exists():
                        for ing in item.menu_item.recipe.ingredients.all():
                            if ing.inventory_item:
                                inv = ing.inventory_item
                                restored_qty = ing.quantity * item.quantity
                                inv.refill_inventory(restored_qty, notes=f"Restored from cancelled order #{order.id} by admin")

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
    # Exclude historical/cancelled to focus on active management
    reservations = Reservation.objects.exclude(status='Cancelled').order_by('-date', '-time')
    
    context = {
        'reservations': reservations,
    }
    return render(request, 'admin/reservations.html', context)


@require_http_methods(["POST"])
def confirm_reservation(request, reservation_id):
    """Update reservation status via Admin panel"""
    reservation = get_object_or_404(Reservation, id=reservation_id)
    new_status = request.POST.get('status')
    
    if new_status not in dict(Reservation.STATUS_CHOICES):
        messages.error(request, 'Invalid status.')
        return redirect('admin_reservations')
        
    if new_status == 'Approved':
        # Re-verify availability
        table = is_table_available(reservation.date, reservation.time, reservation.guests, exclude_reservation_id=reservation.id)
        if not table:
            messages.error(request, 'Cannot approve: No tables available for this time/capacity.')
            return redirect('admin_reservations')
        reservation.table = table
        reservation.confirmed = True
    elif new_status in ['Rejected', 'Cancelled', 'Completed']:
        # Free up the assigned table slots by just unlinking or keeping track
        # Since logic filters by 'Approved', merely changing status is enough
        pass

    reservation.status = new_status
    reservation.save()
    messages.success(request, f'Reservation form {reservation.name} marked as {new_status}.')
    return redirect('admin_reservations')


@require_http_methods(["POST"])
def cancel_reservation_admin(request, reservation_id):
    """Admin cancel/delete reservation"""
    if not request.user.is_staff:
        return redirect('home')
        
    reservation = get_object_or_404(Reservation, id=reservation_id)
    name = reservation.name
    reservation.delete()
    messages.success(request, f'Reservation for "{name}" has been deleted.')
    return redirect('admin_reservations')


from django.db.models import Count

def admin_reports(request):
    """Admin reports for sales, revenue, and top items"""
    # Date filters
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    orders = Order.objects.filter(status__in=['Completed', 'Delivered'])
    
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            orders = orders.filter(created_at__date__gte=start_date)
        except ValueError:
            pass
            
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            orders = orders.filter(created_at__date__lte=end_date)
        except ValueError:
            pass
            
    # Key Metrics
    total_sales = orders.count()
    total_revenue = orders.aggregate(total=Sum('final_amount'))['total'] or 0
    total_tax = orders.aggregate(tax=Sum('tax_amount'))['tax'] or 0
    
    # Top Selling Items
    top_items = OrderItem.objects.filter(order__in=orders) \
        .values('menu_item__name') \
        .annotate(total_quantity=Sum('quantity'), total_revenue=Sum(F('quantity') * F('price'))) \
        .order_by('-total_quantity')[:10]
        
    # Orders by Day
    sales_by_date = orders.values('created_at__date') \
        .annotate(daily_revenue=Sum('final_amount'), daily_orders=Count('id')) \
        .order_by('-created_at__date')[:30]
        
    context = {
        'total_sales': total_sales,
        'total_revenue': total_revenue,
        'total_tax': total_tax,
        'top_items': top_items,
        'sales_by_date': sales_by_date,
        'start_date': start_date_str,
        'end_date': end_date_str,
    }
    return render(request, 'admin/reports.html', context)


# ==================== MENU ADMIN VIEWS ====================

def admin_menu(request):
    """Admin menu management list view"""
    if not request.user.is_staff:
        return redirect('home')
        
    menu_items = MenuItem.objects.all().order_by('category__name', 'name')
    context = {'menu_items': menu_items}
    return render(request, 'admin/menu.html', context)


def admin_menu_add(request):
    """Admin menu item creation"""
    if not request.user.is_staff:
        return redirect('home')
        
    if request.method == 'POST':
        form = MenuItemForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                menu_item = form.save()
                
                # Make sure a Recipe exists too
                Recipe.objects.get_or_create(menu_item=menu_item)
                
                formset = MenuItemIngredientFormSet(request.POST, instance=menu_item)
                if formset.is_valid():
                    formset.save()
                    messages.success(request, f'Menu item "{menu_item.name}" created successfully!')
                    return redirect('admin_menu')
        else:
            formset = MenuItemIngredientFormSet(request.POST)
    else:
        form = MenuItemForm()
        formset = MenuItemIngredientFormSet()
        
    context = {
        'title': 'Add Menu Item',
        'form': form,
        'formset': formset,
    }
    return render(request, 'admin/menu_form.html', context)


def admin_menu_edit(request, item_id):
    """Admin menu item editing"""
    if not request.user.is_staff:
        return redirect('home')
        
    menu_item = get_object_or_404(MenuItem, id=item_id)
    
    if request.method == 'POST':
        form = MenuItemForm(request.POST, request.FILES, instance=menu_item)
        if form.is_valid():
            with transaction.atomic():
                menu_item = form.save()
                
                # Make sure a Recipe exists too
                Recipe.objects.get_or_create(menu_item=menu_item)
                
                formset = MenuItemIngredientFormSet(request.POST, instance=menu_item)
                if formset.is_valid():
                    formset.save()
                    messages.success(request, f'Menu item "{menu_item.name}" updated successfully!')
                    return redirect('admin_menu')
        else:
            formset = MenuItemIngredientFormSet(request.POST, instance=menu_item)
    else:
        form = MenuItemForm(instance=menu_item)
        formset = MenuItemIngredientFormSet(instance=menu_item)
        
    context = {
        'title': f'Edit {menu_item.name}',
        'form': form,
        'formset': formset,
        'item': menu_item
    }
    return render(request, 'admin/menu_form.html', context)


@require_http_methods(["POST"])
def admin_menu_delete(request, item_id):
    """Admin menu item deletion"""
    if not request.user.is_staff:
        return redirect('home')
        
    menu_item = get_object_or_404(MenuItem, id=item_id)
    name = menu_item.name
    menu_item.delete()
    messages.success(request, f'Menu item "{name}" deleted successfully.')
    return redirect('admin_menu')



