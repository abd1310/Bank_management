from rest_framework import viewsets
#from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from .serializers import BankAccountSerializer, TransferSerializer, DepositSerializer, \
    WithdrawSerializer, BankAccountCreateSerializer ,SuspendAccountSerializer
from rest_framework import generics, status
from rest_framework.response import Response
from core.models import BankAccount
# from .utils import send_welcome_email

class BankAccountViewSet(viewsets.ModelViewSet):
    queryset = BankAccount.objects.all()
    serializer_class = BankAccountSerializer
    permission_classes = (IsAuthenticated,)
    # authentication_classes = (TokenAuthentication,)
    http_method_names = ('get', 'delete')

    def get_queryset(self):
        return BankAccount.objects.filter(user=self.request.user).order_by('-id')

    def destroy(self, request, *args, **kwargs):
        account = self.get_object()
        try:
            account.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
    def perform_create(self, serializer):
        serializer.save(user=self.request.user,is_active=True)  

class BankAccountCreateView(generics.CreateAPIView):   
    serializer_class = BankAccountCreateSerializer
    permission_classes = (IsAuthenticated,)
  #  authentication_classes = (TokenAuthentication,)

    def create(self, request, *args, **kwargs):
        if BankAccount.objects.filter(user=request.user).exists():
            return Response({"detail": "User already has a bank account"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        # user_email = self.request.user.email
        
        # send_welcome_email(user_email)

class DepositView(generics.GenericAPIView):
    serializer_class = DepositSerializer
    permission_classes = (IsAuthenticated,)
   # authentication_classes = (TokenAuthentication,)

    def post(self, request, account_id):
        try:
            account = BankAccount.objects.get(pk=account_id, user=request.user)
        except BankAccount.DoesNotExist:
            return Response({"error": "Bank account does not exist or does not belong to you."}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if the account is active
        if not account.is_active:
            return Response({"error": "Account is suspended. No operations allowed."}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            amount = serializer.validated_data['amount']
            account.deposit(amount)
            return Response({'status': 'deposit successful'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
class WithdrawView(generics.GenericAPIView):
    serializer_class = WithdrawSerializer
    permission_classes = (IsAuthenticated,)
    #authentication_classes = (TokenAuthentication,)

    def post(self, request, account_id):
        try:
            account = BankAccount.objects.get(pk=account_id, user=request.user)
        except BankAccount.DoesNotExist:
            return Response({"error": "Bank account does not exist or does not belong to you."}, status=status.HTTP_404_NOT_FOUND)
         # Check if the account is active
        if not account.is_active:
            return Response({"error": "Account is suspended. No operations allowed."}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            amount = serializer.validated_data['amount']
            try:
                account.withdraw(amount)
                return Response({'status': 'withdrawal successful', 'balance': account.balance})
            except ValueError as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
class TransferView(generics.GenericAPIView):
    serializer_class = TransferSerializer
    permission_classes = (IsAuthenticated,)
    #authentication_classes = (TokenAuthentication,)

    def post(self, request, account_id):
        try:
            account = BankAccount.objects.get(pk=account_id, user=request.user)
        except BankAccount.DoesNotExist:
            return Response({"error": "Bank account does not exist or does not belong to you."}, status=status.HTTP_404_NOT_FOUND)

         # Check if the account is active
        if not account.is_active:
            return Response({"error": "Account is suspended. No operations allowed."}, status=status.HTTP_403_FORBIDDEN)


        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            to_account_number = serializer.validated_data['to_account']
            amount = serializer.validated_data['amount']
            try:
                to_account = BankAccount.objects.get(account_number=to_account_number)
                account.transfer(to_account, amount)
                return Response({'status': 'transfer successful'})
            except BankAccount.DoesNotExist:
                return Response({'error': 'Recipient account not found'}, status=status.HTTP_400_BAD_REQUEST)
            except ValueError as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BalanceView(generics.GenericAPIView):
    serializer_class = TransferSerializer
    permission_classes = (IsAuthenticated,)
    #authentication_classes = (TokenAuthentication,)

    def get(self, request, account_id):
        try:
            account = BankAccount.objects.get(pk=account_id, user=request.user)
        except BankAccount.DoesNotExist:
            return Response({"error": "Bank account does not exist or does not belong to you."}, status=status.HTTP_404_NOT_FOUND)

        return Response({'balance': str(account.get_balance())})
    
    
class SuspendAccountView(generics.GenericAPIView):
    serializer_class = SuspendAccountSerializer
    permission_classes = (IsAuthenticated,)
    #authentication_classes = (TokenAuthentication,)

    def post(self, request, account_id):
        try:
            account = BankAccount.objects.get(pk=account_id, user=request.user)
        except BankAccount.DoesNotExist:
            return Response({"error": "Bank account does not exist or does not belong to you."}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            action = serializer.validated_data['action']
            
            if action == 'activate':
                account.is_active = True
                account.save()
                return Response({'status': 'account activated successfully'})
            elif action == 'suspend':
                account.is_active = False
                account.save()
                return Response({'status': 'account suspended successfully'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)