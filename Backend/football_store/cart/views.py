from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, DestroyModelMixin
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db import transaction
from django.db.models import F
from .models import Cart, CartItem
from .serializers import CartDetailSerializer, CartItemSerializer
from main.models import Product
from .pagination import CartPaginateCursor


class CartViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    """
    Работа с корзиной пользователя:
    - получение корзины (list / retrieve — одно и то же)
    - summary (итог)
    - очистка
    """
    serializer_class = CartDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        return cart

    def list(self, request, *args, **kwargs):
        # list и retrieve — одно и то же, т.к. корзина одна
        cart = self.get_object()
        serializer = self.get_serializer(cart)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """ Лёгкий endpoint: сумма + количество позиций """
        cart = self.get_object()
        return Response({
            'total_price': str(cart.total_price),  # Decimal → str для JSON
            'items_count': cart.items.count(),
        })

    @action(detail=False, methods=['post', 'delete'], url_path='clear')
    def clear(self, request):
        """ Очистить корзину (теперь без pk) """
        cart = self.get_object()
        cart.items.all().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CartItemViewSet(ModelViewSet):
    """
    Управление отдельными позициями в корзине:
    - добавление (POST /item/add/)
    - изменение количества (PATCH /item/<id>/)
    - удаление (DELETE /item/<id>/)
    - список (GET /item/)
    """
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CartPaginateCursor

    def get_queryset(self):
        return CartItem.objects.filter(
            cart__user=self.request.user
        ).select_related('product')

    def perform_destroy(self, instance):
        """ При удалении позиции — опционально вернуть товар на склад """
        with transaction.atomic():
            # Раскомментировать, если нужно восстанавливать остаток при удалении из корзины
            # product = Product.objects.select_for_update().get(pk=instance.product.pk)
            # product.quantity = F('quantity') + instance.quantity
            # product.save(update_fields=['quantity'])

            instance.delete()

    @action(detail=False, methods=['post'], url_path='add')
    def add(self, request):
        """ Добавление товара в корзину """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cart_item = serializer.save()

        # Возвращаем **всю** корзину — удобно для фронтенда
        cart_serializer = CartDetailSerializer(
            cart_item.cart,
            context={'request': request}
        )
        return Response(cart_serializer.data, status=status.HTTP_201_CREATED)