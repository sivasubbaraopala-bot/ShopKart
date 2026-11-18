
import razorpay

from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from .models import Product, Order, OrderItem
from .forms import RegisterForm


# --------------------------------------------------
# 1. WELCOME PAGE
# --------------------------------------------------

def welcome(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    return render(request, 'products/welcome.html')


# --------------------------------------------------
# 2. CUSTOMER REGISTRATION
# --------------------------------------------------

def register(request):

    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':

        form = RegisterForm(request.POST)

        if form.is_valid():

            form.save()

            messages.success(
                request,
                'Account created successfully. Please login.'
            )

            return redirect('login')

    else:
        form = RegisterForm()

    return render(
        request,
        'products/register.html',
        {'form': form}
    )


# --------------------------------------------------
# 3. CUSTOMER LOGIN
# --------------------------------------------------

def customer_login(request):

    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':

        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            login(request, user)

            messages.success(
                request,
                f'Welcome {user.username}!'
            )

            return redirect('dashboard')

        else:

            messages.error(
                request,
                'Invalid customer name or password.'
            )

    return render(request, 'products/login.html')


# --------------------------------------------------
# 4. CUSTOMER LOGOUT
# --------------------------------------------------

@login_required
def customer_logout(request):

    logout(request)

    messages.success(
        request,
        'You have been logged out successfully.'
    )

    return redirect('welcome')


# --------------------------------------------------
# 5. PRODUCT DASHBOARD
# --------------------------------------------------

def product_list(request):

    products = Product.objects.all().order_by('-created_at')

    query = request.GET.get('q', '').strip()

    if query:

        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )

    cart = request.session.get('cart', {})

    cart_count = sum(
        int(quantity) for quantity in cart.values()
    )

    context = {
        'products': products,
        'query': query,
        'cart_count': cart_count,
    }

    return render(
        request,
        'products/product_list.html',
        context
    )


# --------------------------------------------------
# 6. PRODUCT DETAILS
# --------------------------------------------------

def product_detail(request, product_id):

    product = get_object_or_404(
        Product,
        id=product_id
    )

    cart = request.session.get('cart', {})

    cart_count = sum(
        int(quantity) for quantity in cart.values()
    )

    context = {
        'product': product,
        'cart_count': cart_count,
    }

    return render(
        request,
        'products/product_detail.html',
        context
    )


# --------------------------------------------------
# 7. ADD PRODUCT TO CART
# --------------------------------------------------

def add_to_cart(request, product_id):

    product = get_object_or_404(
        Product,
        id=product_id
    )

    if request.method == 'POST':
        quantity = request.POST.get('quantity', '1')
    else:
        quantity = request.GET.get('quantity', '1')

    try:
        quantity = int(quantity)
    except (ValueError, TypeError):
        quantity = 1

    if quantity < 1:
        quantity = 1

    if product.stock < 1:

        messages.error(
            request,
            'This product is out of stock.'
        )

        return redirect('dashboard')

    cart = request.session.get('cart', {})

    product_id_string = str(product_id)

    current_quantity = int(
        cart.get(product_id_string, 0)
    )

    new_quantity = current_quantity + quantity

    if new_quantity > product.stock:

        messages.error(
            request,
            f'Only {product.stock} items are available.'
        )

        return redirect('dashboard')

    cart[product_id_string] = new_quantity

    request.session['cart'] = cart

    messages.success(
        request,
        f'{product.name} added to cart.'
    )

    return redirect('cart_detail')


# --------------------------------------------------
# 8. VIEW CART
# --------------------------------------------------

def cart_detail(request):

    cart = request.session.get('cart', {})

    cart_items = []

    total = Decimal('0.00')

    for product_id, quantity in cart.items():

        product = Product.objects.filter(
            id=product_id
        ).first()

        if product is None:
            continue

        quantity = int(quantity)

        subtotal = product.price * quantity

        cart_items.append({
            'product': product,
            'quantity': quantity,
            'subtotal': subtotal,
        })

        total += subtotal

    cart_count = sum(
        int(quantity) for quantity in cart.values()
    )

    context = {
        'cart_items': cart_items,
        'total': total,
        'cart_count': cart_count,
    }

    return render(
        request,
        'products/cart.html',
        context
    )


# --------------------------------------------------
# 9. UPDATE CART QUANTITY
# --------------------------------------------------

