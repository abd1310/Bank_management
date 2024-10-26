from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date, timedelta

from core.models import Bank, BankAccount, Transaction, Loan
from core.utils import CurrencyConverter

User = get_user_model()

class ModelTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            name='Test User'
        )
        self.bank = Bank.get_instance()
        self.account = BankAccount.objects.create(
            user=self.user,
            account_number='1234567890',
            balance=Decimal('1000.00'),
            currency='NIS'
        )

    def test_create_user(self):
        """Test creating a new user"""
        email = 'test2@example.com'
        password = 'testpass123'
        user = User.objects.create_user(
            email=email,
            password=password
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_create_superuser(self):
        """Test creating a new superuser"""
        email = 'admin@example.com'
        password = 'adminpass123'
        user = User.objects.create_superuser(
            email=email,
            password=password
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_bank_instance(self):
        """Test getting or creating a bank instance"""
        bank = Bank.get_instance()
        self.assertIsNotNone(bank)
        self.assertEqual(bank.balance, Decimal('10000000.00'))

    def test_bank_update_balance(self):
        """Test updating bank balance"""
        initial_balance = self.bank.balance
        self.bank.update_balance(Decimal('1000.00'))
        self.assertEqual(self.bank.balance, initial_balance + Decimal('1000.00'))

    def test_bank_account_creation(self):
        """Test creating a bank account"""
        self.assertEqual(self.account.user, self.user)
        self.assertEqual(self.account.balance, Decimal('1000.00'))
        self.assertEqual(self.account.currency, 'NIS')

    def test_bank_account_deposit(self):
        """Test depositing money into account"""
        initial_balance = self.account.balance
        self.account.deposit(Decimal('500.00'))
        self.assertEqual(self.account.balance, initial_balance + Decimal('500.00'))

    def test_bank_account_withdraw(self):
        """Test withdrawing money from account"""
        initial_balance = self.account.balance
        self.account.withdraw(Decimal('500.00'))
        self.assertEqual(self.account.balance, initial_balance - Decimal('500.00'))

    # def test_bank_account_transfer(self):
    #     """Test transferring money between accounts"""
    #     account2 = BankAccount.objects.create(
    #         user=User.objects.create_user(email='test2@example.com', password='testpass123'),
    #         account_number='0987654321',
    #         balance=Decimal('500.00'),
    #         currency='NIS'
    #     )
        
    #     initial_balance1 = self.account.balance
    #     initial_balance2 = account2.balance
        
    #     # Mocking the currency conversion
    #     CurrencyConverter.convert = lambda amount, from_currency, to_currency: amount * 3.5
        
    #     self.account.transfer(account2, Decimal('100.00'))
        
    #     self.assertEqual(self.account.balance, initial_balance1 - Decimal('100.00'))
    #     self.assertEqual(account2.balance, initial_balance2 + Decimal('350.00'))  # 100 NIS = 350 USD (mocked conversion)

    def test_transaction_creation(self):
        """Test creating a transaction"""
        transaction = Transaction.objects.create(
            account=self.account,
            amount=Decimal('100.00'),
            transaction_type='DEPOSIT'
        )
        self.assertEqual(transaction.fee, Decimal('1.00'))  # 1% fee

    def test_loan_creation(self):
        """Test creating a loan"""
        loan = Loan.objects.create(
            account=self.account,
            amount=Decimal('5000.00'),
            interest_rate=Decimal('5.00'),
            end_date=date.today() + timedelta(days=365),
            currency='NIS'
        )
        self.assertTrue(loan.is_active)


    def test_bank_account_deletion(self):
        """Test deleting a bank account"""
        account = BankAccount.objects.create(
            user=User.objects.create_user(email='test3@example.com', password='testpass123'),
            account_number='1122334455',
            balance=Decimal('0.00'),
            currency='NIS'
        )
        account.delete()
        self.assertFalse(BankAccount.objects.filter(account_number='1122334455').exists())

        # Test deletion with non-zero balance
        with self.assertRaises(ValueError):
            self.account.delete()

# if __name__ == '__main__':
#     unittest.main()