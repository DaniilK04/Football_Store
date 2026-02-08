from rest_framework import status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny

from django.db import transaction
from django.db.models import F

from .models import Category, Product, Order, OrderItem
from .serializers import (
    CategorySerializer, ProductSerializer,
    OrderReadSerializer, OrderAdminUpdateSerializer
)
from cart.models import Cart


class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = 'slug'

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAdminUser()]


class ProductViewSet(ModelViewSet):
    serializer_class = ProductSerializer
    lookup_field = 'slug'

    def get_queryset(self):
        if self.action in ['list', 'retrieve']:
            return Product.objects.filter(is_published=True)
        return Product.objects.all()

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAdminUser()]


class OrderViewSet(ReadOnlyModelViewSet):
    """
    Просмотр своих заказов + создание из корзины + изменение статуса (админ)
    """
    serializer_class = OrderReadSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            # Администратор видит все заказы
            return Order.objects.all().prefetch_related('order_items__product')
        # Обычный пользователь видит только свои
        return Order.objects.filter(user=self.request.user).prefetch_related('order_items__product')

    def get_serializer_class(self):
        if self.action == 'partial_update' and self.request.user.is_staff:
            return OrderAdminUpdateSerializer
        return OrderReadSerializer

    def get_permissions(self):
        if self.action in ['partial_update']:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    @action(detail=False, methods=['post'], url_path='create-from-cart')
    def create_from_cart(self, request):
        user = request.user

        try:
            cart = user.cart
        except Cart.DoesNotExist:
            return Response({"detail": "У вас нет корзины"}, status=400)

        if not cart.items.exists():
            return Response({"detail": "Корзина пуста"}, status=400)

        with transaction.atomic():
            # Блокируем все товары, которые есть в корзине
            product_ids = cart.items.values_list('product_id', flat=True)
            locked_products = {
                p.id: p for p in Product.objects.select_for_update().filter(
                    id__in=product_ids,
                    is_published=True
                )
            }

            order = Order.objects.create(user=user, status='new')

            for cart_item in cart.items.select_related('product'):
                product = locked_products.get(cart_item.product_id)

                if not product:
                    raise serializers.ValidationError(
                        f"Товар '{cart_item.product.name}' больше недоступен"
                    )

                if product.quantity < cart_item.quantity:
                    raise serializers.ValidationError(
                        f"Недостаточно '{product.name}' (в наличии: {product.quantity}, нужно: {cart_item.quantity})"
                    )

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=cart_item.quantity,
                    # price можно не передавать
                )

                # Уменьшаем остаток на складе
                Product.objects.filter(pk=product.pk).update(
                    quantity=F('quantity') - cart_item.quantity
                )

            # Очищаем корзину после успешного оформления
            cart.items.all().delete()

        serializer = OrderReadSerializer(order, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)