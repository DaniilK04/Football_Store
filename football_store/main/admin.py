from django.contrib import admin
from .models import Category, Product, Cart, CartItem, Order, OrderItem

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 1
    readonly_fields = ('total_price',)
    autocomplete_fields = ('product',)

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    readonly_fields = ('price',)
    autocomplete_fields = ('product',)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'title',
        'slug',
        'created_at',
        'updated_at'
    )
    readonly_fields = ('id',)
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title',)
    list_filter = ('created_at',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'category',
        'price',
        'quantity',
        'is_published',
        'created_at'
    )
    list_editable = (
        'price',
        'quantity',
        'is_published'
    )
    list_filter = (
        'category',
        'is_published',
        'created_at'
    )
    search_fields = (
        'name',
        'description'
    )
    prepopulated_fields = {'slug': ('name',)}
    autocomplete_fields = ('category',)

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

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'status',
        'total_price',
        'created_at',
        'updated_at'
    )
    list_editable = ('status',)
    readonly_fields = ('id',)
    list_filter = (
        'status',
        'created_at'
    )
    search_fields = (
        'user__username',
        'id'
    )
    inlines = [OrderItemInline]
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

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'order',
        'product',
        'quantity',
        'price'
    )
    list_filter = ('order',)
    readonly_fields = ('id', 'price')
    search_fields = ('product__name',)
    autocomplete_fields = ('order', 'product')
