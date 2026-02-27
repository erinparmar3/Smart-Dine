from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from django.contrib.messages.storage.fallback import FallbackStorage

from home.models import (
    Category,
    InventoryItem,
    MenuItem,
    MenuItemIngredient,
    Order,
    OrderItem,
)
from home.views import cancel_order_customer


class InventoryFlowTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        # Ingredients
        self.flour = InventoryItem.objects.create(
            name="Flour", quantity=1000, unit="g"
        )
        self.cheese = InventoryItem.objects.create(
            name="Cheese", quantity=500, unit="g"
        )

        category = Category.objects.create(name="Mains")

        # Two menu items that share ingredients
        self.pizza = MenuItem.objects.create(
            name="Pizza", description="", price=200, category=category
        )
        self.pasta = MenuItem.objects.create(
            name="Pasta", description="", price=150, category=category
        )

        # Recipe: Pizza uses more flour and cheese
        MenuItemIngredient.objects.create(
            menu_item=self.pizza, inventory_item=self.flour, quantity_required=200
        )
        MenuItemIngredient.objects.create(
            menu_item=self.pizza, inventory_item=self.cheese, quantity_required=100
        )

        # Recipe: Pasta uses some flour only
        MenuItemIngredient.objects.create(
            menu_item=self.pasta, inventory_item=self.flour, quantity_required=100
        )

    def test_multiple_items_deduct_inventory_correctly(self):
        """
        When ordering multiple quantities of multiple items,
        all ingredient quantities should decrease by the combined requirement.
        """
        # Order 2x Pizza and 3x Pasta
        self.pizza.deduct_inventory(quantity=2)
        self.pasta.deduct_inventory(quantity=3)

        self.flour.refresh_from_db()
        self.cheese.refresh_from_db()

        # Flour usage: Pizza 2 * 200 = 400, Pasta 3 * 100 = 300 -> total 700
        self.assertEqual(self.flour.quantity, 1000 - 700)

        # Cheese usage: Pizza only: 2 * 100 = 200
        self.assertEqual(self.cheese.quantity, 500 - 200)

    def test_cancel_order_restores_inventory(self):
        """
        Cancelling a pending order via customer view should restore inventory.
        """
        user = User.objects.create_user(username="cust", password="pass")

        # Place an order with 1x Pizza and 1x Pasta, manually using model logic
        Order.objects.create(  # first create order to attach items
            user=user,
            order_type="Dine-in",
            total_amount=0,
            tax_amount=0,
            final_amount=0,
        )
        order = Order.objects.first()

        OrderItem.objects.create(
            order=order, menu_item=self.pizza, quantity=1, price=self.pizza.price
        )
        OrderItem.objects.create(
            order=order, menu_item=self.pasta, quantity=1, price=self.pasta.price
        )

        # Deduct inventory as place_order would do
        self.pizza.deduct_inventory(quantity=1)
        self.pasta.deduct_inventory(quantity=1)

        flour_after_deduct = InventoryItem.objects.get(pk=self.flour.pk).quantity
        cheese_after_deduct = InventoryItem.objects.get(pk=self.cheese.pk).quantity

        # Sanity checks that deductions happened
        self.assertLess(flour_after_deduct, 1000)
        self.assertLess(cheese_after_deduct, 500)

        # Now cancel via the view, which uses refill_inventory
        request = self.factory.post("/")
        request.user = user

        # Attach a message storage backend so the view can use messages
        setattr(request, "session", {})
        messages = FallbackStorage(request)
        setattr(request, "_messages", messages)
        response = cancel_order_customer(request, order_id=order.id)

        self.assertEqual(response.status_code, 302)  # redirect back to dashboard

        self.flour.refresh_from_db()
        self.cheese.refresh_from_db()

        # After cancellation, inventory should be back to original amounts
        self.assertEqual(self.flour.quantity, 1000)
        self.assertEqual(self.cheese.quantity, 500)
