from django.core.management.base import BaseCommand
from home.models import MenuItem, InventoryItem, Category, MenuItemIngredient, Order, OrderItem
from django.db import transaction

class Command(BaseCommand):
    help = "Test End to End Deduction"

    def handle(self, *args, **options):
        # Setup Test Data
        cat, _ = Category.objects.get_or_create(name='Test Category')
        pizza, _ = MenuItem.objects.get_or_create(name='Test Pizza', price=100, category=cat)
        
        base, _ = InventoryItem.objects.get_or_create(name='Pizza Base', defaults={'unit': 'pcs', 'quantity': 50})
        sauce, _ = InventoryItem.objects.get_or_create(name='Pizza Sauce', defaults={'unit': 'g', 'quantity': 1000})
        cheese, _ = InventoryItem.objects.get_or_create(name='Cheese', defaults={'unit': 'g', 'quantity': 500})
        
        base.quantity = 50
        base.save()
        sauce.quantity = 1000
        sauce.save()
        cheese.quantity = 500
        cheese.save()
        
        MenuItemIngredient.objects.get_or_create(menu_item=pizza, inventory_item=base, defaults={'quantity_required': 1})
        MenuItemIngredient.objects.get_or_create(menu_item=pizza, inventory_item=sauce, defaults={'quantity_required': 20})
        MenuItemIngredient.objects.get_or_create(menu_item=pizza, inventory_item=cheese, defaults={'quantity_required': 2})
        
        # Make sure they are updated
        mi_base = MenuItemIngredient.objects.get(menu_item=pizza, inventory_item=base)
        mi_base.quantity_required = 1
        mi_base.save()
        mi_sauce = MenuItemIngredient.objects.get(menu_item=pizza, inventory_item=sauce)
        mi_sauce.quantity_required = 20
        mi_sauce.save()
        mi_cheese = MenuItemIngredient.objects.get(menu_item=pizza, inventory_item=cheese)
        mi_cheese.quantity_required = 2
        mi_cheese.save()
        
        self.stdout.write("Before Order:")
        self.stdout.write(f"  Base: {base.quantity}")
        self.stdout.write(f"  Sauce: {sauce.quantity}")
        self.stdout.write(f"  Cheese: {cheese.quantity}")
        
        # Simulate place_order logic EXACTLY
        try:
            with transaction.atomic():
                order = Order.objects.create(
                    customer_name="Test User",
                    order_type="Dine-in",
                    total_amount=100,
                    status='Pending'
                )
                
                OrderItem.objects.create(
                    order=order,
                    menu_item=pizza,
                    quantity=1,
                    price=pizza.price
                )
                
                pizza.deduct_inventory(1)
            
            self.stdout.write("Order placed successfully.")
        except Exception as e:
            self.stdout.write(f"Failed: {e}")
            
        base.refresh_from_db()
        sauce.refresh_from_db()
        cheese.refresh_from_db()
        
        self.stdout.write("After Order:")
        self.stdout.write(f"  Base: {base.quantity}")
        self.stdout.write(f"  Sauce: {sauce.quantity}")
        self.stdout.write(f"  Cheese: {cheese.quantity}")
