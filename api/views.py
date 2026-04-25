from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from decimal import Decimal

# GBP is the base currency
EXCHANGE_RATES = {
    'GBP': Decimal('1.00'),
    'USD': Decimal('1.25'),
    'EUR': Decimal('1.15'),
}

# Currency conversion logic
class CurrencyConversionView(APIView):
    def get(self, request, currency1, currency2, amount):
        currency1 = currency1.upper()
        currency2 = currency2.upper()

        if currency1 not in EXCHANGE_RATES:
            return Response(
                {'error': f'Currency {currency1} is not supported'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if currency2 not in EXCHANGE_RATES:
            return Response(
                {'error': f'Currency {currency2} is not supported'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            amount = Decimal(str(amount))
        except:
            return Response(
                {'error': 'Invalid amount'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Convert to GBP first, then to target currency
        to_GBP = 1 / EXCHANGE_RATES[currency1]
        rate = to_GBP * EXCHANGE_RATES[currency2]
        converted_amount = round(amount * rate, 2)

        return Response({
            'from_currency': currency1,
            'to_currency': currency2,
            'rate': round(rate, 6),
            'amount': amount,
            'converted_amount': converted_amount,
        }, status=status.HTTP_200_OK)
