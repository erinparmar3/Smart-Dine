from django.core.management.base import BaseCommand
from home.models import MenuItem

class Command(BaseCommand):
    help = 'Populate the database with menu items for all categories'

    MENU_DATA = {
        'Asian': [
            {
                'name': 'Sushi Roll',
                'price': 349,
                'description': 'Fresh assorted sushi with wasabi and ginger',
                'image': 'https://images.unsplash.com/photo-1553621042-f6e147245754?auto=format&fit=crop&w=500&q=60'
            },
            {
                'name': 'Ramen Noodles',
                'price': 299,
                'description': 'Authentic Japanese ramen with broth and toppings',
                'image': 'https://images.unsplash.com/photo-1555939594-58d7cb561ad1?auto=format&fit=crop&w=500&q=60'
            },
            {
                'name': 'Pad Thai',
                'price': 279,
                'description': 'Stir-fried rice noodles with seafood',
                'image': 'https://images.unsplash.com/photo-1559314117-d587253b6ffd?auto=format&fit=crop&w=500&q=60'
            },
            {
                'name': 'Fried Rice',
                'price': 249,
                'description': 'Fragrant fried rice with egg and vegetables',
                'image': 'https://images.unsplash.com/photo-1585238341710-4ebb77b25b3e?auto=format&fit=crop&w=500&q=60'
            },
            {
                'name': 'Dumplings',
                'price': 199,
                'description': 'Steamed or fried dumplings served with sauce',
                'image': 'https://images.unsplash.com/photo-1563380521-c30fb13d1b63?auto=format&fit=crop&w=500&q=60'
            },
        ],
        'Mexican': [
            {
                'name': 'Tacos al Pastor',
                'price': 259,
                'description': 'Spiced pork tacos with fresh cilantro',
                'image': 'https://images.unsplash.com/photo-1565299585323-38d6b0865b47?auto=format&fit=crop&w=500&q=60'
            },
            {
                'name': 'Burrito',
                'price': 289,
                'description': 'Large flour tortilla filled with meat and beans',
                'image': 'https://images.unsplash.com/photo-1626082927389-6cd097cfd330?auto=format&fit=crop&w=500&q=60'
            },
            {
                'name': 'Quesadilla',
                'price': 219,
                'description': 'Grilled tortilla with cheese and filling',
                'image': 'https://images.unsplash.com/photo-1618353325635-6e36d6b09169?auto=format&fit=crop&w=500&q=60'
            },
            {
                'name': 'Nachos Supreme',
                'price': 249,
                'description': 'Loaded nachos with meat, cheese, and toppings',
                'image': 'https://images.unsplash.com/photo-1599974579688-403ce63ad8de?auto=format&fit=crop&w=500&q=60'
            },
            {
                'name': 'Enchiladas Roja',
                'price': 279,
                'description': 'Rolled tortillas in red sauce with cheese',
                'image': 'https://images.unsplash.com/photo-1585853885329-3a50b3c2c18d?auto=format&fit=crop&w=500&q=60'
            },
        ],
        'Italian': [
            {
                'name': 'Margherita Pizza',
                'price': 349,
                'description': 'Classic pizza with tomato, mozzarella, and basil',
                'image': 'https://images.unsplash.com/photo-1574071318508-1cdbab80d002?auto=format&fit=crop&w=500&q=60'
            },
            {
                'name': 'Pasta Alfredo',
                'price': 299,
                'description': 'Creamy pasta with parmesan and butter',
                'image': 'https://images.unsplash.com/photo-1612874742237-6526221fcf0f?auto=format&fit=crop&w=500&q=60'
            },
            {
                'name': 'Lasagna',
                'price': 329,
                'description': 'Layered pasta with meat sauce and cheese',
                'image': 'https://images.unsplash.com/photo-1599927945589-cb35c4c4b1f0?auto=format&fit=crop&w=500&q=60'
            },
            {
                'name': 'Risotto',
                'price': 319,
                'description': 'Creamy arborio rice with mushrooms',
                'image': 'https://images.unsplash.com/photo-1599143211856-90cea8d78686?auto=format&fit=crop&w=500&q=60'
            },
            {
                'name': 'Bruschetta',
                'price': 189,
                'description': 'Toasted bread with tomato and garlic',
                'image': 'https://images.unsplash.com/photo-1527995412171-829470bda30e?auto=format&fit=crop&w=500&q=60'
            },
        ],
        'American': [
            {
                'name': 'Burger Classic',
                'price': 249,
                'description': 'Juicy burger with lettuce, tomato, and special sauce',
                'image': 'https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=500&q=60'
            },
            {
                'name': 'French Fries',
                'price': 119,
                'description': 'Crispy golden fries with dipping sauce',
                'image': 'https://images.unsplash.com/photo-1585238341710-4ebb77b25b3e?auto=format&fit=crop&w=500&q=60'
            },
            {
                'name': 'Hot Dog',
                'price': 149,
                'description': 'Grilled sausage with mustard and onions',
                'image': 'https://images.unsplash.com/photo-1585618267510-870e404e996d?auto=format&fit=crop&w=500&q=60'
            },
            {
                'name': 'Fried Chicken',
                'price': 279,
                'description': 'Crispy fried chicken with coleslaw',
                'image': 'https://images.unsplash.com/photo-1626082927389-6cd097cfd330?auto=format&fit=crop&w=500&q=60'
            },
            {
                'name': 'Steak',
                'price': 449,
                'description': 'Premium grilled steak with mashed potatoes',
                'image': 'https://images.unsplash.com/photo-1599708704244-8d4bef0f2e27?auto=format&fit=crop&w=500&q=60'
            },
        ],
        'Middle Eastern': [
            {
                'name': 'Shawarma',
                'price': 239,
                'description': 'Marinated meat wrapped in pita bread',
                'image': 'https://images.unsplash.com/photo-1529692236b674f346af280520bec78caff92f38?auto=format&fit=crop&w=500&q=60'
            },
            {
                'name': 'Falafel',
                'price': 179,
                'description': 'Crispy chickpea fritters with tahini sauce',
                'image': 'https://images.unsplash.com/photo-1585238341710-4ebb77b25b3e?auto=format&fit=crop&w=500&q=60'
            },
            {
                'name': 'Hummus',
                'price': 99,
                'description': 'Creamy chickpea dip with olive oil and pita',
                'image': 'https://images.unsplash.com/photo-1585238341710-4ebb77b25b3e?auto=format&fit=crop&w=500&q=60'
            },
            {
                'name': 'Kebab Skewer',
                'price': 269,
                'description': 'Grilled meat skewer with vegetables',
                'image': 'https://images.unsplash.com/photo-1599308090241-d38a26a68376?auto=format&fit=crop&w=500&q=60'
            },
            {
                'name': 'Pita Wrap',
                'price': 199,
                'description': 'Soft pita filled with vegetables and sauce',
                'image': 'https://images.unsplash.com/photo-1585238341710-4ebb77b25b3e?auto=format&fit=crop&w=500&q=60'
            },
        ],
        'Indian': [
            {
                'name': 'Butter Chicken',
                'price': 299,
                'description': 'Creamy tomato-based chicken curry',
                'image': 'https://images.unsplash.com/photo-1565299585323-38d6b0865b47?auto=format&fit=crop&w=500&q=60'
            },
            {
                'name': 'Chicken Biryani',
                'price': 299,
                'description': 'Fragrant basmati rice with spiced chicken',
                'image': 'https://images.unsplash.com/photo-1589302168068-964664d93dc0?auto=format&fit=crop&w=500&q=60'
            },
            {
                'name': 'Paneer Tikka',
                'price': 249,
                'description': 'Grilled cottage cheese with spices',
                'image': 'https://images.unsplash.com/photo-1599308090241-d38a26a68376?auto=format&fit=crop&w=500&q=60'
            },
            {
                'name': 'Garlic Naan',
                'price': 59,
                'description': 'Soft bread with garlic and butter',
                'image': 'https://images.unsplash.com/photo-1541519227354-08fa5d50c44d?auto=format&fit=crop&w=500&q=60'
            },
            {
                'name': 'Samosa',
                'price': 89,
                'description': 'Crispy pastry with spiced potato filling',
                'image': 'https://images.unsplash.com/photo-1599308090241-d38a26a68376?auto=format&fit=crop&w=500&q=60'
            },
        ],
        'Desserts': [
            {
                'name': 'Cheesecake',
                'price': 179,
                'description': 'Rich and creamy cheesecake with berry topping',
                'image': 'https://images.unsplash.com/photo-1571115764595-285f4c3fa001?auto=format&fit=crop&w=500&q=60'
            },
            {
                'name': 'Brownie',
                'price': 129,
                'description': 'Fudgy chocolate brownie',
                'image': 'https://images.unsplash.com/photo-1607623814075-e51df1bdc82f?auto=format&fit=crop&w=500&q=60'
            },
            {
                'name': 'Ice Cream',
                'price': 99,
                'description': 'Creamy ice cream in your choice of flavors',
                'image': 'https://images.unsplash.com/photo-1563805042-7684c019e157?auto=format&fit=crop&w=500&q=60'
            },
            {
                'name': 'Gulab Jamun',
                'price': 119,
                'description': 'Soft milk solids in sweet rose syrup',
                'image': 'https://images.unsplash.com/photo-1585518419759-d8e2e41e85f5?auto=format&fit=crop&w=500&q=60'
            },
            {
                'name': 'Tiramisu',
                'price': 189,
                'description': 'Italian dessert with mascarpone and cocoa',
                'image': 'https://images.unsplash.com/photo-1571115764595-285f4c3fa001?auto=format&fit=crop&w=500&q=60'
            },
        ],
        'Beverages': [
            {
                'name': 'Coca Cola',
                'price': 59,
                'description': 'Refreshing cola drink',
                'image': 'https://images.unsplash.com/photo-1554866585-e1b7a3e78e96?auto=format&fit=crop&w=500&q=60'
            },
            {
                'name': 'Lemonade',
                'price': 79,
                'description': 'Fresh squeezed lemonade',
                'image': 'https://images.unsplash.com/photo-1585518419759-d8e2e41e85f5?auto=format&fit=crop&w=500&q=60'
            },
            {
                'name': 'Iced Tea',
                'price': 69,
                'description': 'Chilled iced tea with lemon',
                'image': 'https://images.unsplash.com/photo-1600788148202-8c70313a0e09?auto=format&fit=crop&w=500&q=60'
            },
            {
                'name': 'Coffee',
                'price': 149,
                'description': 'Hot brewed coffee',
                'image': 'https://images.unsplash.com/photo-1572442388796-11668a67e53d?auto=format&fit=crop&w=500&q=60'
            },
            {
                'name': 'Milkshake',
                'price': 139,
                'description': 'Creamy milkshake in chocolate or vanilla',
                'image': 'https://images.unsplash.com/photo-1577820643272-265f434b0999?auto=format&fit=crop&w=500&q=60'
            },
        ],
    }

    def handle(self, *args, **options):
        # Clear existing items
        count_before = MenuItem.objects.count()
        MenuItem.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'Cleared {count_before} existing items'))

        # Add new items
        created_count = 0
        for category, items in self.MENU_DATA.items():
            for item_data in items:
                MenuItem.objects.create(
                    name=item_data['name'],
                    price=item_data['price'],
                    category=category,
                    image=item_data['image'],
                    description=item_data['description']
                )
                created_count += 1
                self.stdout.write(f"  Created: {item_data['name']} ({category})")

        self.stdout.write(self.style.SUCCESS(f'\nSuccessfully created {created_count} menu items!'))