@require_POST
def update_cart(request, product_id):

    product = get_object_or_404(
        Product,
        id=product_id
    )

    cart = request.session.get('cart', {})

    product_id_string = str(product_id)

    if product_id_string not in cart:
        return redirect('cart_detail')

    try:
        quantity = int(
            request.POST.get('quantity', 1)
        )
    except (ValueError, TypeError):
        quantity = 1

    if quantity <= 0:

        cart.pop(product_id_string, None)

        messages.success(
            request,
            'Product removed from cart.'
        )

    elif quantity > product.stock:

        messages.error(
            request,
            f'Only {product.stock} items are available.'
        )

    else:

        cart[product_id_string] = quantity

        messages.success(
            request,
            'Cart quantity updated.'
        )

    request.session['cart'] = cart

    return redirect('cart_detail')


# --------------------------------------------------
# 10. REMOVE PRODUCT FROM CART
# --------------------------------------------------

def remove_from_cart(request, product_id):

    cart = request.session.get('cart', {})

    product_id_string = str(product_id)

    if product_id_string in cart:

        del cart[product_id_string]

        request.session['cart'] = cart

        messages.success(
            request,
            'Product removed from cart.'
        )

    return redirect('cart_detail')


# --------------------------------------------------
# 11. CHECKOUT
# --------------------------------------------------

def checkout(request):

    cart = request.session.get('cart', {})

    if not cart:

        messages.error(
            request,
            'Your cart is empty.'
        )

        return redirect('cart_detail')

    cart_items = []

    total = Decimal('0.00')

    for product_id, quantity in cart.items():

        product = Product.objects.filter(
            id=product_id
        ).first()

        if product is None:
            continue

        quantity = int(quantity)

        if quantity < 1 or quantity > product.stock:

            messages.error(
                request,
                f'Insufficient stock for {product.name}.'
            )

            return redirect('cart_detail')

        subtotal = product.price * quantity

        cart_items.append({
            'product': product,
            'quantity': quantity,
            'subtotal': subtotal,
        })

        total += subtotal

    if not cart_items:

        messages.error(
            request,
            'No valid products found in your cart.'
        )

        return redirect('cart_detail')

    if request.method == 'POST':

        customer_name = request.POST.get(
            'customer_name', ''
        ).strip()

        phone = request.POST.get(
            'phone', ''
        ).strip()

        email = request.POST.get(
            'email', ''
        ).strip()

        address = request.POST.get(
            'address', ''
        ).strip()

        city = request.POST.get(
            'city', ''
        ).strip()

        state = request.POST.get(
            'state', ''
        ).strip()

        postal_code = request.POST.get(
            'postal_code', ''
        ).strip()

        if not all([
            customer_name,
            phone,
            address,
            city,
            state,
            postal_code
        ]):

            messages.error(
                request,
                'Please fill all required checkout fields.'
            )

        else:

            try:

                with transaction.atomic():

                    # Check stock again before creating order
                    for item in cart_items:

                        product = Product.objects.select_for_update().get(
                            id=item['product'].id
                        )

                        if item['quantity'] > product.stock:

                            raise ValueError(
                                f'Insufficient stock for {product.name}.'
                            )

                    order = Order.objects.create(
                        customer_name=customer_name,
                        phone=phone,
                        email=email,
                        address=address,
                        city=city,
                        state=state,
                        postal_code=postal_code,
                        total_amount=total,
                        status='Pending',
                    )

                    for item in cart_items:

                        OrderItem.objects.create(
                            order=order,
                            product=item['product'],
                            product_name=item['product'].name,
                            unit_price=item['product'].price,
                            quantity=item['quantity'],
                            subtotal=item['subtotal'],
                        )

                return redirect(
                    'initiate_payment',
                    order_id=order.id
                )

            except ValueError as error:

                messages.error(request, str(error))

    context = {
        'cart_items': cart_items,
        'total': total,
    }

    return render(
        request,
        'products/checkout.html',
        context
    )


# --------------------------------------------------
# 12. RAZORPAY PAYMENT
# --------------------------------------------------

