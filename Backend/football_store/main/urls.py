from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()

router.register(r'v1/category', CategoryViewSet, basename='category')
router.register(r'v1/product', ProductViewSet, basename='product')
router.register(r'v1/order', OrderViewSet, basename='order')

urlpatterns = router.urls