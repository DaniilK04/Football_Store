from django.contrib import admin
from .models import Cart, CartItem

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 1
    readonly_fields = ('display_total_price',)
    autocomplete_fields = ('product',)

    def display_total_price(self, obj):
        return obj.total_price

    display_total_price.short_description = "Общая цена"

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'created_at',
        'display_total_price',
        'updated_at'
    )
    search_fields = ('user__username',)
    inlines = [CartItemInline]
    readonly_fields = ('id', 'display_total_price',)
    autocomplete_fields = ('user',)

    def display_total_price(self, obj):
        return obj.total_price

    display_total_price.short_description = "Общая цена"

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'cart',
        'product',
        'quantity',
        'display_total_price',
        'created_at'
    )
    list_filter = ('cart',)
    readonly_fields = ('id', 'display_total_price')
    search_fields = ('product__name',)
    autocomplete_fields = ('cart', 'product')

    def display_total_price(self, obj):
        return obj.total_price

    display_total_price.short_description = "Общая цена"

