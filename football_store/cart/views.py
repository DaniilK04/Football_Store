from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from rest_framework.mixins import RetrieveModelMixin, DestroyModelMixin
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.shortcuts import get_object_or_404
from .models import Cart, CartItem
from .serializers import CartDetailSerializer, CartItemSerializer
from main.models import Product


class CartViewSet(RetrieveModelMixin, GenericViewSet):
    serializer_class = CartDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        return cart

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """ Только итоговая сумма и количество позиций """
        cart = self.get_object()
        return Response({
            'total_price': cart.total_price,
            'items_count': cart.items.count(),
        })

    @action(detail=True, methods=['post', 'delete'])
    def clear(self, request, pk=None):
        """ Очистить корзину """
        cart = self.get_object()
        cart.items.all().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CartItemViewSet(ModelViewSet):
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CartItem.objects.filter(
            cart__user=self.request.user
        ).select_related('product')

    def perform_destroy(self, instance):
        with transaction.atomic():
            # Если у тебя есть механизм резервирования — здесь можно вернуть количество
            # product = Product.objects.select_for_update().get(pk=instance.product_id)
            # product.quantity += instance.quantity
            # product.save(update_fields=['quantity'])
            instance.delete()

    @action(detail=False, methods=['post'], url_path='add')
    def add(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = serializer.save()
        # Можно вернуть полную корзину после добавления (удобно для фронта)
        cart_serializer = CartDetailSerializer(serializer.instance.cart, context={'request': request})
        return Response(cart_serializer.data, status=status.HTTP_201_CREATED)
