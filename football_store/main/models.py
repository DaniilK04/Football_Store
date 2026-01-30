from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from .validators import *
from django.db.models import Sum, F, DecimalField

class Category(models.Model):
    """Категории товаров, например: "Футболки", "Мячи", "Аксессуары"."""
    title = models.CharField(
        verbose_name='Название',
        max_length=255,
        null=False,
        blank=False
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
        """Индекс — это структура данных в базе, которая ускоряет поиск по указанным полям.
        Представь: у тебя есть книга, и тебе нужно найти все упоминания слова "Django".
        Без индекса придётся читать каждую страницу книги.
        С индексом — как если бы у книги был алфавитный указатель слов, и поиск происходит мгновенно.
        Теперь поиск Product.objects.filter(slug='nike-shoes') будет гораздо быстрее, особенно если таблица большая.
        # с индексом:
        Product.objects.filter(title='Nike')  # база использует индекс, ищет быстро"""
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['title']),
        ]

class Product(models.Model):
    """Конкретный товар, который продаётся в магазине."""
    name = models.CharField(
        verbose_name='Название',
        max_length=255,
        null=False,
        blank=False
    )
    slug = models.SlugField(
        verbose_name='URL',
        max_length=255,
        blank=True,
        unique=True
    )
    description = models.TextField(
        verbose_name='Описание',
    )
    price = models.DecimalField(
        verbose_name='Цена',
        max_digits=13,
        decimal_places=2,
        validators=[validate_price]
    )
    quantity = models.IntegerField(
        verbose_name='Товар на складе',
        validators=[validate_quantity]
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="products",
        db_index=True,
        verbose_name='Категория',
    )
    image = models.ImageField(
        upload_to='photos/%Y/%m/%d/',
        verbose_name="Фотографии"
    )
    is_published = models.BooleanField(
        verbose_name='Опубликовано',
        default=True,
        db_index=True
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
            raise ValidationError({
                'image': 'Для публикации продукта обязательно нужно загрузить фото.'
            })


    def get_absolute_url(self):
        return reverse('product', kwargs={'slug': self.slug})

    def __str__(self):
        return self.name

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

    class Meta:
        verbose_name = "Продукт"
        verbose_name_plural = "Продукты"
        ordering = ["-created_at"]
        db_table = 'product'
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['name']),
        ]


class Order(models.Model):
    """Заказ, который пользователь оформляет."""
    ORDER_CHOISE = (
        ('New', 'Новый'),
        ('Processing', 'В процессе'),
        ('Shipped', 'Отправлено'),
        ('Completed', 'Завершено'),
        ('Canceled', 'Отменено')
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_order',
        db_index=True,
        verbose_name='Пользователь',
    )
    status = models.CharField(
        verbose_name='Статус',
        choices=ORDER_CHOISE,
        default='Processing',
    )
    total_price = models.DecimalField(
        max_digits=13,
        decimal_places=2,
        verbose_name='Цена',
        default=0
    )
    created_at = models.DateTimeField(
        verbose_name='Дата создания',
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )
    items = models.ManyToManyField(
        Product,
        through='OrderItem',
        related_name='orders'
    )
    def recalculate_total_price(self):
        total = self.order_items.aggregate(
            total=Sum(
                F('price') * F('quantity'),
                output_field=DecimalField()
            )
        )['total'] or 0

        self.total_price = total
        self.save(update_fields=['total_price'])

    def __str__(self):
        return f"Заказ #{self.pk} пользователя {self.user.username} ({self.status})"

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ["-created_at"]
        db_table = 'order'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]

class OrderItem(models.Model):
    """Конкретный товар в конкретном заказе."""
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="order_items",
        verbose_name='Заказ',
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='product_order',
        verbose_name='Продукт',
    )
    quantity = models.IntegerField(
        verbose_name='Количество',
        validators=[MinValueValidator(1)]
    )
    price = models.DecimalField(
        verbose_name='Цена',
        max_digits=13,
        decimal_places=2
    )

    @property
    def total_price(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    class Meta:
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиция заказов"
        db_table = 'order_item'
        unique_together = ('order', 'product')




