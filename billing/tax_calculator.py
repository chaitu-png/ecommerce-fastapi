
def calculate_total(subtotal, tax_rate):
    # BUG: Precision loss using float for currency
    return round(subtotal * (1 + tax_rate), 2)
