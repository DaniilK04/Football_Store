from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings

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
        decimal_places=2
    )
    quantity = models.IntegerField(
        verbose_name='Товар на складе',
        validators=[MinValueValidator(1)]
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

class Cart(models.Model):
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
        verbose_name='Товар на складе',
        validators=[MinValueValidator(1)]
    )

    def __str__(self):
        return self.product.name

    class Meta:
        verbose_name = "Позиция в корзине"
        ordering = ["-created_at"]
        db_table = 'cart_item'
        unique_together = ('cart', 'product')


class Order(models.Model):
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
        verbose_name='Цена'
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

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    class Meta:
        verbose_name = "Позиция заказа"
        db_table = 'order_item'




