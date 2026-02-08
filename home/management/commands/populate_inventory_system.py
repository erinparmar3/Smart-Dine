"""
Management command to populate the database with 40 menu items,
their recipes (Bill of Materials), and real-time inventory.

This script creates:
- InventoryItems: All base ingredients needed
- MenuItems: 40 food items across 8 categories
- MenuItemIngredient: Links each menu item to required ingredients with quantities
"""

from django.core.management.base import BaseCommand
from decimal import Decimal
from home.models import (
    MenuItem, InventoryItem, MenuItemIngredient, InventoryLog
)


class Command(BaseCommand):
    help = 'Populate database with 40 menu items and real-time inventory management'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Starting database population...'))
        
        # Step 1: Create inventory items (base ingredients)
        self.stdout.write(self.style.SUCCESS('📦 Creating inventory items...'))
        inventory = self.create_inventory()
        
        # Step 2: Create menu items with recipes
        self.stdout.write(self.style.SUCCESS('🍽️  Creating menu items with recipes...'))
        self.create_menu_items(inventory)
        
        self.stdout.write(self.style.SUCCESS('✅ Database population completed successfully!'))

    def create_inventory(self):
        """Create inventory items for all ingredients"""
        inventory_items = {
            # Beverages
            'Sparkling Water': (2000, 'ml', 100),
            'Coffee Beans': (5000, 'grams', 500),
            'Tea Leaves': (2000, 'grams', 300),
            'Lemon': (500, 'pieces', 50),
            'Cola Syrup': (3000, 'ml', 300),
            'Milk': (10000, 'ml', 1000),
            'Ice': (20000, 'grams', 2000),
            
            # Desserts
            'All Purpose Flour': (15000, 'grams', 2000),
            'Butter': (5000, 'grams', 500),
            'Sugar': (10000, 'grams', 1000),
            'Eggs': (1000, 'pieces', 100),
            'Cocoa Powder': (2000, 'grams', 300),
            'Cream Cheese': (3000, 'grams', 300),
            'Mascarpone': (2000, 'grams', 200),
            'Saffron': (20, 'grams', 5),
            'Milk Powder': (2000, 'grams', 200),
            
            # Indian
            'Chicken Breast': (10000, 'grams', 1000),
            'Basmati Rice': (10000, 'grams', 1000),
            'Paneer': (3000, 'grams', 300),
            'Yogurt': (5000, 'grams', 500),
            'Onion': (5000, 'grams', 500),
            'Garlic': (1000, 'grams', 100),
            'Ginger': (1000, 'grams', 100),
            'Tomato': (3000, 'grams', 300),
            'Lentils': (3000, 'grams', 300),
            'Coriander': (500, 'grams', 50),
            'Cumin': (500, 'grams', 50),
            'Turmeric': (300, 'grams', 30),
            'Chili Powder': (500, 'grams', 50),
            
            # Middle Eastern
            'Chickpeas': (3000, 'grams', 300),
            'Tahini': (2000, 'grams', 200),
            'Pita Bread': (100, 'pieces', 10),
            'Falafel Mix': (2000, 'grams', 200),
            'Lamb': (5000, 'grams', 500),
            'Hummus': (2000, 'grams', 200),
            
            # American
            'Ground Beef': (8000, 'grams', 800),
            'Beef Patty': (100, 'pieces', 10),
            'Potatoes': (8000, 'grams', 800),
            'Bread Buns': (100, 'pieces', 10),
            'Ketchup': (2000, 'ml', 200),
            'Mustard': (1000, 'ml', 100),
            'Lettuce': (2000, 'grams', 200),
            'Cheese Slice': (250, 'pieces', 25),
            'Salad Oil': (5000, 'ml', 500),
            
            # Italian
            'Pasta': (5000, 'grams', 500),
            'Mozzarella': (3000, 'grams', 300),
            'Parmesan': (2000, 'grams', 200),
            'Tomato Sauce': (5000, 'ml', 500),
            'Fresh Basil': (500, 'grams', 50),
            'Olive Oil': (3000, 'ml', 300),
            'Arborio Rice': (3000, 'grams', 300),
            'Beef Stock': (5000, 'ml', 500),
            
            # Mexican
            'Corn Tortillas': (150, 'pieces', 15),
            'Flour Tortillas': (150, 'pieces', 15),
            'Beef BBQ': (3000, 'grams', 300),
            'Salsa': (2000, 'ml', 200),
            'Cheddar Cheese': (2000, 'grams', 200),
            'Bell Pepper': (2000, 'grams', 200),
            'Cilantro': (500, 'grams', 50),
            'Lime': (300, 'pieces', 30),
            
            # Asian
            'Nori Seaweed': (200, 'pieces', 20),
            'Sushi Rice': (3000, 'grams', 300),
            'Wasabi': (500, 'grams', 50),
            'Salmon': (3000, 'grams', 300),
            'Tuna': (2000, 'grams', 200),
            'Ramen Noodles': (2000, 'grams', 200),
            'Pad Thai Sauce': (2000, 'ml', 200),
            'Shrimp': (2000, 'grams', 200),
            'Soy Sauce': (3000, 'ml', 300),
        }
        
        inventory_map = {}
        for name, (qty, unit, reorder) in inventory_items.items():
            item, created = InventoryItem.objects.update_or_create(
                name=name,
                defaults={
                    'quantity': qty,
                    'unit': unit,
                    'reorder_level': reorder,
                    'reorder_quantity': qty,
                    'price_per_unit': Decimal('10.00'),
                }
            )
            inventory_map[name] = item
            status = '✓ Created' if created else '~ Updated'
            self.stdout.write(f'  {status}: {name} ({qty} {unit})')
        
        return inventory_map

    def create_menu_items(self, inventory):
        """Create 40 menu items with their recipes and inventory requirements"""
        
        menu_data = [
            # BEVERAGES
            {'name': 'Milkshake', 'category': 'Beverages', 'price': 120, 'description': 'Creamy milkshake',
             'recipe': {'Milk': 300, 'Ice': 200, 'Sugar': 50}},
            {'name': 'Coffee', 'category': 'Beverages', 'price': 80, 'description': 'Freshly brewed coffee',
             'recipe': {'Coffee Beans': 20, 'Water': 300}},
            {'name': 'Iced Tea', 'category': 'Beverages', 'price': 90, 'description': 'Chilled iced tea',
             'recipe': {'Tea Leaves': 10, 'Ice': 200, 'Lemon': 0.5}},
            {'name': 'Lemonade', 'category': 'Beverages', 'price': 100, 'description': 'Fresh lemonade',
             'recipe': {'Lemon': 2, 'Sugar': 50, 'Water': 300}},
            {'name': 'Coca Cola', 'category': 'Beverages', 'price': 50, 'description': 'Cold cola',
             'recipe': {'Cola Syrup': 100, 'Ice': 150, 'Water': 250}},
            
            # DESSERTS
            {'name': 'Cheesecake', 'category': 'Desserts', 'price': 180, 'description': 'New York cheesecake',
             'recipe': {'Cream Cheese': 200, 'Sugar': 100, 'Eggs': 2, 'Butter': 100}},
            {'name': 'Brownie', 'category': 'Desserts', 'price': 120, 'description': 'Chocolate brownie',
             'recipe': {'Cocoa Powder': 50, 'All Purpose Flour': 150, 'Eggs': 2, 'Sugar': 100, 'Butter': 100}},
            {'name': 'Ice Cream', 'category': 'Desserts', 'price': 100, 'description': 'Ice cream scoop',
             'recipe': {'Milk Powder': 100, 'Sugar': 50, 'Ice': 200}},
            {'name': 'Gulab Jamun', 'category': 'Desserts', 'price': 140, 'description': 'Indian sweet',
             'recipe': {'Milk Powder': 150, 'Sugar': 100, 'Ghee': 50}},
            {'name': 'Tiramisu', 'category': 'Desserts', 'price': 160, 'description': 'Italian layered dessert',
             'recipe': {'Mascarpone': 200, 'Eggs': 2, 'Coffee Beans': 20, 'Sugar': 80, 'Cocoa Powder': 30}},
            
            # INDIAN
            {'name': 'Butter Chicken', 'category': 'Indian', 'price': 280, 'description': 'Creamy butter chicken',
             'recipe': {'Chicken Breast': 200, 'Butter': 50, 'Tomato Sauce': 100, 'Onion': 50, 'Garlic': 10, 'Ginger': 10}},
            {'name': 'Chicken Biryani', 'category': 'Indian', 'price': 250, 'description': 'Fragrant rice dish',
             'recipe': {'Chicken Breast': 200, 'Basmati Rice': 150, 'Onion': 50, 'Saffron': 0.5, 'Yogurt': 50}},
            {'name': 'Paneer Tikka', 'category': 'Indian', 'price': 220, 'description': 'Grilled paneer',
             'recipe': {'Paneer': 200, 'Yogurt': 50, 'Onion': 30, 'Tomato': 30, 'Coriander': 10}},
            {'name': 'Garlic Naan', 'category': 'Indian', 'price': 80, 'description': 'Garlic bread',
             'recipe': {'All Purpose Flour': 200, 'Garlic': 20, 'Butter': 30, 'Yogurt': 30}},
            {'name': 'Samosa', 'category': 'Indian', 'price': 60, 'description': 'Fried pastry',
             'recipe': {'All Purpose Flour': 100, 'Potatoes': 100, 'Onion': 30, 'Cumin': 5}},
            
            # MIDDLE EASTERN
            {'name': 'Shawarma', 'category': 'Middle Eastern', 'price': 220, 'description': 'Spiced meat wrap',
             'recipe': {'Lamb': 200, 'Pita Bread': 1, 'Tomato': 50, 'Onion': 50, 'Tahini': 30}},
            {'name': 'Falafel', 'category': 'Middle Eastern', 'price': 140, 'description': 'Chickpea fritters',
             'recipe': {'Chickpeas': 200, 'Falafel Mix': 50, 'Onion': 30, 'Garlic': 10, 'Coriander': 5}},
            {'name': 'Hummus', 'category': 'Middle Eastern', 'price': 120, 'description': 'Chickpea dip',
             'recipe': {'Chickpeas': 150, 'Tahini': 50, 'Garlic': 10, 'Lemon': 1, 'Olive Oil': 30}},
            {'name': 'Kebab Skewer', 'category': 'Middle Eastern', 'price': 200, 'description': 'Grilled skewer',
             'recipe': {'Lamb': 200, 'Onion': 50, 'Bell Pepper': 50, 'Tomato': 50}},
            {'name': 'Pita Wrap', 'category': 'Middle Eastern', 'price': 160, 'description': 'Filled wrap',
             'recipe': {'Pita Bread': 1, 'Lamb': 150, 'Hummus': 50, 'Tomato': 50, 'Lettuce': 50}},
            
            # AMERICAN
            {'name': 'Burger Classic', 'category': 'American', 'price': 180, 'description': 'Classic burger',
             'recipe': {'Ground Beef': 200, 'Bread Buns': 1, 'Lettuce': 50, 'Tomato': 50, 'Cheese Slice': 1}},
            {'name': 'French Fries', 'category': 'American', 'price': 80, 'description': 'Crispy fries',
             'recipe': {'Potatoes': 200, 'Salad Oil': 50, 'Salt': 5}},
            {'name': 'Hot Dog', 'category': 'American', 'price': 100, 'description': 'Hot dog with toppings',
             'recipe': {'Beef Patty': 1, 'Bread Buns': 1, 'Onion': 30, 'Ketchup': 30, 'Mustard': 20}},
            {'name': 'Fried Chicken', 'category': 'American', 'price': 200, 'description': 'Crispy fried chicken',
             'recipe': {'Chicken Breast': 250, 'All Purpose Flour': 100, 'Salad Oil': 100}},
            {'name': 'Steak', 'category': 'American', 'price': 350, 'description': 'Premium steak',
             'recipe': {'Ground Beef': 300, 'Butter': 50, 'Garlic': 20, 'Salt': 5}},
            
            # ITALIAN
            {'name': 'Margherita Pizza', 'category': 'Italian', 'price': 200, 'description': 'Classic pizza',
             'recipe': {'Pizza Base': 1, 'Mozzarella': 150, 'Tomato Sauce': 100, 'Fresh Basil': 20}},
            {'name': 'Pasta Alfredo', 'category': 'Italian', 'price': 220, 'description': 'Creamy pasta',
             'recipe': {'Pasta': 200, 'Butter': 50, 'Cream': 100, 'Parmesan': 50, 'Garlic': 10}},
            {'name': 'Lasagna', 'category': 'Italian', 'price': 240, 'description': 'Layered pasta',
             'recipe': {'Pasta': 250, 'Ground Beef': 200, 'Mozzarella': 150, 'Tomato Sauce': 200}},
            {'name': 'Risotto', 'category': 'Italian', 'price': 260, 'description': 'Creamy rice',
             'recipe': {'Arborio Rice': 200, 'Beef Stock': 300, 'Parmesan': 50, 'Butter': 50, 'Onion': 50}},
            {'name': 'Bruschetta', 'category': 'Italian', 'price': 120, 'description': 'Toasted bread',
             'recipe': {'Bread Buns': 2, 'Tomato': 100, 'Garlic': 10, 'Olive Oil': 20, 'Fresh Basil': 10}},
            
            # MEXICAN
            {'name': 'Tacos al Pastor', 'category': 'Mexican', 'price': 200, 'description': 'Spiced tacos',
             'recipe': {'Corn Tortillas': 3, 'Beef BBQ': 150, 'Onion': 50, 'Cilantro': 20, 'Lime': 1}},
            {'name': 'Burrito', 'category': 'Mexican', 'price': 220, 'description': 'Wrapped burrito',
             'recipe': {'Flour Tortillas': 2, 'Ground Beef': 150, 'Beans': 100, 'Rice': 100, 'Cheddar Cheese': 50}},
            {'name': 'Quesadilla', 'category': 'Mexican', 'price': 180, 'description': 'Cheese quesadilla',
             'recipe': {'Flour Tortillas': 2, 'Cheddar Cheese': 100, 'Salsa': 50, 'Chicken': 100}},
            {'name': 'Nachos Supreme', 'category': 'Mexican', 'price': 200, 'description': 'Loaded nachos',
             'recipe': {'Corn Tortillas': 100, 'Cheddar Cheese': 100, 'Ground Beef': 100, 'Salsa': 50, 'Sour Cream': 50}},
            {'name': 'Enchiladas Roja', 'category': 'Mexican', 'price': 210, 'description': 'Red sauce enchiladas',
             'recipe': {'Corn Tortillas': 3, 'Chicken': 150, 'Salsa': 100, 'Cheese': 100, 'Onion': 30}},
            
            # ASIAN
            {'name': 'Sushi Roll', 'category': 'Asian', 'price': 240, 'description': 'Fresh sushi',
             'recipe': {'Nori Seaweed': 2, 'Sushi Rice': 150, 'Salmon': 100, 'Cucumber': 50, 'Wasabi': 10}},
            {'name': 'Ramen Noodles', 'category': 'Asian', 'price': 200, 'description': 'Hot ramen soup',
             'recipe': {'Ramen Noodles': 150, 'Beef Stock': 300, 'Egg': 1, 'Garlic': 10, 'Ginger': 10}},
            {'name': 'Pad Thai', 'category': 'Asian', 'price': 210, 'description': 'Thai noodles',
             'recipe': {'Ramen Noodles': 150, 'Pad Thai Sauce': 100, 'Shrimp': 100, 'Egg': 1, 'Peanuts': 30}},
            {'name': 'Fried Rice', 'category': 'Asian', 'price': 180, 'description': 'Stir-fried rice',
             'recipe': {'Basmati Rice': 180, 'Egg': 2, 'Shrimp': 80, 'Soy Sauce': 30, 'Onion': 50}},
            {'name': 'Dumplings', 'category': 'Asian', 'price': 140, 'description': 'Steamed dumplings',
             'recipe': {'All Purpose Flour': 150, 'Ground Pork': 100, 'Cabbage': 80, 'Soy Sauce': 20, 'Garlic': 10}},
        ]
        
        created_count = 0
        for item_data in menu_data:
            menu_item, created = MenuItem.objects.update_or_create(
                name=item_data['name'],
                defaults={
                    'category': item_data['category'],
                    'price': Decimal(str(item_data['price'])),
                    'description': item_data['description'],
                    'image': f'https://via.placeholder.com/300x200?text={item_data["name"].replace(" ", "+")}'
                }
            )
            
            if created:
                created_count += 1
            
            # Add recipe ingredients
            for ingredient_name, quantity in item_data['recipe'].items():
                if ingredient_name in inventory:
                    inv_item = inventory[ingredient_name]
                    MenuItemIngredient.objects.update_or_create(
                        menu_item=menu_item,
                        inventory_item=inv_item,
                        defaults={'quantity_required': int(quantity) if quantity >= 1 else 1}
                    )
            
            status = '✓ Created' if created else '~ Updated'
            self.stdout.write(f'  {status}: {item_data["name"]} (₹{item_data["price"]})')
        
        self.stdout.write(self.style.SUCCESS(f'\n📊 Total: {created_count} new items created, {len(menu_data) - created_count} updated'))
