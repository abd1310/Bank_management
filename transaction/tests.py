from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
from core.models import BankAccount, Transaction

class TransactionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'test@example.com',
            'testpass123'
        )
        self.client.force_authenticate(self.user)
        self.bank_account = BankAccount.objects.create(
            user=self.user,
            account_number='1234567890',
            balance=Decimal('1000.00'),
            currency='USD'
        )

    # def test_create_transaction(self):
    #     payload = {
    #         'account': self.bank_account.id,
    #         'amount': '100.00',
    #         'transaction_type': 'DEPOSIT'
    #     }
    #     res = self.client.post('/api/transactions/', payload)
    #     self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    #     transaction = Transaction.objects.get(id=res.data['id'])
    #     self.assertEqual(transaction.amount, Decimal('100.00'))
    #     self.assertEqual(transaction.transaction_type, 'DEPOSIT')
    #     self.assertEqual(transaction.fee, Decimal('1.00'))  # Assuming 1% fee

    def test_list_user_transactions(self):
        Transaction.objects.create(account=self.bank_account, amount='50.00', transaction_type='WITHDRAW')
        Transaction.objects.create(account=self.bank_account, amount='150.00', transaction_type='DEPOSIT')

        res = self.client.get('/api/transactions/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)

    def test_retrieve_transaction(self):
        transaction = Transaction.objects.create(account=self.bank_account, amount='75.00', transaction_type='TRANSFER')
        res = self.client.get(f'/api/transactions/{transaction.id}/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['amount'], '75.00')
        self.assertEqual(res.data['transaction_type'], 'TRANSFER')

    def test_transaction_fee_calculation(self):
        transaction = Transaction.objects.create(account=self.bank_account, amount='100.00', transaction_type='DEPOSIT')
        self.assertEqual(transaction.fee, Decimal('1.00'))  # Assuming 1% fee

    def test_invalid_transaction_type(self):
        with self.assertRaises(ValueError):
            Transaction.objects.create(account=self.bank_account, amount='100.00', transaction_type='INVALID')