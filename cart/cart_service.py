"""
Shopping Cart Service - Cart management and checkout.

BUG INVENTORY:
- BUG-043: Price stored at add-time, not recalculated at checkout (stale price)
- BUG-044: No inventory check on add-to-cart
- BUG-045: Cart items can have negative quantities
- BUG-046: Discount code applied multiple times
"""

import time
from datetime import datetime
from typing import Dict, List, Optional


class CartItem:
    def __init__(self, product_id: str, name: str, price: float,
                 quantity: int = 1):
        self.product_id = product_id
        self.name = name
        # BUG-043: Price captured at add-time, never refreshed
        self.price = price
        self.quantity = quantity
        self.added_at = datetime.utcnow()


class ShoppingCart:
    def __init__(self, user_id: str):
        self.id = f"CART-{int(time.time() * 1000)}"
        self.user_id = user_id
        self.items: Dict[str, CartItem] = {}
        self.discount_codes: List[str] = []
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()


class CartService:
    """Manages shopping carts for users."""

    def __init__(self):
        self.carts: Dict[str, ShoppingCart] = {}
        self._product_catalog: Dict[str, dict] = {}

    def create_cart(self, user_id: str) -> ShoppingCart:
        """Create a new cart for a user."""
        cart = ShoppingCart(user_id)
        self.carts[user_id] = cart
        return cart

    def add_item(self, user_id: str, product_id: str, name: str,
                 price: float, quantity: int = 1) -> bool:
        """
        Add item to cart.

        BUG-044: No inventory check - user can add items that are out of stock.
        BUG-045: No validation on quantity - negative values accepted.
        BUG-043: Price is captured now and never updated.
        """
        cart = self.carts.get(user_id)
        if not cart:
            cart = self.create_cart(user_id)

        # BUG-045: No quantity validation
        # quantity could be -5, making the total negative

        if product_id in cart.items:
            cart.items[product_id].quantity += quantity
        else:
            # BUG-043: Price frozen at this moment
            cart.items[product_id] = CartItem(product_id, name, price, quantity)

        # BUG-044: No inventory check at all
        cart.updated_at = datetime.utcnow()
        return True

    def remove_item(self, user_id: str, product_id: str) -> bool:
        """Remove item from cart."""
        cart = self.carts.get(user_id)
        if not cart or product_id not in cart.items:
            return False

        del cart.items[product_id]
        cart.updated_at = datetime.utcnow()
        return True

    def apply_discount(self, user_id: str, code: str,
                       discount_percent: float) -> bool:
        """
        Apply discount code to cart.

        BUG-046: No check if code already applied.
        Same 20% discount can be applied 5x = 100% off.
        """
        cart = self.carts.get(user_id)
        if not cart:
            return False

        # BUG-046: No deduplication check
        cart.discount_codes.append(code)
        return True

    def calculate_total(self, user_id: str) -> dict:
        """Calculate cart total with discounts."""
        cart = self.carts.get(user_id)
        if not cart:
            return {"subtotal": 0, "discount": 0, "total": 0}

        # BUG-043: Uses stored prices, not current catalog prices
        subtotal = sum(
            item.price * item.quantity
            for item in cart.items.values()
        )

        # BUG-046: Each discount code applies independently
        total_discount = 0
        for code in cart.discount_codes:
            # Assume 10% per code for simulation
            total_discount += subtotal * 0.10

        # BUG: Total can go negative with enough discount codes
        total = subtotal - total_discount

        return {
            "subtotal": round(subtotal, 2),
            "discount": round(total_discount, 2),
            "total": round(total, 2),  # Can be negative!
            "items_count": sum(i.quantity for i in cart.items.values()),
        }

    def checkout(self, user_id: str) -> Optional[dict]:
        """
        Process checkout.

        BUG-043: Prices not re-validated against current catalog.
        BUG-044: Inventory not checked - may sell out-of-stock items.
        """
        cart = self.carts.get(user_id)
        if not cart or not cart.items:
            return None

        totals = self.calculate_total(user_id)

        # BUG: No final inventory check before order creation
        # BUG: No price re-validation

        order = {
            "order_id": f"ORD-{int(time.time() * 1000)}",
            "user_id": user_id,
            "items": [
                {
                    "product_id": item.product_id,
                    "name": item.name,
                    "price": item.price,  # BUG-043: Stale price
                    "quantity": item.quantity,
                }
                for item in cart.items.values()
            ],
            "totals": totals,
            "created_at": datetime.utcnow().isoformat(),
        }

        # Clear cart after checkout
        cart.items.clear()
        cart.discount_codes.clear()

        return order
