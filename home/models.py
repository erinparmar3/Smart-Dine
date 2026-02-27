from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.contrib.auth.models import User

class Category(models.Model):
    """Food categories"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
        
    def __str__(self):
        return self.name

class InventoryItem(models.Model):
    """Inventory tracking for ingredients - Base ingredient inventory"""
    UNIT_CHOICES = [
        ('g', 'Gram'),
        ('ml', 'Milliliter'),
        ('pcs', 'Pieces'),
    ]

    name = models.CharField(max_length=100, unique=True)
    quantity = models.FloatField(default=0.0, validators=[MinValueValidator(0.0)])
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='g')
    reorder_level = models.FloatField(default=0.0)  # alert when below this
    reorder_quantity = models.FloatField(default=0.0)  # quantity to order when restocking
    price_per_unit = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.quantity} {self.unit}"
    
    def save(self, *args, **kwargs):
        """Override save to prevent negative quantities"""
        if self.quantity < 0:
            # Prevent negative inventory
            old_quantity = self.quantity
            self.quantity = 0
            
            # Log this forced correction
            super().save(*args, **kwargs)
            
            InventoryLog.objects.create(
                inventory_item=self,
                action='Adjusted',
                quantity_changed=0 - old_quantity,
                previous_quantity=old_quantity,
                new_quantity=self.quantity,
                notes="Prevented negative inventory - qty reset to 0"
            )
            return
        
        super().save(*args, **kwargs)
    
    def refill_inventory(self, quantity_added, notes=""):
        """Refill inventory and auto-update availability of dependent menu items
        
        This is the ONLY way to restore inventory availability.
        Automatically marks menu items as Available if all ingredients are now sufficient.
        """
        from django.db import transaction
        
        with transaction.atomic():
            # Lock this specific inventory item
            item = InventoryItem.objects.select_for_update().get(id=self.id)
            
            old_qty = item.quantity
            item.quantity += quantity_added
            
            if item.quantity < 0:
                item.quantity = 0
            
            item.save()
            
            # Update self to reflect changes in current object proxy
            self.quantity = item.quantity
            
            # Log the refill
            InventoryLog.objects.create(
                inventory_item=item,
                action='Added',
                quantity_changed=quantity_added,
                previous_quantity=old_qty,
                new_quantity=item.quantity,
                notes=notes or "Manual inventory refill"
            )
    
    def get_dependent_menu_items(self):
        """Get all menu items that depend on this ingredient"""
        return MenuItem.objects.filter(recipe_items__inventory_item=self).distinct()
    
    def is_low_stock(self):
        """Check if stock is below reorder level"""
        return self.quantity < self.reorder_level
    
    def get_status(self):
        """Get current stock status"""
        if self.quantity == 0:
            return 'Out of Stock'
        elif self.is_low_stock():
            return 'Low Stock'
        else:
            return 'In Stock'
    
    class Meta:
        verbose_name_plural = "Inventory Items"
        ordering = ['name']


class MenuItem(models.Model):
    """Menu items available in the restaurant"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='menu_items')
    is_active = models.BooleanField(default=True, help_text="Is this item currently on the menu?")
    image = models.ImageField(upload_to='menu_items/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - ₹{self.price}"
    
    def is_available(self):
        """Check if all required ingredients are in stock"""
        # Prefer the new MenuItemIngredient recipe_items, fallback to legacy Recipe
        recipe_items = self.recipe_items.all()
        if recipe_items.exists():
            for recipe_item in recipe_items:
                if recipe_item.inventory_item.quantity < recipe_item.quantity_required:
                    return False
            return True

        # Fallback to legacy Recipe/RecipeIngredient if present
        if hasattr(self, 'recipe') and self.recipe.ingredients.exists():
            for ing in self.recipe.ingredients.all():
                if ing.inventory_item and ing.inventory_item.quantity < ing.quantity:
                    return False
            return True

        return True
    
    def get_missing_ingredients(self):
        """Get list of ingredients that are out of stock or insufficient"""
        missing = []
        
        recipe_items = self.recipe_items.all()
        if recipe_items.exists():
            for recipe_item in recipe_items:
                required = recipe_item.quantity_required
                current = recipe_item.inventory_item.quantity
                if current < required:
                    missing.append({
                        'name': recipe_item.inventory_item.name,
                        'unit': recipe_item.inventory_item.unit,
                        'required': required,
                        'current': current,
                        'shortage': required - current,
                    })
            return missing
        
        # Fallback to legacy recipe
        if hasattr(self, 'recipe') and self.recipe.ingredients.exists():
            for ing in self.recipe.ingredients.all():
                if not ing.inventory_item:
                    continue
                required = ing.quantity
                current = ing.inventory_item.quantity
                if current < required:
                    missing.append({
                        'name': ing.inventory_item.name,
                        'unit': ing.inventory_item.unit,
                        'required': required,
                        'current': current,
                        'shortage': required - current,
                    })
        
        return missing
    
    def can_fulfill_order(self, quantity=1):
        """Check if we can fulfill order for given quantity"""
        recipe_items = self.recipe_items.all()
        if recipe_items.exists():
            for recipe_item in recipe_items:
                required = recipe_item.quantity_required * quantity
                if recipe_item.inventory_item.quantity < required:
                    return False, f"Insufficient {recipe_item.inventory_item.name}"
            return True, "Available"

        # Fallback to legacy recipe
        if hasattr(self, 'recipe') and self.recipe.ingredients.exists():
            for ing in self.recipe.ingredients.all():
                if not ing.inventory_item:
                    continue
                required = ing.quantity * quantity
                if ing.inventory_item.quantity < required:
                    return False, f"Insufficient {ing.inventory_item.name}"
            return True, "Available"

        return True, "Available"
    
    def deduct_inventory(self, quantity=1):
        """Deduct required ingredients from inventory after order
        
        ATOMIC OPERATION: Either ALL ingredients are deducted or NONE are.
        Ensures inventory never goes negative.
        Raises ValueError if any ingredient is insufficient.
        """
        from django.db import transaction
        
        try:
            with transaction.atomic():
                # Lock the recipe items to prevent concurrent modifications
                recipe_items = list(self.recipe_items.select_related('inventory_item').all())
                
                if recipe_items:
                    # Lock inventory items first strictly before doing anything
                    inventory_ids = [item.inventory_item_id for item in recipe_items]
                    locked_inventories = {
                        inv.id: inv 
                        for inv in InventoryItem.objects.select_for_update().filter(id__in=inventory_ids)
                    }
                    
                    # FIRST: Validate that ALL ingredients are available
                    # This prevents partial deductions
                    for recipe_item in recipe_items:
                        required = recipe_item.quantity_required * quantity
                        inventory = locked_inventories.get(recipe_item.inventory_item_id)
                        if inventory.quantity < required:
                            raise ValueError(
                                f"Insufficient {inventory.name}: "
                                f"Need {required} {inventory.unit}, "
                                f"Have {inventory.quantity}"
                            )
                    
                    # SECOND: All validations passed, now deduct
                    for recipe_item in recipe_items:
                        inventory = locked_inventories.get(recipe_item.inventory_item_id)
                        required = recipe_item.quantity_required * quantity
                        
                        # Deduct (never goes negative due to validation above)
                        old_qty = inventory.quantity
                        inventory.quantity -= required
                        inventory.save()
                        
                        # Log the deduction
                        InventoryLog.objects.create(
                            inventory_item=inventory,
                            action='Used',
                            quantity_changed=-required,
                            previous_quantity=old_qty,
                            new_quantity=inventory.quantity,
                            notes=f"Used for {self.name} ({quantity}x order)"
                        )
                    return True

                # Fallback to legacy Recipe/RecipeIngredient
                if hasattr(self, 'recipe') and self.recipe.ingredients.exists():
                    legacy_items = list(self.recipe.ingredients.select_related('inventory_item').all())
                    inventory_ids = [ing.inventory_item_id for ing in legacy_items if ing.inventory_item_id]
                    
                    locked_inventories = {
                        inv.id: inv 
                        for inv in InventoryItem.objects.select_for_update().filter(id__in=inventory_ids)
                    }
                    
                    # Validate first
                    for ing in legacy_items:
                        if not ing.inventory_item_id:
                            continue
                        inventory = locked_inventories.get(ing.inventory_item_id)
                        required = ing.quantity * quantity
                        if inventory.quantity < required:
                            raise ValueError(
                                f"Insufficient {inventory.name}: "
                                f"Need {required}, Have {inventory.quantity}"
                            )
                    
                    # All valid, now deduct
                    for ing in legacy_items:
                        if not ing.inventory_item_id:
                            continue
                            
                        inventory = locked_inventories.get(ing.inventory_item_id)
                        required = ing.quantity * quantity
                        
                        old_qty = inventory.quantity
                        inventory.quantity -= required
                        inventory.save()
                        
                        InventoryLog.objects.create(
                            inventory_item=inventory,
                            action='Used',
                            quantity_changed=-required,
                            previous_quantity=old_qty,
                            new_quantity=inventory.quantity,
                            notes=f"Used for {self.name} ({quantity}x order)"
                        )
                    return True

                return True
        except Exception as e:
            # Re-raise so order transaction can be rolled back
            raise
    
    class Meta:
        ordering = ['-created_at']


class MenuItemRecipe(models.Model):
    """Recipe/BOM (Bill of Materials) linking MenuItems to their required ingredients"""
    menu_item = models.OneToOneField(MenuItem, on_delete=models.CASCADE, related_name='recipe_bom')
    
    def __str__(self):
        return f"Recipe for {self.menu_item.name}"
    
    class Meta:
        verbose_name = "Menu Item Recipe"
        verbose_name_plural = "Menu Item Recipes"


class MenuItemIngredient(models.Model):
    """Individual ingredients required for a menu item"""
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name='recipe_items')
    inventory_item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='used_in_menus')
    quantity_required = models.FloatField(validators=[MinValueValidator(0.0)])  # quantity per order (g/ml/pcs)
    
    class Meta:
        unique_together = ('menu_item', 'inventory_item')
        verbose_name = "Menu Item Ingredient"
    
    def __str__(self):
        return f"{self.menu_item.name} requires {self.quantity_required} {self.inventory_item.unit} of {self.inventory_item.name}"
    
    def has_sufficient_stock(self):
        """Check if inventory has enough of this ingredient"""
        return self.inventory_item.quantity >= self.quantity_required


