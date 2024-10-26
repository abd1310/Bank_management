from rest_framework import viewsets, status
#from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from core.models import Loan, BankAccount
from .serializers import LoanSerializer, LoanRepaymentSerializer
from rest_framework.response import Response

class LoanViewSet(viewsets.ModelViewSet):
    serializer_class = LoanSerializer
    permission_classes = (IsAuthenticated,)
  #  authentication_classes = (TokenAuthentication,)
    http_method_names = ['post', 'head']
    
    def get_queryset(self):
        return Loan.objects.filter(account__user=self.request.user)

    def create(self, request, *args, **kwargs):
        # Create a mutable copy of the request data
        mutable_data = request.data.copy()

        # Ensure the account belongs to the current user
        account_id = mutable_data.get('account')
        try:
            account = BankAccount.objects.get(id=account_id, user=request.user)
        except BankAccount.DoesNotExist:
            return Response({"error": "Invalid account or not authorized."}, status=status.HTTP_400_BAD_REQUEST)

        # Use the mutable copy for serializer initialization
        serializer = self.get_serializer(data=mutable_data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        # Set the account here
        account_id = self.request.data.get('account')
        account = BankAccount.objects.get(id=account_id, user=self.request.user)
        serializer.save(account=account)
    
    
class LoanRepaymentViewSet(viewsets.ModelViewSet):
    serializer_class = LoanRepaymentSerializer
    permission_classes = (IsAuthenticated,)
  #  authentication_classes = (TokenAuthentication,)
    queryset = Loan.objects.all()
    http_method_names = ('get','head', 'options')
