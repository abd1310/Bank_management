from rest_framework import serializers
from core.models import Loan 
from django.utils import timezone
from rest_framework import serializers
from core.models import Loan


class LoanSerializer(serializers.ModelSerializer):

    class Meta:
        model = Loan
        fields = ['id', 'account', 'amount', 'interest_rate', 'end_date']
        read_only_fields = ['id']

    def validate(self, data):
        if data['end_date'] <= timezone.now().date():
            raise serializers.ValidationError("End date must be after the start date.")
        if data['amount'] > Loan.MAX_LOAN_AMOUNT:
            raise serializers.ValidationError(f"Loan amount cannot exceed {Loan.MAX_LOAN_AMOUNT} NIS")
        
        # Ensure the account belongs to the current user
        request = self.context.get('request')
        if request and request.user:
            if data['account'].user != request.user:
                raise serializers.ValidationError("You can only create loans for your own account.")
        else:
            raise serializers.ValidationError("Authentication required.")
        
        return data
    
    def validate_account(self, value):
            if not value.is_active:
                raise serializers.ValidationError("Cannot create a loan for an inactive account")
            return value

    
class LoanRepaymentSerializer(serializers.ModelSerializer):
    monthly_payment = serializers.SerializerMethodField()
    currency = serializers.CharField(source='account.currency')
    remaining_balance = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Loan
        fields = ['id', 'account', 'amount', 'interest_rate', 'start_date', 'end_date', 'is_active', 'monthly_payment', 'currency', 'remaining_balance']
        read_only_fields = ['id', 'account', 'amount', 'interest_rate', 'start_date', 'end_date', 'is_active', 'monthly_payment', 'currency']

    def get_monthly_payment(self, obj) -> float:
        principal = obj.amount
        rate = obj.interest_rate / 100 / 12  # monthly interest rate
        time = (obj.end_date.year - obj.start_date.year) * 12 + (obj.end_date.month - obj.start_date.month)

        if rate == 0:
            return round(principal / time, 2)
        
        monthly_payment = principal * (rate * (1 + rate) ** time) / ((1 + rate) ** time - 1)
        return round(monthly_payment, 2)    