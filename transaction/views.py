from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from core.models import Transaction
from .serializers import TransactionSerializer



class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = (IsAuthenticated,)
 #   authentication_classes = (TokenAuthentication,)
    http_method_names = ('get','head', 'options')

    def get_queryset(self):
        return Transaction.objects.filter(account__user=self.request.user)
