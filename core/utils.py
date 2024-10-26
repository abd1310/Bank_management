from decimal import Decimal, ROUND_HALF_UP

class CurrencyConverter:
    @staticmethod
    def convert(amount, from_currency, to_currency):
        # For demonstration, using fixed rates
        # In a real application, you'd fetch current rates from an API
        rates = {
            'USD': Decimal('3.5'),
            'EUR': Decimal('4.0'),
            'NIS': Decimal('1.0'),
        }
        
        # Check if currencies are supported
        if from_currency not in rates or to_currency not in rates:
            raise ValueError("Unsupported currency")
        
        # Perform conversion
        converted_amount = amount * rates[to_currency] / rates[from_currency]
        
        # Round to 2 decimal places
        return converted_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)