from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from core.models import BankAccount, User
from decimal import Decimal

class BankAccountAPITestCase(APITestCase):

    def setUp(self):
        # Create a user and authenticate them
        self.user = User.objects.create_user(email='testuser@example.com', password='testpassword')
        self.client.force_authenticate(user=self.user)

        # Ensure no existing bank account for the user
        BankAccount.objects.filter(user=self.user).delete()
        
        # Create a bank account for the user
        self.account = BankAccount.objects.create(
            user=self.user,
            account_number='1234567890',
            balance=Decimal('1000.00'),
            currency='NIS',
            is_active=True
        )

        # URLs for various account operations
        self.create_account_url = reverse('bank_account:create')
        self.deposit_url = reverse('bank_account:deposit', kwargs={'account_id': self.account.id})
        self.withdraw_url = reverse('bank_account:withdraw', kwargs={'account_id': self.account.id})
        self.transfer_url = reverse('bank_account:transfer', kwargs={'account_id': self.account.id})
        self.balance_url = reverse('bank_account:balance', kwargs={'account_id': self.account.id})
        self.suspend_url = reverse('bank_account:suspend', kwargs={'account_id': self.account.id})

    def test_create_bank_account(self):
        """Test creating a new bank account"""
        # Ensure no bank account exists for the user
        BankAccount.objects.filter(user=self.user).delete()  # Clean slate

        data = {
            'currency': 'NIS'  # Make sure to provide required fields
        }

        response = self.client.post(self.create_account_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(BankAccount.objects.count(), 1)

    def test_create_bank_account_duplicate(self):
        """Test that a user cannot create more than one bank account"""
        # Create the first bank account
        self.test_create_bank_account()  # Call the previous test to ensure setup

        data = {'currency': 'USD'}
        response = self.client.post(self.create_account_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], "User already has a bank account")

    def test_deposit(self):
        """Test depositing money into the account"""
        data = {'amount': Decimal('500.00')}
        response = self.client.post(self.deposit_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal('1500.00'))

    def test_withdraw(self):
        """Test withdrawing money from the account"""
        data = {'amount': Decimal('300.00')}
        response = self.client.post(self.withdraw_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal('700.00'))

    # def test_withdraw_insufficient_balance(self):
    #     """Test withdrawal with insufficient balance."""
    #     withdraw_amount = Decimal('1000.00')  # Attempt to withdraw more than balance
    #     data = {'amount': withdraw_amount}

    #     # Perform the withdrawal
    #     response = self.client.post(self.withdraw_url, data, format='json')

    #     # Check response status code
    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    #     # Ensure the correct error message is returned
    #     self.assertEqual(response.data['error'], 'Cannot withdraw. Balance would exceed minimum limit of NIS')

    #     # Refresh the account from the database to check the balance
    #     self.account.refresh_from_db()

    #     # Check that the balance has not changed
    #     self.assertEqual(self.account.balance, Decimal('700.00'))

    # def test_transfer(self):
    #     """Test transferring money to another account"""
    #     # Create a recipient account
    #     recipient = BankAccount.objects.create(
    #         user=self.user,  # You can change this to another user if needed
    #         account_number='0987654321',
    #         balance=Decimal('500.00'),
    #         currency='NIS',
    #         is_active=True
    #     )
        
    #     data = {'to_account': recipient.account_number, 'amount': Decimal('200.00')}
    #     response = self.client.post(self.transfer_url, data, format='json')
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)

    #     # Check balances after transfer
    #     self.account.refresh_from_db()
    #     recipient.refresh_from_db()
    #     self.assertEqual(self.account.balance, Decimal('800.00'))
    #     self.assertEqual(recipient.balance, Decimal('700.00'))

    def test_transfer_account_not_found(self):
        """Test transfer to a non-existent account"""
        data = {'to_account': '9999999999', 'amount': Decimal('200.00')}
        response = self.client.post(self.transfer_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Recipient account not found')

    def test_get_balance(self):
        """Test retrieving the account balance"""
        response = self.client.get(self.balance_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['balance'], '1000.00')

    def test_suspend_account(self):
        """Test suspending the account"""
        data = {'action': 'suspend'}
        response = self.client.post(self.suspend_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.account.refresh_from_db()
        self.assertFalse(self.account.is_active)

    def test_activate_account(self):
        """Test activating a suspended account"""
        # First suspend the account
        self.account.is_active = False
        self.account.save()

        data = {'action': 'activate'}
        response = self.client.post(self.suspend_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.account.refresh_from_db()
        self.assertTrue(self.account.is_active)

    def test_deposit_suspended_account(self):
        """Test deposit when the account is suspended"""
        self.account.is_active = False
        self.account.save()

        data = {'amount': Decimal('200.00')}
        response = self.client.post(self.deposit_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['error'], 'Account is suspended. No operations allowed.')

    def test_withdraw_suspended_account(self):
        """Test withdrawal when the account is suspended"""
        self.account.is_active = False
        self.account.save()

        data = {'amount': Decimal('200.00')}
        response = self.client.post(self.withdraw_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['error'], 'Account is suspended. No operations allowed.')

    def test_transfer_suspended_account(self):
        """Test transfer when the account is suspended"""
        self.account.is_active = False
        self.account.save()

        data = {'to_account': '0987654321', 'amount': Decimal('200.00')}
        response = self.client.post(self.transfer_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['error'], 'Account is suspended. No operations allowed.')
