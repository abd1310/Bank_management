from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal

from rest_framework.exceptions import ValidationError

from core.utils import CurrencyConverter


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        user = self.create_user(email, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'



class Bank(models.Model):
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('10000000.00'))
    MAX_LOAN_AMOUNT = Decimal('50000.00')  # Maximum allowed loan

    @classmethod
    def get_instance(cls):
        """Get the first bank instance or create one with the starting balance."""
        bank = cls.objects.first()
        if not bank:
            bank = cls.objects.create(balance=Decimal('10000000.00'))  # Ensure the starting balance
        return bank

    def can_grant_loan(self, loan_amount):
        """Check if the bank can grant the loan based on balance and max loan limits."""
        if loan_amount > self.MAX_LOAN_AMOUNT:
            raise ValidationError(f"Loan amount cannot exceed {self.MAX_LOAN_AMOUNT} NIS.")
        if self.balance < loan_amount:
            raise ValidationError("The bank does not have sufficient funds to grant this loan.")
        return True

    def update_balance(self, amount):
        """Update the bank's balance after transactions or loans."""
        self.balance += amount  # amount can be positive (deposit) or negative (loan or withdrawal)
        self.save()


class BankAccount(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bank_account')
    #user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bank_accounts')
    account_number = models.CharField(max_length=20, unique=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    # currency = models.CharField(max_length=3, default='NIS')
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    min_BALANCE = Decimal('-100.00')

    CURRENCY_CHOICES = [
        ('NIS', 'New Israeli Shekel'),
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'),
    ]
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='NIS')

    def __str__(self):
        return f"{self.account_number} - {self.user.email}"
    

    def delete(self, *args, **kwargs):
        if self.balance != 0:
            raise ValueError("Cannot delete account with non-zero balance")
        super().delete(*args, **kwargs)

    def deposit(self, amount):
        self.balance += amount
        self.save()
        Transaction.objects.create(
            account=self,
            amount=amount,
            transaction_type='DEPOSIT'
        )

    def withdraw(self, amount):
        if self.balance - amount < self.min_BALANCE:
            raise ValueError(
                f"Cannot withdraw. Balance would exceed minimum limit of NIS")
        self.balance -= amount
        self.save()
        Transaction.objects.create(
            account=self,
            amount=amount,
            transaction_type='WITHDRAW'
        )

    def transfer(self, to_account, amount):
        if self.balance < amount:
            raise ValueError("Insufficient funds")

        converted_amount = CurrencyConverter.convert(amount, self.currency, to_account.currency)

        self.withdraw(amount)
        to_account.deposit(converted_amount)

        Transaction.objects.create(
            account=self,
            amount=amount,
            transaction_type='TRANSFER'
        )

    def get_balance(self):
        return self.balance


class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('DEPOSIT', 'Deposit'),
        ('WITHDRAW', 'Withdraw'),
        ('TRANSFER', 'Transfer'),
    ]
    account = models.ForeignKey(BankAccount, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='NIS')

    def save(self, *args, **kwargs):
        if self.transaction_type not in dict(self.TRANSACTION_TYPES):
            raise ValueError('Invalid transaction type')

        # Ensure amount is a Decimal
        if isinstance(self.amount, str):
            self.amount = Decimal(self.amount)

        # Calculate fee (e.g., 1% of the transaction amount)
        self.fee = self.amount * Decimal('0.01')

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')} | {self.transaction_type} | {self.amount} {self.currency} | Account: {self.account.account_number}"



class Loan(models.Model):
    account = models.ForeignKey(BankAccount, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    currency = models.CharField(max_length=3, choices=BankAccount.CURRENCY_CHOICES, default='NIS')

    MAX_LOAN_AMOUNT = Decimal('50000.00')

    
    def __str__(self):
        status = "Active" if self.is_active else "Inactive"
        return f"Loan ({status}) | {self.amount} {self.currency} | Account: {self.account.account_number} | Rate: {self.interest_rate}% | Ends: {self.end_date}"
   