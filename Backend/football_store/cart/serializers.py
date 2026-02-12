from rest_framework import serializers
from django.db import transaction
from .models import Cart, CartItem
from main.models import Product
from main.serializers import ProductSerializer


class CartItemSerializer(serializers.ModelSerializer):
    product = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Product.objects.filter(is_published=True),
        write_only=True
    )

    product_detail = ProductSerializer(
        source='product',
        read_only=True
    )

    total_price = serializers.DecimalField(
        max_digits=13,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = CartItem
        fields = [
            'id',
            'product',
            'product_detail',
            'quantity',
            'price',
            'total_price',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'price', 'total_price', 'created_at', 'updated_at']

    def create(self, validated_data):
        request = self.context['request']
        user = request.user
        product = validated_data['product']
        quantity = validated_data['quantity']

        with transaction.atomic():
            product = Product.objects.select_for_update().get(pk=product.pk)

            if product.quantity < quantity:
                raise serializers.ValidationError(
                    {'quantity': f'На складе только {product.quantity} шт.'}
                )

            cart, _ = Cart.objects.get_or_create(user=user)

            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                defaults={'quantity': quantity, 'price': product.price}
            )

            if not created:
                cart_item.quantity += quantity
                cart_item.save()

        return cart_item


class CartDetailSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.DecimalField(
        max_digits=13,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = Cart
        fields = ['id', 'total_price', 'items', 'created_at', 'updated_at']
