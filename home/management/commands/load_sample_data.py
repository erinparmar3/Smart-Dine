from django.core.management.base import BaseCommand
from home.models import MenuItem, Table, InventoryItem, Recipe, RecipeIngredient
from decimal import Decimal


class Command(BaseCommand):
    help = 'Load sample data into the database'

    def handle(self, *args, **options):
        self.stdout.write('Loading sample data...')

        # Create sample menu items
        menu_data = [
            {
                'name': 'Margherita Pizza',
                'price': Decimal('349.00'),
                'category': 'Main',
                'description': 'Classic Margherita pizza with fresh mozzarella and basil',
                'image': 'https://images.unsplash.com/photo-1574071318508-1cdbab80d002?auto=format&fit=crop&w=500&q=60',
            },
            {
                'name': 'Chicken Biryani',
                'price': Decimal('299.00'),
                'category': 'Main',
                'description': 'Fragrant basmati rice with tender chicken and aromatic spices',
                'image': 'https://images.unsplash.com/photo-1589302168068-964664d93dc0?auto=format&fit=crop&w=500&q=60',
            },
            {
                'name': 'Cappuccino',
                'price': Decimal('149.00'),
                'category': 'Beverage',
                'description': 'Smooth and creamy cappuccino made with premium coffee beans',
                'image': 'https://images.unsplash.com/photo-1572442388796-11668a67e53d?auto=format&fit=crop&w=500&q=60',
            },
            {
                'name': 'Caesar Salad',
                'price': Decimal('199.00'),
                'category': 'Starter',
                'description': 'Fresh vegetables with Caesar dressing and croutons',
                'image': 'https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=500&q=60',
            },
            {
                'name': 'Spaghetti Carbonara',
                'price': Decimal('279.00'),
                'category': 'Main',
                'description': 'Classic Italian pasta with creamy sauce and crispy bacon',
                'image': 'https://images.unsplash.com/photo-1612874742237-6526221fcf0f?auto=format&fit=crop&w=500&q=60',
            },
            {
                'name': 'Chocolate Cake',
                'price': Decimal('99.00'),
                'category': 'Dessert',
                'description': 'Rich and moist chocolate cake with chocolate frosting',
                'image': 'https://images.unsplash.com/photo-1578985545062-69928b1d9587?auto=format&fit=crop&w=500&q=60',
            },
        ]

        created_items = []
        for item_data in menu_data:
            item, created = MenuItem.objects.get_or_create(
                name=item_data['name'],
                defaults={
                    'price': item_data['price'],
                    'category': item_data['category'],
                    'description': item_data['description'],
                    'image': item_data['image'],
                }
            )
            if created:
                created_items.append(item.name)
                self.stdout.write(self.style.SUCCESS(f'Created: {item.name}'))

        # Create sample tables
        for i in range(1, 7):
            table, created = Table.objects.get_or_create(
                table_number=i,
                defaults={
                    'capacity': 4 if i <= 4 else 2,
                    'status': 'Available',
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created: Table {i}'))

        # Create sample inventory items
        inventory_data = [
            {'name': 'Flour', 'quantity': 5000, 'unit': 'grams', 'reorder_level': 1000},
            {'name': 'Cheese', 'quantity': 2000, 'unit': 'grams', 'reorder_level': 500},
            {'name': 'Tomato Sauce', 'quantity': 3000, 'unit': 'ml', 'reorder_level': 1000},
            {'name': 'Chicken', 'quantity': 5000, 'unit': 'grams', 'reorder_level': 1000},
            {'name': 'Rice', 'quantity': 10000, 'unit': 'grams', 'reorder_level': 2000},
            {'name': 'Spices', 'quantity': 1000, 'unit': 'grams', 'reorder_level': 200},
            {'name': 'Milk', 'quantity': 5000, 'unit': 'ml', 'reorder_level': 1000},
            {'name': 'Coffee Beans', 'quantity': 1000, 'unit': 'grams', 'reorder_level': 200},
            {'name': 'Vegetables', 'quantity': 4000, 'unit': 'grams', 'reorder_level': 1000},
            {'name': 'Butter', 'quantity': 2000, 'unit': 'grams', 'reorder_level': 500},
            {'name': 'Eggs', 'quantity': 500, 'unit': 'units', 'reorder_level': 100},
            {'name': 'Fresh Herbs', 'quantity': 500, 'unit': 'grams', 'reorder_level': 100},
        ]

        for inv_data in inventory_data:
            inv_item, created = InventoryItem.objects.get_or_create(
                name=inv_data['name'],
                defaults={
                    'quantity': inv_data['quantity'],
                    'unit': inv_data['unit'],
                    'reorder_level': inv_data['reorder_level'],
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created Inventory: {inv_item.name}'))

        self.stdout.write(self.style.SUCCESS('Successfully loaded sample data!'))
        self.stdout.write(f'Created {len(created_items)} menu items, 6 tables, and 12 inventory items.')
