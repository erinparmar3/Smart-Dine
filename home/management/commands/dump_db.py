from django.core.management.base import BaseCommand
from home.models import MenuItem, InventoryItem, MenuItemIngredient, Order

class Command(BaseCommand):
    help = "Dump DB Info"

    def handle(self, *args, **options):
        self.stdout.write("--- MENU ITEMS ---")
        for m in MenuItem.objects.all():
            self.stdout.write(f"- {m.name} (ID: {m.id})")
            for ri in m.recipe_items.all():
                self.stdout.write(f"  Requires: {ri.quantity_required} of {ri.inventory_item.name} (Stock: {ri.inventory_item.quantity})")
                
        self.stdout.write("\n--- RECENT ORDERS ---")
        for order in Order.objects.order_by('-id')[:5]:
            self.stdout.write(f"Order #{order.id} | Status: {order.status} | Total: {order.total_amount}")
            for item in order.items.all():
                self.stdout.write(f"  - {item.quantity}x {item.menu_item.name}")
