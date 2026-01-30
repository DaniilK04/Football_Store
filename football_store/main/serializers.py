from rest_framework import serializers
from .models import *
import re

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'title', 'created_at', 'updated_at', 'slug']
        read_only_fields = ('id', 'slug', 'created_at', 'updated_at')

    def validate_title(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Название не может быть пустым")

        if len(value) < 3:
            raise serializers.ValidationError("Название слишком короткое")

        if re.search(r'[<>#@!$%^&*]', value):
            raise serializers.ValidationError("Название содержит недопустимые символы")

        if value.isupper():
            raise serializers.ValidationError("Название не должно быть полностью заглавными буквами")
        return value


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'description', 'price', 'quantity',
                  'category', 'image', 'is_published',
                  'created_at', 'updated_at']

        read_only_fields = ('id', 'slug', 'created_at', 'updated_at')

    def validate_image(self, value):
        # Если продукт опубликован, изображение обязательно
        is_published = self.initial_data.get('is_published', getattr(self.instance, 'is_published', False))
        if is_published and not value:
            raise serializers.ValidationError("Для публикации продукта обязательно нужно загрузить фото.")

        # Проверка формата файла
        if value:
            valid_extensions = ['jpg', 'jpeg', 'png']
            ext = value.name.split('.')[-1].lower()
            if ext not in valid_extensions:
                raise serializers.ValidationError(f"Недопустимый формат изображения. Допустимые: {', '.join(valid_extensions)}")

            # Проверка размера файла (например, 5 МБ)
            max_size = 5 * 1024 * 1024  # 5MB
            if value.size > max_size:
                raise serializers.ValidationError("Размер изображения не должен превышать 5 МБ")

        return value


class OrderSerializer(serializers.ModelSerializer):
    total_price = serializers.DecimalField(
        source='total_price',
        max_digits=13,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = Order
        fields = ['id', 'user', 'status',
                  'total_price', 'created_at',
                  'updated_at', 'items']
        read_only_fields = ('id', 'user',
                            'created_at',
                            'updated_at', 'total_price',)

    def create(self, validated_data):
        user = self.context['request'].user
        return Order.objects.create(user=user, **validated_data)





