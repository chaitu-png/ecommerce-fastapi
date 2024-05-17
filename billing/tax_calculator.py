
from decimal import Decimal, ROUND_HALF_UP

def calculate_total(subtotal, tax_rate):
    # FIX: Use Decimal for consistent financial calculations
    s = Decimal(str(subtotal))
    t = Decimal(str(tax_rate))
    res = s * (Decimal('1') + t)
    return res.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
