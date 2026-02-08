from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone

class InventoryItem(models.Model):
    """Inventory tracking for ingredients - Base ingredient inventory"""
    name = models.CharField(max_length=100, unique=True)
    quantity = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    unit = models.CharField(max_length=50, default='units')  # grams, liters, units, pieces
    reorder_level = models.IntegerField(default=100)  # alert when below this
    reorder_quantity = models.IntegerField(default=500)  # quantity to order when restocking
    price_per_unit = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.quantity} {self.unit}"
    
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
    CATEGORY_CHOICES = [
        ('Asian', 'Asian'),
        ('Mexican', 'Mexican'),
        ('Italian', 'Italian'),
        ('American', 'American'),
        ('Middle Eastern', 'Middle Eastern'),
        ('Indian', 'Indian'),
        ('Desserts', 'Desserts'),
        ('Beverages', 'Beverages'),
    ]
    
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    image = models.URLField(default='https://via.placeholder.com/300x200?text=Menu+Item')
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - ₹{self.price}"
    
    def is_available(self):
        """Check if all required ingredients are in stock"""
        recipe_items = self.recipe_items.all()
        if not recipe_items.exists():
            return True
        
        for recipe_item in recipe_items:
            if recipe_item.inventory_item.quantity < recipe_item.quantity_required:
                return False
        return True
    
    def can_fulfill_order(self, quantity=1):
        """Check if we can fulfill order for given quantity"""
        recipe_items = self.recipe_items.all()
        if not recipe_items.exists():
            return True, "Available"
        
        for recipe_item in recipe_items:
            required = recipe_item.quantity_required * quantity
            if recipe_item.inventory_item.quantity < required:
                return False, f"Insufficient {recipe_item.inventory_item.name}"
        
        return True, "Available"
    
    def deduct_inventory(self, quantity=1):
        """Deduct required ingredients from inventory after order"""
        recipe_items = self.recipe_items.all()
        if not recipe_items.exists():
            return True
        
        try:
            for recipe_item in recipe_items:
                inventory = recipe_item.inventory_item
                required = recipe_item.quantity_required * quantity
                if inventory.quantity >= required:
                    old_qty = inventory.quantity
                    inventory.quantity -= required
                    inventory.save()
                    # Log the change
                    InventoryLog.objects.create(
                        inventory_item=inventory,
                        action='Used',
                        quantity_changed=-required,
                        previous_quantity=old_qty,
                        new_quantity=inventory.quantity,
                        notes=f"Used for {self.name} order"
                    )
                else:
                    return False
            return True
        except Exception as e:
            print(f"Error deducting inventory: {e}")
            return False
    
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
    quantity_required = models.IntegerField(validators=[MinValueValidator(1)])  # quantity per order
    
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
    quantity_changed = models.IntegerField()  # positive or negative
    previous_quantity = models.IntegerField()
    new_quantity = models.IntegerField()
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
    quantity = models.IntegerField(validators=[MinValueValidator(1)])  # in grams/units
    
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
        ('In Kitchen', 'In Kitchen'),
        ('Preparing', 'Preparing'),
        ('Ready', 'Ready'),
        ('Delivered Pending', 'Delivered Pending'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]
    
    PAYMENT_CHOICES = [
        ('Card', 'Credit/Debit Card'),
        ('UPI', 'UPI / Wallet'),
        ('Cash', 'Cash'),
    ]
    
    order_id = models.AutoField(primary_key=True)
    order_type = models.CharField(max_length=20, choices=ORDER_TYPE_CHOICES)
    table = models.ForeignKey(Table, on_delete=models.SET_NULL, null=True, blank=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='Card')
    total = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Order #{self.order_id} - {self.get_status_display()}"
    
    class Meta:
        ordering = ['-created_at']


class OrderItem(models.Model):
    """Items in an order"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    
    def __str__(self):
        return f"{self.quantity}x {self.menu_item.name}"
    
    def subtotal(self):
        return self.quantity * self.price


class Reservation(models.Model):
    """Table reservations"""
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    date = models.DateField()
    time = models.TimeField()
    guests = models.PositiveIntegerField(validators=[MinValueValidator(1), ])
    table = models.ForeignKey(Table, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Reservation for {self.name} on {self.date} at {self.time}"
    
    class Meta:
        ordering = ['-date', '-time']
