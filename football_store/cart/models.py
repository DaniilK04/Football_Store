from django.db import models, transaction
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.conf import settings
from django.core.exceptions import ValidationError
from main.models import *
from decimal import Decimal


class Cart(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart',
        verbose_name='Пользователь',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Создано'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Обновлено'
    )

    def __str__(self):
        return f"Корзина {self.user.username}"

    @property
    def total_price(self) -> Decimal:
        # Защищаемся от битых/несохранённых CartItem
        total = Decimal('0.00')
        for item in self.items.select_related('product'):
            try:
                total += item.total_price
            except (TypeError, AttributeError):
                pass  # пропускаем проблемные строки, чтобы админка не падала
        return total

    class Meta:
        verbose_name = "Корзина"
        verbose_name_plural = "Корзины"
        db_table = 'cart'
        ordering = ['-created_at']


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Корзина'
    )
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
    price = models.DecimalField(
        verbose_name='Цена на момент добавления',
        max_digits=13,
        decimal_places=2,
        editable=False,
        default=Decimal('0.00'),           # ← важно для админки и новых экземпляров
        null=False,
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
        """Безопасное вычисление суммы позиции"""
        if self.price is None or self.quantity is None:
            return Decimal('0.00')
        return self.price * Decimal(self.quantity)

    def clean(self):
        if self.quantity > self.product.quantity:
            raise ValidationError({
                'quantity': f'На складе только {self.product.quantity} шт.'
            })

    def save(self, *args, **kwargs):
        if self.price is None or self.price == Decimal('0.00'):
            # устанавливаем цену только если она не задана
            if hasattr(self, 'product') and self.product_id:
                self.price = self.product.price
            else:
                self.price = Decimal('0.00')  # fallback
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} × {self.quantity}"