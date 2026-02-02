from django.shortcuts import render, get_object_or_404
from django.template.context_processors import request
from rest_framework.viewsets import *
from rest_framework import *
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import *
from .models import *
from .serializers import *

class CategoryViewSet(ModelViewSet):
    """Класс для категорий товаров, для всех и для одной категории"""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    # По какому полю искать объект при retrieve()
    # lookup_field = 'slug' → /categories/football/ вместо /categories/5/
    lookup_field = 'slug'
    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter
    ]
    filterset_fields = ['title'] # фильтр по точному совпадению
    search_fields = ['title'] # поиск по названию
    ordering_fields = ['created_at'] # по каким полям можно сортировать
    ordering = ['-created_at']  # по умолчанию новые сверху

    def get_permissions(self):
        # Строка, которая говорит:
        # КАКОЕ действие сейчас выполняет ViewSet. DRF сам её проставляет.
        # Типа если действия с таблицей, просмотр всех категорий(списка) и просмотр одной категории(детальной), то
        # это роль будет пользователя, иначе роль будет админа, для(POST, PUT, DELETE И др) запросов.
        if self.action in ['list', 'retrieve']:
            return [AllowAny()] # какой пользователь может смотреть(любой или авторизованный)
        return [IsAdminUser()]


class ProductViewSet(ModelViewSet):
    serializer_class = ProductSerializer
    lookup_field = 'slug'
    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter
    ]
    filterset_fields = ['name']  # фильтр по точному совпадению
    search_fields = ['name']  # поиск по названию
    ordering_fields = ['created_at']  # по каким полям можно сортировать
    ordering = ['-created_at']  # по умолчанию новые сверху


    def get_queryset(self):
        return Product.objects.filter(is_published=True)

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAdminUser()]


class OrderViewSetRead(ModelViewSet):
    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter
    ]
    search_fields = ['order_items__product__name']  # поиск по названию
    ordering_fields = ['status']  # по каким полям можно сортировать
    ordering = ['-created_at']  # по умолчанию новые сверху
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """«Когда я получаю заказы (Order), сразу заранее подтяни
            все OrderItem этого заказа и связанные с ними Product
            одним дополнительным запросом, а не по одному на каждый объект».
            Что значит 'order_items__product'
            Разберём по цепочке:
            Order
             └── order_items (related_name у OrderItem)
                  └── product (ForeignKey на Product)
            order_items — связь Order → OrderItem
            __product — связь OrderItem → Product"""
        return Order.objects.filter(user=self.request.user).prefetch_related(
            'order_items__product')

    def get_serializer_class(self):
        # Можно разделить на лёгкий список и полный детальный просмотр
        if self.action == 'retrieve':
            # Если хотите более подробный вывод — создайте OrderDetailSerializer
            return OrderReadSerializer
        # для списка — можно оставить тот же или сделать облегчённый вариант
        return OrderReadSerializer





