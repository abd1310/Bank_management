from django.urls import path, include
from rest_framework.routers import DefaultRouter
from bank_account import views
from .views import DepositView, WithdrawView, TransferView, BalanceView, SuspendAccountView

router = DefaultRouter()
router.register('accounts', views.BankAccountViewSet, basename='bankaccount')

app_name = 'bank_account'

urlpatterns = [
    path('', include(router.urls)),
    path('create/', views.BankAccountCreateView.as_view(), name='create'),
    path('accounts/<int:account_id>/deposit/', DepositView.as_view(), name='deposit'),
    path('accounts/<int:account_id>/withdraw/', WithdrawView.as_view(), name='withdraw'),
    path('accounts/<int:account_id>/transfer/', TransferView.as_view(), name='transfer'),
    path('accounts/<int:account_id>/balance/', BalanceView.as_view(), name='balance'),
    path('accounts/<int:account_id>/suspend/', SuspendAccountView.as_view(), name='suspend'),
]
