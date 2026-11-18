
from django.urls import path
from . import views

urlpatterns = [
    path('', views.welcome, name='welcome'),

    path('dashboard/', views.product_list, name='dashboard'),
    path('dashboard/', views.product_list, name='product_list'),

    path('product/<int:product_id>/', views.product_detail, name='product_detail'),

    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:product_id>/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),

    path('checkout/', views.checkout, name='checkout'),
    path('payment/<int:order_id>/', views.initiate_payment, name='initiate_payment'),
    path('verify-payment/<int:order_id>/', views.verify_payment, name='verify_payment'),
    path('order-success/<int:order_id>/', views.order_success, name='order_success'),

    path('register/', views.register, name='register'),
    path('login/', views.customer_login, name='login'),
    path('logout/', views.customer_logout, name='logout'),
]
