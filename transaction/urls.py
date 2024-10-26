from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('', views.TransactionViewSet, basename='transaction')

app_name = 'transaction'

urlpatterns = [
    path('', include(router.urls)),
]