def initiate_payment(request, order_id):

    order = get_object_or_404(
        Order,
        id=order_id
    )

    if order.status == 'Paid':

        return redirect(
            'order_success',
            order_id=order.id
        )

    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:

        messages.error(
            request,
            'Razorpay API keys are not configured.'
        )

        return redirect('checkout')

    try:

        client = razorpay.Client(
            auth=(
                settings.RAZORPAY_KEY_ID,
                settings.RAZORPAY_KEY_SECRET
            )
        )

        payment_data = {
            'amount': int(order.total_amount * 100),
            'currency': 'INR',
            'receipt': f'order_{order.id}',
        }

        razorpay_order = client.order.create(
            data=payment_data
        )

        order.razorpay_order_id = razorpay_order['id']

        order.save(
            update_fields=['razorpay_order_id']
        )

        context = {
            'order': order,
            'razorpay_order_id': razorpay_order['id'],
            'razorpay_key_id': settings.RAZORPAY_KEY_ID,
            'amount': int(order.total_amount * 100),
            'currency': 'INR',
        }

        return render(
            request,
            'products/payment.html',
            context
        )

    except Exception:

        messages.error(
            request,
            'Unable to start payment. Please try again.'
        )

        return redirect('checkout')


# --------------------------------------------------
# 13. VERIFY RAZORPAY PAYMENT
# --------------------------------------------------

@require_POST
def verify_payment(request, order_id):

    order = get_object_or_404(
        Order,
        id=order_id
    )

    razorpay_payment_id = request.POST.get(
        'razorpay_payment_id'
    )

    razorpay_order_id = request.POST.get(
        'razorpay_order_id'
    )

    razorpay_signature = request.POST.get(
        'razorpay_signature'
    )

    if not all([
        razorpay_payment_id,
        razorpay_order_id,
        razorpay_signature
    ]):

        messages.error(
            request,
            'Payment details are missing.'
        )

        return redirect('checkout')

    if razorpay_order_id != order.razorpay_order_id:

        messages.error(
            request,
            'Invalid payment order.'
        )

        return redirect('checkout')

    try:

        client = razorpay.Client(
            auth=(
                settings.RAZORPAY_KEY_ID,
                settings.RAZORPAY_KEY_SECRET
            )
        )

        # Verify Razorpay signature
        client.utility.verify_payment_signature({
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature,
        })

        # Confirm payment details with Razorpay
        payment = client.payment.fetch(
            razorpay_payment_id
        )

        if payment.get('order_id') != order.razorpay_order_id:
            raise ValueError('Payment order does not match.')

        if int(payment.get('amount', 0)) != int(order.total_amount * 100):
            raise ValueError('Payment amount does not match.')

        if payment.get('currency') != 'INR':
            raise ValueError('Payment currency does not match.')

        if payment.get('status') != 'captured':

            messages.error(
                request,
                'Payment has not been captured successfully.'
            )

            return redirect('checkout')

        # Update order and stock only once
        with transaction.atomic():

            locked_order = Order.objects.select_for_update().get(
                id=order.id
            )

            if locked_order.status != 'Paid':

                order_items = list(
                    locked_order.items.select_related('product')
                )

                locked_products = {}

                for item in order_items:

                    if item.product_id is None:
                        raise ValueError(
                            'A product in this order is unavailable.'
                        )

                    product = Product.objects.select_for_update().get(
                        id=item.product_id
                    )

                    locked_products[product.id] = product

                    if product.stock < item.quantity:

                        raise ValueError(
                            f'Insufficient stock for {product.name}.'
                        )

                for item in order_items:

                    product = locked_products[item.product_id]

                    product.stock -= item.quantity

                    product.save(
                        update_fields=['stock']
                    )

                locked_order.status = 'Paid'

                locked_order.razorpay_payment_id = razorpay_payment_id

                locked_order.save(
                    update_fields=[
                        'status',
                        'razorpay_payment_id'
                    ]
                )

        # Clear shopping cart after successful payment
        request.session['cart'] = {}

        messages.success(
            request,
            'Payment successful! Your order is confirmed.'
        )

        return redirect(
            'order_success',
            order_id=order.id
        )

    except Exception:

        messages.error(
            request,
            'Payment verification failed. Please contact support.'
        )

        return redirect('checkout')


# --------------------------------------------------
# 14. ORDER SUCCESS PAGE
# --------------------------------------------------

def order_success(request, order_id):

    order = get_object_or_404(
        Order,
        id=order_id
    )

    context = {
        'order': order,
        'order_items': order.items.all(),
    }

    return render(
        request,
        'products/order_success.html',
        context
    )
