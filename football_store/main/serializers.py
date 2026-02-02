from rest_framework import serializers
from django.db import transaction
from decimal import Decimal
from .models import Category, Product, Order, OrderItem
import re

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'title', 'slug', 'created_at', 'updated_at']
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']

    def validate_title(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Название не может быть пустым")
        if len(value) < 2:
            raise serializers.ValidationError("Название слишком короткое (минимум 2 символа)")
        if re.search(r'[<>#@!$%^&*]', value):
            raise serializers.ValidationError("Название содержит недопустимые символы")
        return value


class ProductSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Category.objects.all(),
        required=False
    )
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'price', 'quantity',
            'category', 'image', 'is_published', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']

    def validate(self, data):
        # Проверяем при создании и обновлении
        is_published = data.get('is_published', getattr(self.instance, 'is_published', False))
        image = data.get('image', getattr(self.instance, 'image', None))

        if is_published and not image:
            raise serializers.ValidationError({
                'image': 'Для публикации продукта обязательно нужно загрузить фото.'
            })
        return data

    def validate_image(self, value):
        if value:
            valid_extensions = ['jpg', 'jpeg', 'png']
            ext = value.name.split('.')[-1].lower()
            if ext not in valid_extensions:
                raise serializers.ValidationError(
                    f"Недопустимый формат. Допустимые: {', '.join(valid_extensions)}"
                )
            if value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError("Изображение не должно превышать 5 МБ")
        return value


# ─── Для чтения ────────────────────────────────────────────────

class OrderItemDetailSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_slug = serializers.CharField(source='product.slug', read_only=True)
    total_price = serializers.DecimalField(max_digits=13, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product_name', 'product_slug', 'quantity', 'price', 'total_price']


class OrderReadSerializer(serializers.ModelSerializer):
    items = OrderItemDetailSerializer(many=True, read_only=True)
    total_price = serializers.DecimalField(max_digits=13, decimal_places=2, read_only=True, source='total_price')
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'username', 'status', 'total_price',
            'created_at', 'updated_at', 'items'
        ]
        read_only_fields = fields


# ─── Для создания заказа ───────────────────────────────────────

class OrderItemCreateSerializer(serializers.ModelSerializer):
    product = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Product.objects.filter(is_published=True)
    )

    class Meta:
        model = OrderItem
        fields = ['product', 'quantity']


class OrderCreateSerializer(serializers.ModelSerializer):
    items = OrderItemCreateSerializer(
        many=True,
        write_only=True
    )

    class Meta:
        model = Order
        fields = ['items']

    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError("Заказ не может быть пустым")
        return items

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        user = self.context['request'].user

        with transaction.atomic():
            order = Order.objects.create(user=user, status='new')

            for item_data in items_data:
                product = item_data['product']
                quantity = item_data['quantity']

                if product.quantity < quantity:
                    raise serializers.ValidationError(
                        f"Недостаточно товара '{product.name}' на складе "
                        f"(в наличии: {product.quantity}, требуется: {quantity})"
                    )

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    price=product.price
                )

                # уменьшаем остаток
                product.quantity -= quantity
                product.save(update_fields=['quantity'])

        return order