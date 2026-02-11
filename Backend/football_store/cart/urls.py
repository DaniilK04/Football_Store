from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()

router.register(r'cart', CartViewSet, basename='cart')
router.register(r'item', CartItemViewSet, basename='cart_item')

urlpatterns = router.urls