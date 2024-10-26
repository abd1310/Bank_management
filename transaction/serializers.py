from rest_framework import serializers
from core.models import Transaction

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id', 'account', 'amount', 'transaction_type', 'timestamp','currency','fee']
        read_only_fields = ['id', 'timestamp', 'fee']