class InventoryLog(models.Model):
    """Audit trail for all inventory changes"""
    ACTION_CHOICES = [
        ('Added', 'Added'),
        ('Used', 'Used - Order'),
        ('Adjusted', 'Manual Adjustment'),
        ('Returned', 'Returned'),
        ('Damaged', 'Damaged/Wasted'),
    ]
    
    inventory_item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    quantity_changed = models.FloatField()  # positive or negative
    previous_quantity = models.FloatField()
    new_quantity = models.FloatField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.inventory_item.name} - {self.action} ({self.quantity_changed})"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Inventory Logs"


class Recipe(models.Model):
    """Recipe ingredients for each menu item - KEPT FOR BACKWARDS COMPATIBILITY"""
    menu_item = models.OneToOneField(MenuItem, on_delete=models.CASCADE, related_name='recipe')
    
    def __str__(self):
        return f"Recipe for {self.menu_item.name}"


class RecipeIngredient(models.Model):
    """Individual ingredients in a recipe - KEPT FOR BACKWARDS COMPATIBILITY"""
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='ingredients')
    inventory_item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, null=True, blank=True, related_name='old_recipe_uses')
    ingredient = models.CharField(max_length=100, null=True, blank=True)  # e.g., 'flour', 'cheese'
    quantity = models.FloatField(validators=[MinValueValidator(0.0)])  # in grams/units
    
    def __str__(self):
        if self.inventory_item:
            return f"{self.inventory_item.name} - {self.quantity}"
        return f"{self.quantity}g of {self.ingredient}"
    
    def has_sufficient_stock(self):
        """Check if inventory has enough of this ingredient"""
        if not self.inventory_item:
            return True
        return self.inventory_item.quantity >= self.quantity


