from django.contrib import admin
from .models import Cart, CartItem

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 1
    readonly_fields = ('total_price',)
    autocomplete_fields = ('product',)

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'created_at',
        'updated_at'
    )
    search_fields = ('user__username',)
    inlines = [CartItemInline]
    autocomplete_fields = ('user',)

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'cart',
        'product',
        'quantity',
        'total_price',
        'created_at'
    )
    list_filter = ('cart',)
    readonly_fields = ('id', 'total_price')
    search_fields = ('product__name',)
    autocomplete_fields = ('cart', 'product')
