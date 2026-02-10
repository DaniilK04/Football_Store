from rest_framework import status, serializers, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from .pagination import *
from django.db import transaction
from django.db.models import F, Q

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
    pagination_class = ProductPaginateCursor

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'category__title']
    ordering_fields = ['price', 'created_at', 'name']
    ordering = ['-created_at']

    def get_queryset(self):
        qs = Product.objects.filter(is_published=True)

        # пример простого фильтра по категории через query param ?category=slug
        category_slug = self.request.query_params.get('category')
        if category_slug:
            qs = qs.filter(category__slug=category_slug)

        # можно ещё ?min_price=... &max_price=...
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        if min_price:
            qs = qs.filter(price__gte=min_price)
        if max_price:
            qs = qs.filter(price__lte=max_price)

        return qs


class OrderViewSet(ReadOnlyModelViewSet):
    """
    Просмотр своих заказов + создание заказа из корзины + отмена заказа пользователем
    + изменение статуса (только администратор)
    """
    serializer_class = OrderReadSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = ProductPaginateCursor

    def get_queryset(self):
        """
        Админ видит все заказы, пользователь — только свои
        """
        if self.request.user.is_staff:
            return Order.objects.all().prefetch_related('order_items__product')
        return Order.objects.filter(user=self.request.user).prefetch_related('order_items__product')

    def get_serializer_class(self):
        """
        Админу можно менять статус, остальным — только чтение
        """
        if self.action == 'partial_update' and self.request.user.is_staff:
            return OrderAdminUpdateSerializer
        return OrderReadSerializer

    def get_permissions(self):
        """
        partial_update — только для админов
        остальные действия — для авторизованных пользователей
        """
        if self.action in ['partial_update']:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    @action(detail=False, methods=['post'], url_path='create-from-cart')
    @transaction.atomic
    def create_from_cart(self, request):
        """
        Создание заказа из корзины с проверкой остатков и атомарным уменьшением количества
        """
        user = request.user

        try:
            cart = user.cart
        except Cart.DoesNotExist:
            return Response({"detail": "У вас нет корзины"}, status=400)

        if not cart.items.exists():
            return Response({"detail": "Корзина пуста"}, status=400)

        # Получаем ID товаров и лочим их
        product_ids = cart.items.values_list('product_id', flat=True)
        locked_products = {
            p.id: p
            for p in Product.objects.select_for_update().filter(
                id__in=product_ids,
                is_published=True
            )
        }

        order = Order.objects.create(user=user, status='new')

        for cart_item in cart.items.select_related('product'):
            product = locked_products.get(cart_item.product_id)

            if not product:
                raise serializers.ValidationError(
                    f"Товар '{cart_item.product.name}' больше недоступен или снят с публикации"
                )

            if product.quantity < cart_item.quantity:
                raise serializers.ValidationError(
                    f"Недостаточно товара '{product.name}' "
                    f"(в наличии: {product.quantity}, требуется: {cart_item.quantity})"
                )

            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=cart_item.quantity,
                # price берётся автоматически в модели OrderItem.save()
            )

            # Атомарное уменьшение остатка
            Product.objects.filter(pk=product.pk).update(
                quantity=F('quantity') - cart_item.quantity
            )

        # Успешно → чистим корзину
        cart.items.all().delete()

        serializer = OrderReadSerializer(order, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        """
        Пользователь может отменить свой заказ, если он ещё в статусе 'new' или 'processing'
        """
        order = self.get_object()

        # Проверка права на отмену
        if order.user != request.user and not request.user.is_staff:
            return Response(
                {"detail": "Вы можете отменять только свои заказы"},
                status=status.HTTP_403_FORBIDDEN
            )

        allowed_to_cancel = {'new', 'processing'}

        if order.status not in allowed_to_cancel:
            return Response(
                {
                    "detail": f"Заказ уже нельзя отменить (текущий статус: {order.get_status_display()})"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            order.status = 'canceled'
            order.save(update_fields=['status'])

            # Опционально: вернуть товары на склад (раскомментируй, если нужно)
            # for item in order.order_items.select_for_update():
            #     Product.objects.filter(pk=item.product_id).update(
            #         quantity=F('quantity') + item.quantity
            #     )

        serializer = OrderReadSerializer(order, context={'request': request})
        return Response({
            "detail": "Заказ успешно отменён",
            "order": serializer.data
        })