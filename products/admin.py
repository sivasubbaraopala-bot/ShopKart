
from django.contrib import admin

from .models import Product, Order, OrderItem


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'name',
        'price',
        'stock',
        'created_at'
    )

    search_fields = ('name', 'description')

    list_filter = ('created_at',)


class OrderItemInline(admin.TabularInline):

    model = OrderItem
    extra = 0
    readonly_fields = (
        'product_name',
        'unit_price',
        'quantity',
        'subtotal'
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'customer_name',
        'phone',
        'total_amount',
        'status',
        'created_at'
    )

    search_fields = (
        'customer_name',
        'phone',
        'email'
    )

    list_filter = (
        'status',
        'created_at'
    )

    inlines = [OrderItemInline]
