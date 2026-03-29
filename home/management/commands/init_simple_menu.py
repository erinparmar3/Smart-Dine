from django.core.management.base import BaseCommand
from django.db import transaction

from home.models import Category, InventoryItem, MenuItem, MenuItemIngredient


class Command(BaseCommand):
    help = "Initialize a simplified menu (20–25 items) with minimal inventory and clean mappings"

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Resetting simple menu and inventory..."))

        # Wipe existing menu + recipe mapping + inventory for a clean simple setup
        MenuItemIngredient.objects.all().delete()
        MenuItem.objects.all().delete()
        InventoryItem.objects.all().delete()

        # Core categories
        pizza_cat = Category.objects.get_or_create(name="Pizza", defaults={"description": "Pizzas"})[0]
        burger_cat = Category.objects.get_or_create(name="Burgers", defaults={"description": "Burgers"})[0]
        sandwich_cat = Category.objects.get_or_create(name="Sandwiches", defaults={"description": "Sandwiches"})[0]
        snacks_cat = Category.objects.get_or_create(name="Basic Snacks", defaults={"description": "Snacks"})[0]
        beverages_cat = Category.objects.get_or_create(name="Beverages", defaults={"description": "Beverages"})[0]

        # Minimal ingredient set strictly for ~20–25 demo items
        ingredients_def = {
            # Common pizza base
            "Pizza Base": {"unit": "pcs", "qty": 100},
            "Pizza Sauce": {"unit": "g", "qty": 8000},
            "Mozzarella": {"unit": "g", "qty": 8000},
            "Veg Toppings Mix": {"unit": "g", "qty": 5000},
            "Paneer Cubes": {"unit": "g", "qty": 4000},
            "Chicken Tikka": {"unit": "g", "qty": 4000},
            # Burgers
            "Burger Bun": {"unit": "pcs", "qty": 120},
            "Veg Patty": {"unit": "pcs", "qty": 100},
            "Chicken Patty": {"unit": "pcs", "qty": 80},
            "Cheddar Slice": {"unit": "pcs", "qty": 150},
            "Burger Lettuce": {"unit": "g", "qty": 3000},
            "Burger Mayo": {"unit": "g", "qty": 3000},
            # Sandwiches
            "Bread Slice": {"unit": "pcs", "qty": 300},
            "Butter": {"unit": "g", "qty": 3000},
            "Green Chutney": {"unit": "g", "qty": 2000},
            "Sandwich Veg Mix": {"unit": "g", "qty": 4000},
            "Grilled Paneer": {"unit": "g", "qty": 3000},
            # Snacks
            "French Fries": {"unit": "g", "qty": 5000},
            "Nachos": {"unit": "g", "qty": 3000},
            "Cheese Sauce": {"unit": "g", "qty": 2000},
            "Ketchup": {"unit": "g", "qty": 3000},
            # Beverages
            "Cola Syrup": {"unit": "ml", "qty": 5000},
            "Lemon Syrup": {"unit": "ml", "qty": 3000},
            "Soda Water": {"unit": "ml", "qty": 10000},
            "Milk": {"unit": "ml", "qty": 8000},
            "Coffee Powder": {"unit": "g", "qty": 1000},
        }

        inventory = {}
        for name, cfg in ingredients_def.items():
            inv = InventoryItem.objects.create(
                name=name,
                quantity=cfg["qty"],
                unit=cfg["unit"],
                reorder_level=cfg["qty"] * 0.2,
                reorder_quantity=cfg["qty"],
                price_per_unit=0,
            )
            inventory[name] = inv

        # Create ~20–25 core menu items
        items_def = [
            # Pizzas
            {
                "name": "Margherita Pizza",
                "price": 249,
                "category": pizza_cat,
                "description": "Classic cheese pizza with tomato sauce and mozzarella.",
                "recipe": {
                    "Pizza Base": 1,
                    "Pizza Sauce": 60,
                    "Mozzarella": 80,
                },
            },
            {
                "name": "Veggie Delight Pizza",
                "price": 269,
                "category": pizza_cat,
                "description": "Loaded with mixed veggies and mozzarella.",
                "recipe": {
                    "Pizza Base": 1,
                    "Pizza Sauce": 60,
                    "Mozzarella": 70,
                    "Veg Toppings Mix": 60,
                },
            },
            {
                "name": "Paneer Tikka Pizza",
                "price": 289,
                "category": pizza_cat,
                "description": "Spiced paneer tikka on a cheesy base.",
                "recipe": {
                    "Pizza Base": 1,
                    "Pizza Sauce": 60,
                    "Mozzarella": 70,
                    "Paneer Cubes": 70,
                },
            },
            {
                "name": "Chicken Tikka Pizza",
                "price": 299,
                "category": pizza_cat,
                "description": "Grilled chicken tikka with cheese.",
                "recipe": {
                    "Pizza Base": 1,
                    "Pizza Sauce": 60,
                    "Mozzarella": 70,
                    "Chicken Tikka": 70,
                },
            },
            # Burgers
            {
                "name": "Classic Veg Burger",
                "price": 149,
                "category": burger_cat,
                "description": "Crispy veg patty with lettuce and mayo.",
                "recipe": {
                    "Burger Bun": 1,
                    "Veg Patty": 1,
                    "Cheddar Slice": 1,
                    "Burger Lettuce": 15,
                    "Burger Mayo": 15,
                },
            },
            {
                "name": "Cheese Veg Burger",
                "price": 169,
                "category": burger_cat,
                "description": "Veg burger with extra cheese slice.",
                "recipe": {
                    "Burger Bun": 1,
                    "Veg Patty": 1,
                    "Cheddar Slice": 2,
                    "Burger Lettuce": 15,
                    "Burger Mayo": 15,
                },
            },
            {
                "name": "Classic Chicken Burger",
                "price": 189,
                "category": burger_cat,
                "description": "Fried chicken patty with lettuce and mayo.",
                "recipe": {
                    "Burger Bun": 1,
                    "Chicken Patty": 1,
                    "Cheddar Slice": 1,
                    "Burger Lettuce": 15,
                    "Burger Mayo": 15,
                },
            },
            {
                "name": "Double Patty Burger",
                "price": 219,
                "category": burger_cat,
                "description": "Two veg patties stacked with cheese.",
                "recipe": {
                    "Burger Bun": 1,
                    "Veg Patty": 2,
                    "Cheddar Slice": 2,
                    "Burger Lettuce": 20,
                    "Burger Mayo": 20,
                },
            },
            # Sandwiches
            {
                "name": "Veg Grilled Sandwich",
                "price": 129,
                "category": sandwich_cat,
                "description": "Grilled veg sandwich with chutney.",
                "recipe": {
                    "Bread Slice": 2,
                    "Butter": 10,
                    "Green Chutney": 15,
                    "Sandwich Veg Mix": 50,
                },
            },
            {
                "name": "Paneer Grilled Sandwich",
                "price": 149,
                "category": sandwich_cat,
                "description": "Grilled paneer filling with veggies.",
                "recipe": {
                    "Bread Slice": 2,
                    "Butter": 10,
                    "Green Chutney": 15,
                    "Grilled Paneer": 50,
                },
            },
            {
                "name": "Cheese Toast Sandwich",
                "price": 139,
                "category": sandwich_cat,
                "description": "Simple cheese toasted sandwich.",
                "recipe": {
                    "Bread Slice": 2,
                    "Butter": 10,
                    "Mozzarella": 40,
                },
            },
            # Snacks
            {
                "name": "French Fries",
                "price": 99,
                "category": snacks_cat,
                "description": "Crispy salted fries.",
                "recipe": {
                    "French Fries": 80,
                    "Ketchup": 15,
                },
            },
            {
                "name": "Cheese Fries",
                "price": 129,
                "category": snacks_cat,
                "description": "Fries topped with cheese sauce.",
                "recipe": {
                    "French Fries": 80,
                    "Cheese Sauce": 30,
                },
            },
            {
                "name": "Loaded Nachos",
                "price": 149,
                "category": snacks_cat,
                "description": "Nachos with cheese sauce and ketchup.",
                "recipe": {
                    "Nachos": 60,
                    "Cheese Sauce": 30,
                    "Ketchup": 10,
                },
            },
            # Beverages
            {
                "name": "Cola",
                "price": 69,
                "category": beverages_cat,
                "description": "Chilled cola over ice.",
                "recipe": {
                    "Cola Syrup": 30,
                    "Soda Water": 200,
                },
            },
            {
                "name": "Lemon Soda",
                "price": 69,
                "category": beverages_cat,
                "description": "Sparkling lemon flavored soda.",
                "recipe": {
                    "Lemon Syrup": 25,
                    "Soda Water": 200,
                },
            },
            {
                "name": "Cold Coffee",
                "price": 119,
                "category": beverages_cat,
                "description": "Iced coffee with milk.",
                "recipe": {
                    "Milk": 200,
                    "Coffee Powder": 10,
                },
            },
        ]

        for item_cfg in items_def:
            mi = MenuItem.objects.create(
                name=item_cfg["name"],
                description=item_cfg["description"],
                price=item_cfg["price"],
                category=item_cfg["category"],
                is_active=True,
            )
            for ing_name, qty in item_cfg["recipe"].items():
                MenuItemIngredient.objects.create(
                    menu_item=mi,
                    inventory_item=inventory[ing_name],
                    quantity_required=qty,
                )

        self.stdout.write(self.style.SUCCESS("Simple menu initialized with ~20–25 items and minimal inventory."))

