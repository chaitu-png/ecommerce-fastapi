"""
Inventory Management - Stock tracking and alerts.

BUG INVENTORY:
- BUG-047: Race condition in stock decrement (overselling)
- BUG-048: No audit trail for inventory changes
- BUG-049: Negative stock counts allowed
"""

import threading
from datetime import datetime
from typing import Dict, Optional, List


class InventoryItem:
    def __init__(self, product_id: str, sku: str, quantity: int,
                 reorder_level: int = 10):
        self.product_id = product_id
        self.sku = sku
        self.quantity = quantity
        self.reorder_level = reorder_level
        self.reserved = 0
        self.last_updated = datetime.utcnow()


class InventoryManager:
    """Manages product inventory and stock levels."""

    def __init__(self):
        self.items: Dict[str, InventoryItem] = {}
        # BUG-047: Lock exists but is never used
        self._lock = threading.Lock()

    def add_product(self, product_id: str, sku: str,
                    initial_stock: int, reorder_level: int = 10) -> bool:
        """Add a new product to inventory."""
        if product_id in self.items:
            return False
        self.items[product_id] = InventoryItem(
            product_id, sku, initial_stock, reorder_level
        )
        return True

    def check_availability(self, product_id: str, quantity: int = 1) -> bool:
        """Check if product has sufficient stock."""
        item = self.items.get(product_id)
        if not item:
            return False
        return (item.quantity - item.reserved) >= quantity

    def reserve_stock(self, product_id: str, quantity: int) -> bool:
        """
        Reserve stock for a pending order.

        BUG-047: No locking - concurrent reservations can exceed available stock.
        """
        item = self.items.get(product_id)
        if not item:
            return False

        available = item.quantity - item.reserved

        # BUG-047: TOCTOU race - check and update not atomic
        if available >= quantity:
            # Another thread could reserve between check and update
            item.reserved += quantity
            # BUG-048: No audit log of reservation
            return True

        return False

    def confirm_sale(self, product_id: str, quantity: int) -> bool:
        """
        Confirm sale and decrement stock.

        BUG-049: No check prevents stock from going negative.
        """
        item = self.items.get(product_id)
        if not item:
            return False

        # BUG-049: Can result in negative quantity
        item.quantity -= quantity
        item.reserved = max(0, item.reserved - quantity)
        item.last_updated = datetime.utcnow()

        # BUG-048: No audit trail
        return True

    def restock(self, product_id: str, quantity: int) -> bool:
        """Add stock for a product."""
        item = self.items.get(product_id)
        if not item:
            return False

        item.quantity += quantity
        item.last_updated = datetime.utcnow()
        return True

    def get_low_stock_items(self) -> List[InventoryItem]:
        """Get items below reorder level."""
        return [
            item for item in self.items.values()
            if item.quantity <= item.reorder_level
        ]

    def get_inventory_report(self) -> dict:
        """Generate inventory summary."""
        total_value = 0  # Would need prices
        return {
            "total_products": len(self.items),
            "low_stock_count": len(self.get_low_stock_items()),
            "total_reserved": sum(i.reserved for i in self.items.values()),
            "total_stock": sum(i.quantity for i in self.items.values()),
            "negative_stock": sum(
                1 for i in self.items.values() if i.quantity < 0
            ),
        }
