from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django import forms
from .models import (
    MenuItem, Order, OrderItem, Reservation, Table, 
    InventoryItem, MenuItemIngredient, InventoryLog,
    Recipe, RecipeIngredient, Category
)


# ============================================================================
# INVENTORY MANAGEMENT ADMIN
# ============================================================================

class InventoryItemForm(forms.ModelForm):
    """Form for editing inventory with change notes"""
    change_notes = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Optional: Reason for this change (damaged, delivered, corrected, etc.)'
        })
    )
    
    class Meta:
        model = InventoryItem
        fields = ('name', 'quantity', 'unit', 'reorder_level', 'reorder_quantity', 'price_per_unit')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['name'].widget.attrs['readonly'] = True
            self.fields['unit'].widget.attrs['readonly'] = True
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if self.instance.pk:  # Updating existing
            old_quantity = self.instance.quantity
            new_quantity = instance.quantity
            
            if old_quantity != new_quantity:
                quantity_changed = new_quantity - old_quantity
                change_notes = self.cleaned_data.get('change_notes', '')
                
                if commit:
                    instance.save()
                    
                    # Log the change
                    if quantity_changed > 0:
                        action = 'Added'
                    elif quantity_changed < 0:
                        action = 'Adjusted'
                    else:
                        action = 'Adjusted'
                    
                    InventoryLog.objects.create(
                        inventory_item=instance,
                        action=action,
                        quantity_changed=quantity_changed,
                        previous_quantity=old_quantity,
                        new_quantity=new_quantity,
                        notes=change_notes or f"Manual adjustment in admin"
                    )
            else:
                if commit:
                    instance.save()
        else:  # Creating new
            if commit:
                instance.save()
        
        return instance


# ============================================================================
# INVENTORY MANAGEMENT ADMIN
# ============================================================================

@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    form = InventoryItemForm
    list_display = ('name', 'quantity', 'unit', 'status_badge', 'reorder_level', 'last_updated')
    list_filter = ('unit', 'last_updated')
    search_fields = ('name',)
    readonly_fields = ('last_updated',)
    fields = ('name', 'quantity', 'unit', 'reorder_level', 'reorder_quantity', 'price_per_unit', 'change_notes', 'last_updated')
    actions = ['refill_to_reorder_qty']
    
    def status_badge(self, obj):
        status = obj.get_status()
        colors = {
            'Out of Stock': 'red',
            'Low Stock': 'orange',
            'In Stock': 'green',
        }
        color = colors.get(status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            status
        )
    status_badge.short_description = 'Status'
    
    @admin.action(description="🔄 Refill to Reorder Quantity")
    def refill_to_reorder_qty(self, request, queryset):
        """Refill items to their reorder quantity and log the action"""
        count = 0
        for item in queryset:
            quantity_needed = item.reorder_quantity - item.quantity
            if quantity_needed > 0:
                item.refill_inventory(quantity_needed, notes="Refilled to reorder quantity")
                count += 1
        
        if count > 0:
            self.message_user(request, f"✅ {count} item(s) refilled. All dependent menu items will be automatically available if ingredients are sufficient.")
        else:
            self.message_user(request, "ℹ️  Selected items already at or above reorder quantity.")


@admin.register(InventoryLog)
class InventoryLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'inventory_item', 'action_display', 'quantity_display', 'status_change')
    list_filter = ('action', 'created_at', 'inventory_item')
    search_fields = ('inventory_item__name', 'notes')
    readonly_fields = ('inventory_item', 'action', 'quantity_changed', 'previous_quantity', 'new_quantity', 'created_at')
    date_hierarchy = 'created_at'
    
    def action_display(self, obj):
        colors = {
            'Added': 'green',
            'Used': 'orange',
            'Adjusted': 'blue',
            'Returned': 'purple',
            'Damaged': 'red',
        }
        color = colors.get(obj.action, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px;">{}</span>',
            color,
            obj.action
        )
    action_display.short_description = 'Action'
    
    def quantity_display(self, obj):
        icon = '➕' if obj.quantity_changed > 0 else '➖' if obj.quantity_changed < 0 else '='
        return f"{icon} {obj.quantity_changed}"
    quantity_display.short_description = 'Change'
    
    def status_change(self, obj):
        return f"{obj.previous_quantity} → {obj.new_quantity}"
    status_change.short_description = 'Inventory Change'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


