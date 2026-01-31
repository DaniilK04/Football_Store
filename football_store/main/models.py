from django.db import models, transaction
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.urls import reverse
from django.core.validators import MinValueValidator
from django.conf import settings
from django.db.models import Sum, F, DecimalField
from decimal import Decimal
from rest_framework.exceptions import ValidationError
from .validators import validate_price, validate_quantity  # предполагаем, что они есть


class Category(models.Model):
    title = models.CharField(
        verbose_name='Название',
        max_length=255
    )
    slug = models.SlugField(
        verbose_name='URL',
        max_length=255,
        blank=True,
        unique=True
    )
    created_at = models.DateTimeField(
        verbose_name='Дата создания',
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title, allow_unicode=True)
            slug = base_slug
            counter = 1
            while Category.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('category', kwargs={'slug': self.slug})

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ["-created_at"]
        db_table = 'category'
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['title']),
        ]


class Product(models.Model):
    name = models.CharField(
        verbose_name='Название',
        max_length=255
    )
    slug = (models.SlugField
            (
        verbose_name='URL',
        max_length=255,
        blank=True,
        unique=True
    ))
    description = models.TextField(
        verbose_name='Описание',
        blank=True
    )
    price = models.DecimalField(
        verbose_name='Цена',
        max_digits=13,
        decimal_places=2,
        validators=[validate_price]
    )
    quantity = models.PositiveIntegerField(
        verbose_name='Товар на складе',
        default=0,
        validators=[validate_quantity]
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="products",
        db_index=True
    )
    image = models.ImageField(
        upload_to='photos/%Y/%m/%d/',
        verbose_name="Фотография",
        blank=True,
        null=True
    )
    is_published = models.BooleanField(
        verbose_name='Опубликовано',
        default=False
        , db_index=True
    )
    created_at = models.DateTimeField(
        verbose_name='Дата создания',
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )

    def clean(self):
        if self.is_published and not self.image:
            raise ValidationError(
                {'image': 'Для публикации продукта обязательно нужно загрузить фото.'}
            )

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name, allow_unicode=True)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('product', kwargs={'slug': self.slug})

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Продукт"
        verbose_name_plural = "Продукты"
        ordering = ["-created_at"]
        db_table = 'product'
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['name']),
            models.Index(fields=['is_published']),
        ]


class Order(models.Model):
    ORDER_STATUS = (
        ('new', 'Новый'),
        ('processing', 'В обработке'),
        ('shipped', 'Отправлен'),
        ('completed', 'Завершён'),
        ('canceled', 'Отменён'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name='Пользователь'
    )
    status = models.CharField(
        verbose_name='Статус',
        max_length=20,
        choices=ORDER_STATUS,
        default='new'
    )
    created_at = models.DateTimeField(verbose_name='Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    items = models.ManyToManyField(
        Product,
        through='OrderItem',
        related_name='orders'
    )

    @property
    def total_price(self) -> Decimal:
        result = self.order_items.aggregate(
            total=Sum(
                F('price') * F('quantity'),
                output_field=DecimalField(max_digits=13, decimal_places=2)
            )
        )['total']
        return result if result is not None else Decimal('0.00')

    def __str__(self):
        return f"Заказ #{self.pk} — {self.user.username} ({self.get_status_display()})"

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ["-created_at"]
        db_table = 'order'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['user']),
        ]

class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="order_items"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='order_items'
    )
    quantity = models.PositiveIntegerField(
        verbose_name='Количество',
        validators=[MinValueValidator(1)]
    )
    price = models.DecimalField(
        verbose_name='Цена на момент заказа',
        max_digits=13,
        decimal_places=2
    )

    class Meta:
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказов"
        db_table = 'order_item'
        unique_together = ('order', 'product')

    @property
    def total_price(self) -> Decimal:
        return self.price * Decimal(self.quantity)

    def __str__(self):
        return f"{self.product.name} × {self.quantity}"