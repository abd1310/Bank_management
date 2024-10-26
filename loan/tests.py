from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.utils import timezone
from core.models import Loan, BankAccount
from django.contrib.auth import get_user_model

class LoanAPITestCase(APITestCase):

    def setUp(self):
        User = get_user_model()  # Use the custom user model
        self.user = User.objects.create_user(email='testuser@example.com', password='testpassword')
        self.account = BankAccount.objects.create(user=self.user, balance=5000, currency='NIS', is_active=True)
        self.loan_url = reverse('loan:loan-list')  # URL for creating loans
        self.repay_url = reverse('loan:repay-list')  # URL for repaying loans
        self.client.force_authenticate(user=self.user)

    def test_create_loan(self):
        """Test loan creation with valid data"""
        data = {
            'account': self.account.id,
            'amount': 1000,
            'interest_rate': 5,
            'end_date': (timezone.now() + timezone.timedelta(days=365)).date()
        }
        response = self.client.post(self.loan_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Loan.objects.count(), 1)
    
    def test_loan_creation_exceeds_max_amount(self):
        """Test loan creation exceeding max allowed amount"""
        data = {
            'account': self.account.id,
            'amount': Loan.MAX_LOAN_AMOUNT + 1,  # Exceeding max amount
            'interest_rate': 5,
            'end_date': (timezone.now() + timezone.timedelta(days=365)).date()
        }
        response = self.client.post(self.loan_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(f"Loan amount cannot exceed {Loan.MAX_LOAN_AMOUNT} NIS", response.data['non_field_errors'])