class Table(models.Model):
    """Restaurant tables"""
    STATUS_CHOICES = [
        ('Available', 'Available'),
        ('Occupied', 'Occupied'),
        ('Reserved', 'Reserved'),
    ]
    
    table_number = models.PositiveIntegerField(unique=True)
    capacity = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Available')
    
    def __str__(self):
        return f"Table {self.table_number} (Capacity: {self.capacity})"


class Order(models.Model):
    """Customer orders"""
    ORDER_TYPE_CHOICES = [
        ('Dine-in', 'Dine-in'),
        ('Delivery', 'Delivery'),
        ('Pickup', 'Pickup'),
    ]
    
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Preparing', 'Preparing'),
        ('Ready', 'Ready'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('UPI', 'UPI'),
        ('Card', 'Credit/Debit Card'),
        ('Cash', 'Cash'),
        ('Wallet', 'Digital Wallet'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
        ('Refunded', 'Refunded'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    order_type = models.CharField(max_length=20, choices=ORDER_TYPE_CHOICES, default='Dine-in')
    table = models.ForeignKey(Table, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    
    # Customer details (fallback if no user account or for delivery)
    customer_name = models.CharField(max_length=100, blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)
    customer_address = models.TextField(blank=True)
    
    # Financial details
    total_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    final_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    
    # Payment details
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, blank=True, null=True)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='Pending')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Order #{self.id} - {self.get_status_display()}"
    
    class Meta:
        ordering = ['-created_at']


class OrderItem(models.Model):
    """Items in an order"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    # Customizations
    special_instructions = models.TextField(blank=True, help_text="e.g., No onions, extra cheese")

    def __str__(self):
        return f"{self.quantity}x {self.menu_item.name} for Order #{self.order.id}"
        
    def subtotal(self):
        return self.quantity * self.price

    def save(self, *args, **kwargs):
        # Removed auto-deduction here, it must be explicitly called during order placement
        # to ensure atomic and correct inventory deduction
        super().save(*args, **kwargs)


class Reservation(models.Model):
    """Table reservations"""
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='reservations')
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    date = models.DateField()
    time = models.TimeField()
    guests = models.PositiveIntegerField()
    table = models.ForeignKey(Table, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # New status field
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    confirmed = models.BooleanField(default=False) # Kept for backward compatibility, will deprecate
    
    def __str__(self):
        return f"Reservation for {self.name} on {self.date} at {self.time}"
    
    class Meta:
        ordering = ['-date', '-time']
