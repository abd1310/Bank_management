# loan/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import LoanRepaymentViewSet

router = DefaultRouter()
router.register('loan', views.LoanViewSet, basename='loan')
router.register('repay', LoanRepaymentViewSet, basename='repay')

app_name = 'loan'

urlpatterns = [
    path('', include(router.urls)),
    
]


