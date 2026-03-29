import os
import django
import sys

# Setup Django
sys.path.append(r"a:\DDU\SEM 4\PYTHON\SP Project\Django\smartdine")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartdine.settings')
django.setup()

from home.models import MenuItem, InventoryItem, Category, MenuItemIngredient

# Let's see what happens when we deduct inventory
try:
    print("Testing deduct_inventory...")
    m = MenuItem.objects.first()
    if not m:
        print("No menu items found. Creating...")
        cat, _ = Category.objects.get_or_create(name='Test Category')
        m = MenuItem.objects.create(name='Test Pizza', price=10, category=cat)
        
    inv1, _ = InventoryItem.objects.get_or_create(name='Pizza Base')
    inv2, _ = InventoryItem.objects.get_or_create(name='Cheese')
    inv1.quantity = 100
    inv1.save()
    inv2.quantity = 500
    inv2.save()
    
    mi1, _ = MenuItemIngredient.objects.get_or_create(menu_item=m, inventory_item=inv1, defaults={'quantity_required': 1})
    mi1.quantity_required = 1
    mi1.save()
    
    mi2, _ = MenuItemIngredient.objects.get_or_create(menu_item=m, inventory_item=inv2, defaults={'quantity_required': 50})
    mi2.quantity_required = 50
    mi2.save()
    
    print("Current inventory:")
    print(f"Pizza Base: {inv1.quantity}")
    print(f"Cheese: {inv2.quantity}")
    
    m.deduct_inventory(1)
    
    inv1.refresh_from_db()
    inv2.refresh_from_db()
    print("After deduct_inventory(1):")
    print(f"Pizza Base: {inv1.quantity}")
    print(f"Cheese: {inv2.quantity}")
        
except Exception as e:
    import traceback
    traceback.print_exc()
