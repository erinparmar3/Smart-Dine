from django.db import models
from django.core.validators import MinValueValidator

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
        if not hasattr(self, 'recipe') or not self.recipe:
            return True
        
        for ingredient in self.recipe.ingredients.all():
            if not ingredient.has_sufficient_stock():
                return False
        return True
    
    def can_fulfill_order(self, quantity=1):
        """Check if we can fulfill order for given quantity"""
        if not self.is_available():
            return False, "Item out of stock"
        
        if not hasattr(self, 'recipe') or not self.recipe:
            return True, "Available"
        
        for ingredient in self.recipe.ingredients.all():
            required = ingredient.quantity * quantity
            if ingredient.inventory_item.quantity < required:
                return False, f"Insufficient {ingredient.inventory_item.name}"
        
        return True, "Available"
    
    def deduct_inventory(self, quantity=1):
        """Deduct required ingredients from inventory after order"""
        if not hasattr(self, 'recipe') or not self.recipe:
            return True
        
        try:
            for ingredient in self.recipe.ingredients.all():
                inventory = ingredient.inventory_item
                required = ingredient.quantity * quantity
                if inventory.quantity >= required:
                    inventory.quantity -= required
                    inventory.save()
                else:
                    return False
            return True
        except:
            return False
    
    class Meta:
        ordering = ['-created_at']


class Recipe(models.Model):
    """Recipe ingredients for each menu item"""
    menu_item = models.OneToOneField(MenuItem, on_delete=models.CASCADE, related_name='recipe')
    
    def __str__(self):
        return f"Recipe for {self.menu_item.name}"


class RecipeIngredient(models.Model):
    """Individual ingredients in a recipe (Bill of Materials)"""
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='ingredients')
    inventory_item = models.ForeignKey('InventoryItem', on_delete=models.CASCADE, related_name='used_in_recipes')
    quantity = models.IntegerField(validators=[MinValueValidator(1)])  # required quantity per order
    
    class Meta:
        unique_together = ('recipe', 'inventory_item')
    
    def __str__(self):
        return f"{self.inventory_item.name} - {self.quantity}"
    
    def has_sufficient_stock(self):
        """Check if inventory has enough of this ingredient"""
        return self.inventory_item.quantity >= self.quantity


class InventoryItem(models.Model):
    """Inventory tracking for ingredients"""
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
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='inventory_logs')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.inventory_item.name} - {self.action} ({self.quantity_changed})"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Inventory Logs"
