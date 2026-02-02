from django.shortcuts import render, get_object_or_404
from rest_framework.viewsets import *
from rest_framework import *
from rest_framework.permissions import AllowAny, IsAdminUser
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


