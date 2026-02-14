from rest_framework import serializers
from django.db import transaction
from .models import Category, Product, Order, OrderItem
from cart.models import Cart, CartItem


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'title', 'slug', 'created_at', 'updated_at']
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']


class ProductSerializer(serializers.ModelSerializer):
    # Добавляем slug категории
    category_slug = serializers.SlugRelatedField(
        source='category',
        read_only=True,
        slug_field='slug'
    )

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'price', 'quantity',
            'category', 'category_slug', 'image', 'is_published', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']


# ─── Order ──────────────────────────────────────────────────────

class OrderItemReadSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_slug = serializers.CharField(source='product.slug', read_only=True)
    product_image = serializers.ImageField(source='product.image', read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            'id',
            'product_name',
            'product_slug',
            'product_image',
            'quantity',
            'price',
            'total_price'
        ]
        read_only_fields = fields



class OrderReadSerializer(serializers.ModelSerializer):
    items = OrderItemReadSerializer(
        source='order_items',   # 👈 ВАЖНО
        many=True,
        read_only=True
    )
    username = serializers.CharField(source='user.username', read_only=True)
    total_price = serializers.DecimalField(max_digits=13, decimal_places=2, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id',
            'username',
            'status',
            'total_price',
            'created_at',
            'updated_at',
            'items'
        ]
        read_only_fields = fields



class OrderAdminUpdateSerializer(serializers.ModelSerializer):
    """ Только для изменения статуса администратором """
    class Meta:
        model = Order
        fields = ['status']
        extra_kwargs = {
            'status': {'required': True}
        }