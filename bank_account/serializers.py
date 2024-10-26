import random
from rest_framework import serializers, status
from rest_framework.response import Response
from core.models import BankAccount,Bank
from decimal import Decimal

class BankAccountSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = BankAccount
        fields = ['id', 'user_email', 'account_number', 'balance', 'currency', 'is_active']
        read_only_fields = ['id', 'user_email', 'account_number', 'balance', 'currency', 'is_active']

class BankAccountCreateSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    currency = serializers.ChoiceField(choices=['NIS', 'USD', 'EUR'], default='NIS')

    class Meta:
        model = BankAccount
        fields = ['id', 'user_email', 'account_number', 'balance', 'currency', 'is_active']
        read_only_fields = ['id', 'user_email', 'account_number', 'balance', 'currency', 'is_active']

    def create(self, validated_data):
        currency = validated_data.get('currency', 'NIS')
        # Generate a unique account number
        while True:
            account_number = str(random.randint(1000000000, 9999999999))
            if not BankAccount.objects.filter(account_number=account_number).exists():
                break

        # Create the bank account with default values
        bank_account = BankAccount.objects.create(
            user=self.context['request'].user,
            account_number=account_number,
            balance=0,
            currency=currency,
            is_active=True
        )
        return bank_account
    
class SuspendAccountSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['activate', 'suspend'])

class DepositSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.01'))

class WithdrawSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.01'))

class TransactionSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)

class TransferSerializer(serializers.Serializer):
    to_account = serializers.CharField(max_length=20)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.01'))
