from django.db import models, transaction
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.conf import settings
from django.core.exceptions import ValidationError
from main.models import Product
from decimal import Decimal


class Cart(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart',           # более читаемое имя
        verbose_name='Пользователь',
    )
    created_at = (models.DateTimeField
                  (auto_now_add=True,
                   verbose_name='Создано'
                   ))
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Обновлено'
    )

    def __str__(self):
        return f"Корзина {self.user.username}"

    @property
    def total_price(self) -> Decimal:
        return sum(item.total_price for item in self.cart_items.select_related('product'))

    class Meta:
        verbose_name = "Корзина"
        verbose_name_plural = "Корзины"
        db_table = 'cart'
        ordering = ['-created_at']


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='cart_items',
        verbose_name='Товар'
    )
    quantity = models.PositiveIntegerField(
        verbose_name='Количество',
        validators=[MinValueValidator(1)]
    )
    price = models.DecimalField(               # ← важно! фиксируем цену
        verbose_name='Цена на момент добавления',
        max_digits=13,
        decimal_places=2,
        editable=False
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Товар в корзине"
        verbose_name_plural = "Товары в корзине"
        db_table = 'cart_item'
        unique_together = (('cart', 'product'),)
        ordering = ['-created_at']

    @property
    def total_price(self) -> Decimal:
        return self.price * Decimal(self.quantity)

    def clean(self):
        if self.quantity > self.product.quantity:
            raise ValidationError({
                'quantity': f'На складе только {self.product.quantity} шт.'
            })

    def save(self, *args, **kwargs):
        if not self.price:  # устанавливаем цену только при первом сохранении
            self.price = self.product.price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} × {self.quantity}"