# ============================================================================
# MENU ITEM MANAGEMENT WITH INVENTORY
# ============================================================================

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

class MenuItemIngredientInline(admin.TabularInline):
    model = MenuItemIngredient
    extra = 1
    fields = ('inventory_item', 'quantity_required')


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'availability_badge', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'availability_status')
    inlines = [MenuItemIngredientInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'category', 'price', 'description')
        }),
        ('Media', {
            'fields': ('image',)
        }),
        ('Availability', {
            'fields': ('availability_status',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def availability_badge(self, obj):
        if obj.is_available():
            return format_html('<span style="color: green; font-weight: bold;">✓ Available</span>')
        else:
            return format_html('<span style="color: red; font-weight: bold;">✗ Out of Stock</span>')
    availability_badge.short_description = 'Availability'
    
    def availability_status(self, obj):
        if obj.is_available():
            ingredients = obj.recipe_items.all()
            if ingredients.exists():
                status = '<div style="background-color: #d4edda; padding: 10px; border-radius: 5px;"><strong>✓ In Stock</strong><br>'
                for ing in ingredients:
                    status += f'  • {ing.inventory_item.name}: {ing.inventory_item.quantity}/{ing.quantity_required} {ing.inventory_item.unit}<br>'
                status += '</div>'
            else:
                status = '<div style="background-color: #d4edda; padding: 10px;">✓ No inventory tracking required</div>'
        else:
            status = '<div style="background-color: #f8d7da; padding: 10px; border-radius: 5px;"><strong>✗ Out of Stock</strong><br>'
            ingredients = obj.recipe_items.all()
            for ing in ingredients:
                if ing.inventory_item.quantity < ing.quantity_required:
                    status += f'  • {ing.inventory_item.name}: INSUFFICIENT ({ing.inventory_item.quantity}/{ing.quantity_required})<br>'
            status += '</div>'
        return mark_safe(status)
    availability_status.short_description = 'Inventory Status'


@admin.register(MenuItemIngredient)
class MenuItemIngredientAdmin(admin.ModelAdmin):
    list_display = ('menu_item', 'inventory_item', 'quantity_required', 'unit_display', 'current_stock')
    list_filter = ('menu_item__category',)
    search_fields = ('menu_item__name', 'inventory_item__name')
    fields = ('menu_item', 'inventory_item', 'quantity_required')
    
    def unit_display(self, obj):
        return obj.inventory_item.unit
    unit_display.short_description = 'Unit'
    
    def current_stock(self, obj):
        stock = obj.inventory_item.quantity
        required = obj.quantity_required
        if stock < required:
            color = 'red'
            icon = '⚠️'
        elif stock < required * 5:
            color = 'orange'
            icon = '⚠️'
        else:
            color = 'green'
            icon = '✓'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}/{}</span>',
            color,
            icon,
            stock,
            required
        )
    current_stock.short_description = 'Current Stock / Required'


# ============================================================================
# ORDER MANAGEMENT WITH INVENTORY
# ============================================================================

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('menu_item', 'quantity', 'price', 'subtotal')
    can_delete = False
    fields = ('menu_item', 'quantity', 'price')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    inlines = [OrderItemInline]
    list_display = ('id', 'order_type', 'table', 'total_amount', 'status_badge', 'payment_method', 'created_at')
    list_filter = ('status', 'order_type', 'payment_method', 'created_at')
    search_fields = ('id',)
    readonly_fields = ('id', 'created_at', 'total_amount')
    actions = ['mark_in_kitchen', 'mark_preparing', 'mark_ready', 'mark_delivered', 'mark_completed', 'cancel_order']
    
    fieldsets = (
        ('Order Information', {
            'fields': ('id', 'order_type', 'table', 'total_amount', 'created_at')
        }),
        ('Status', {
            'fields': ('status', 'completed_at')
        }),
        ('Payment', {
            'fields': ('payment_method',)
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'Pending': 'orange',
            'In Kitchen': 'blue',
            'Preparing': 'cyan',
            'Ready': 'yellow',
            'Delivered Pending': 'purple',
            'Completed': 'green',
            'Cancelled': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.status
        )
    status_badge.short_description = 'Order Status'
    
    @admin.action(description="🍳 Mark as In Kitchen")
    def mark_in_kitchen(self, request, queryset):
        updated = queryset.filter(status='Pending').update(status='In Kitchen')
        if updated > 0:
            # Deduct inventory when order goes to kitchen
            for order in queryset.filter(status='In Kitchen'):
                for item in order.items.all():
                    item.menu_item.deduct_inventory(item.quantity)
        self.message_user(request, f'{updated} order(s) marked as in kitchen. Inventory deducted.')
    
    @admin.action(description="👨‍🍳 Mark as Preparing")
    def mark_preparing(self, request, queryset):
        updated = queryset.update(status='Preparing')
        self.message_user(request, f'{updated} order(s) marked as preparing.')
    
    @admin.action(description="📦 Mark as Ready")
    def mark_ready(self, request, queryset):
        updated = queryset.update(status='Ready')
        self.message_user(request, f'{updated} order(s) marked as ready for delivery.')
    
    @admin.action(description="⏳ Mark as Delivered Pending")
    def mark_delivered(self, request, queryset):
        updated = queryset.update(status='Delivered Pending')
        self.message_user(request, f'{updated} order(s) marked as delivered pending.')
    
    @admin.action(description="✅ Mark as Completed")
    def mark_completed(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(status='Completed', completed_at=timezone.now())
        self.message_user(request, f'{updated} order(s) marked as completed.')
    
    @admin.action(description="❌ Cancel Order")
    def cancel_order(self, request, queryset):
        updated = queryset.filter(status__in=['Pending', 'In Kitchen']).update(status='Cancelled')
        self.message_user(request, f'{updated} order(s) cancelled.')


# ============================================================================
# OTHER ADMIN CLASSES
# ============================================================================

@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ('table_number', 'capacity', 'status', 'status_badge')
    list_filter = ('status',)
    list_editable = ('status',)
    
    def status_badge(self, obj):
        colors = {
            'Available': 'green',
            'Occupied': 'orange',
            'Reserved': 'blue',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.status
        )
    status_badge.short_description = 'Status Badge'


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'time', 'guests', 'confirmed_badge', 'table', 'created_at')
    list_filter = ('confirmed', 'date', 'created_at')
    search_fields = ('name', 'phone', 'email')
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Guest Information', {
            'fields': ('name', 'phone', 'email')
        }),
        ('Reservation Details', {
            'fields': ('date', 'time', 'guests', 'table')
        }),
        ('Status', {
            'fields': ('confirmed',)
        }),
        ('Additional Notes', {
            'fields': ('notes',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    actions = ['confirm_bookings', 'cancel_bookings']
    
    def confirmed_badge(self, obj):
        if obj.confirmed:
            return mark_safe(
                '<span style="background-color: green; color: white; padding: 3px 10px; border-radius: 3px;">✓ Confirmed</span>'
            )
        else:
            return mark_safe(
                '<span style="background-color: orange; color: white; padding: 3px 10px; border-radius: 3px;">⏳ Pending</span>'
            )
    confirmed_badge.short_description = 'Confirmation Status'
    
    @admin.action(description="✓ Confirm Booking")
    def confirm_bookings(self, request, queryset):
        updated = queryset.update(confirmed=True)
        self.message_user(request, f'{updated} reservation(s) confirmed.')
    
    @admin.action(description="❌ Cancel Booking")
    def cancel_bookings(self, request, queryset):
        updated = queryset.delete()[0]
        self.message_user(request, f'{updated} reservation(s) cancelled.')


# Keep old models registered for backwards compatibility
admin.site.register(Recipe)
admin.site.register(RecipeIngredient)

