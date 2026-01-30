from rest_framework import serializers
from .models import *


class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = ['id', 'user', 'created_at', 'updated_at']
        read_only_fields = ('id', 'created_at', 'updated_at')

    def create(self, validated_data):
        user = self.context['request'].user
        return Cart.objects.create(user=user, **validated_data)


class CartItemSerializer(serializers.ModelSerializer):
    total_price = serializers.DecimalField(
        max_digits=13,
        decimal_places=2,
        read_only=True,
        source='total_price'
    )

    class Meta:
        model = CartItem
        fields = ['id', 'created_at', 'updated_at', 'product', 'quantity', 'total_price']
        read_only_fields = ('id', 'created_at', 'updated_at', 'total_price')

    def create(self, validated_data):
        request = self.context['request']
        user = request.user
        cart = user.user_cart  # корзина текущего пользователя

        product = validated_data['product']
        quantity = validated_data['quantity']

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )

        if not created:
            new_quantity = cart_item.quantity + quantity

            if new_quantity > product.quantity:
                raise serializers.ValidationError({
                    'quantity': 'Общее количество товара в корзине превышает количество на складе'
                })

            cart_item.quantity = new_quantity
            cart_item.save()

        return cart_item

    def validate(self, attrs):
        product = attrs.get('product')
        quantity = attrs.get('quantity')

        if quantity > product.quantity:
            raise serializers.ValidationError({
                'quantity': 'Количество товаров в корзине не может быть больше количества на складе'
            })

        return attrs
