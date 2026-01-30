from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.conf import settings
from django.core.exceptions import ValidationError
from main.models import Product

class Cart(models.Model):
    """Корзина пользователя — каждый пользователь имеет одну корзину."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_cart',
        db_index=True,
        verbose_name='Пользователь',
    )
    created_at = models.DateTimeField(
        verbose_name='Дата создания',
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )

    def __str__(self):
        return f"Корзина пользователя {self.user.username}"

    class Meta:
        verbose_name = "Корзина"
        verbose_name_plural = "Корзины"
        ordering = ["-created_at"]
        db_table = 'cart'

class CartItem(models.Model):
    """Одна строка в корзине, содержит товар и его количество."""
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="cart_items",
        verbose_name='Корзина',
    )
    created_at = models.DateTimeField(
        verbose_name='Дата создания',
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='product_cart',
        verbose_name='Продукт',
    )
    quantity = models.IntegerField(
        verbose_name='Количество товара',
        validators=[MinValueValidator(1)]
    )

    def clean(self):
        if self.quantity > self.product.quantity:
            raise ValidationError({
                'quantity': 'Количество товаров в корзине не может быть больше количества товара на складе'
            })

    @property
    def total_price(self):
        return self.quantity * self.product.price

    def __str__(self):
        return self.product.name

    class Meta:
        verbose_name = "Позиция в корзине"
        verbose_name_plural = "Позиция в корзине"
        ordering = ["-created_at"]
        db_table = 'cart_item'
        unique_together = ('cart', 'product')