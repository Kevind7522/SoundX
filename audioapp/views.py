from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from django.http import HttpResponse
from django.conf import settings
from decimal import Decimal

from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    Image
)

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER

import os

from .models import Product, Wishlist, Order, Cart, OrderItem


# ----------------------------
# NAVBAR COUNTS
# ----------------------------

def navbar_counts(user):
    return {
        "wishlist_count": Wishlist.objects.filter(user=user).count(),
        "cart_count": Cart.objects.filter(user=user).count(),
    }


# ----------------------------
# HOME PAGE
# ----------------------------

def index(request):
    products = Product.objects.all()

    return render(request, "index.html", {
        "products": products
    })


# ----------------------------
# REGISTER
# ----------------------------

def register(request):

    if request.method == "POST":

        name = request.POST["name"]
        email = request.POST["email"]
        password = request.POST["password"]
        confirm = request.POST["confirm"]

        if password != confirm:
            return render(
                request,
                "register.html",
                {"error": "Passwords do not match"}
            )

        if User.objects.filter(username=email).exists():
            return render(
                request,
                "register.html",
                {"error": "Email already exists"}
            )

        user = User.objects.create_user(
            username=email,
            first_name=name,
            email=email,
            password=password
        )

        login(request, user)

        return redirect("dashboard")

    return render(request, "register.html")


# ----------------------------
# LOGIN
# ----------------------------

def user_login(request):

    if request.method == "POST":

        email = request.POST["email"]
        password = request.POST["password"]

        user = authenticate(
            username=email,
            password=password
        )

        if user is not None:

            login(request, user)

            return redirect("dashboard")

        return render(
            request,
            "login.html",
            {"error": "Invalid Email or Password"}
        )

    return render(request, "login.html")


# ----------------------------
# LOGOUT
# ----------------------------

def user_logout(request):

    logout(request)

    return redirect("index")

# ----------------------------
# DASHBOARD
# ----------------------------

@login_required
def dashboard(request):

    products = Product.objects.all()

    wishlist_ids = Wishlist.objects.filter(
        user=request.user
    ).values_list("product_id", flat=True)

    context = {
        "products": products,
        "wishlist_ids": wishlist_ids,
    }

    context.update(navbar_counts(request.user))

    return render(request, "dashboard.html", context)


# ----------------------------
# TOGGLE WISHLIST
# ----------------------------

@login_required
def toggle_wishlist(request, product_id):

    product = get_object_or_404(
        Product,
        id=product_id
    )

    wishlist_item = Wishlist.objects.filter(
        user=request.user,
        product=product
    )

    if wishlist_item.exists():

        wishlist_item.delete()

    else:

        Wishlist.objects.create(
            user=request.user,
            product=product
        )

    return redirect(
        request.META.get(
            "HTTP_REFERER",
            "dashboard"
        )
    )


# ----------------------------
# WISHLIST PAGE
# ----------------------------

@login_required
def wishlist(request):

    items = Wishlist.objects.filter(
        user=request.user
    )

    context = {
        "items": items,
    }

    context.update(
        navbar_counts(request.user)
    )

    return render(
        request,
        "wishlist.html",
        context
    )

# ----------------------------
# ADD TO CART
# ----------------------------

@login_required
def add_to_cart(request, product_id):

    product = get_object_or_404(
        Product,
        id=product_id
    )

    cart_item = Cart.objects.filter(
        user=request.user,
        product=product
    )

    if cart_item.exists():

        item = cart_item.first()
        item.quantity += 1
        item.save()

    else:

        Cart.objects.create(
            user=request.user,
            product=product,
            quantity=1
        )

    return redirect(
        request.META.get(
            "HTTP_REFERER",
            "dashboard"
        )
    )


# ----------------------------
# CART PAGE
# ----------------------------

@login_required
def cart(request):

    cart_items = Cart.objects.filter(
        user=request.user
    )

    total = 0

    for item in cart_items:

        item.subtotal = item.product.price * item.quantity

        total += item.subtotal

    context = {
        "cart_items": cart_items,
        "total": total,
    }

    context.update(
        navbar_counts(request.user)
    )

    return render(
        request,
        "cart.html",
        context
    )


# ----------------------------
# INCREASE QUANTITY
# ----------------------------

@login_required
def increase_quantity(request, cart_id):

    cart = get_object_or_404(
        Cart,
        id=cart_id,
        user=request.user
    )

    cart.quantity += 1
    cart.save()

    return redirect("cart")


# ----------------------------
# DECREASE QUANTITY
# ----------------------------

@login_required
def decrease_quantity(request, cart_id):

    cart = get_object_or_404(
        Cart,
        id=cart_id,
        user=request.user
    )

    if cart.quantity > 1:

        cart.quantity -= 1
        cart.save()

    return redirect("cart")


# ----------------------------
# REMOVE FROM CART
# ----------------------------

@login_required
def remove_from_cart(request, cart_id):

    cart = get_object_or_404(
        Cart,
        id=cart_id,
        user=request.user
    )

    cart.delete()

    return redirect("cart")

# ----------------------------
# BUY NOW CHECKOUT
# ----------------------------

@login_required
def checkout(request, product_id):

    product = get_object_or_404(
        Product,
        id=product_id
    )

    if request.method == "POST":

        payment = request.POST.get("payment")

        # ----------------------------
        # PAYMENT VALIDATION
        # ----------------------------

        if payment == "UPI":

            upi_id = request.POST.get(
                "upi_id", ""
            ).strip()

            upi_pin = request.POST.get(
                "upi_pin", ""
            ).strip()

            if not upi_id or not upi_pin:

                context = {
                    "product": product,
                    "error": "Please enter your UPI ID and UPI PIN."
                }

                context.update(
                    navbar_counts(request.user)
                )

                return render(
                    request,
                    "checkout.html",
                    context
                )

        elif payment == "Credit / Debit Card":

            card_number = request.POST.get(
                "card_number", ""
            ).strip()

            cvv = request.POST.get(
                "cvv", ""
            ).strip()

            if not card_number or not cvv:

                context = {
                    "product": product,
                    "error": "Please enter your Card Number and CVV."
                }

                context.update(
                    navbar_counts(request.user)
                )

                return render(
                    request,
                    "checkout.html",
                    context
                )

        # ----------------------------
        # CREATE ORDER
        # ----------------------------

        order = Order.objects.create(
            user=request.user,
            customer_name=request.POST["name"],
            phone=request.POST["phone"],
            address=request.POST["address"],
            city=request.POST["city"],
            state=request.POST["state"],
            pincode=request.POST["pincode"],
            payment_method=payment
        )

        # ----------------------------
        # CREATE ORDER ITEM
        # ----------------------------

        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=1,
            price=product.price
        )

        return redirect("orders")

    # ----------------------------
    # GET REQUEST
    # ----------------------------

    context = {
        "product": product,
    }

    context.update(
        navbar_counts(request.user)
    )

    return render(
        request,
        "checkout.html",
        context
    )


# ----------------------------
# ORDER ALL CHECKOUT
# ----------------------------

@login_required
def checkout_cart(request):

    cart_items = Cart.objects.filter(user=request.user)

    if not cart_items.exists():
        return redirect("cart")

    total = 0

    for item in cart_items:
        item.subtotal = item.product.price * item.quantity
        total += item.subtotal

    if request.method == "POST":

        payment = request.POST.get("payment")

        # -------------------------
        # PAYMENT VALIDATION
        # -------------------------

        if payment == "UPI":

            upi_id = request.POST.get("upi_id", "").strip()
            upi_pin = request.POST.get("upi_pin", "").strip()

            if not upi_id or not upi_pin:

                context = {
                    "cart_items": cart_items,
                    "total": total,
                    "error": "Please enter UPI ID and UPI PIN."
                }

                context.update(navbar_counts(request.user))

                return render(
                    request,
                    "checkout_cart.html",
                    context
                )

        elif payment == "Credit / Debit Card":

            card_number = request.POST.get(
                "card_number", ""
            ).strip()

            cvv = request.POST.get(
                "cvv", ""
            ).strip()

            if not card_number or not cvv:

                context = {
                    "cart_items": cart_items,
                    "total": total,
                    "error": "Please enter Card Number and CVV."
                }

                context.update(navbar_counts(request.user))

                return render(
                    request,
                    "checkout_cart.html",
                    context
                )

        # -------------------------
        # CREATE ORDER
        # -------------------------

        order = Order.objects.create(
            user=request.user,
            customer_name=request.POST["name"],
            phone=request.POST["phone"],
            address=request.POST["address"],
            city=request.POST["city"],
            state=request.POST["state"],
            pincode=request.POST["pincode"],
            payment_method=payment,
        )

        # -------------------------
        # CREATE ORDER ITEMS
        # -------------------------

        for item in cart_items:

            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price
            )

        # Empty cart after successful order
        cart_items.delete()

        return redirect("orders")

    context = {
        "cart_items": cart_items,
        "total": total,
    }

    context.update(navbar_counts(request.user))

    return render(
        request,
        "checkout_cart.html",
        context
    )

# ----------------------------
# ORDERS PAGE
# ----------------------------

@login_required
def orders(request):

    orders = Order.objects.filter(
        user=request.user
    ).prefetch_related("items__product").order_by("-ordered_at")

    for order in orders:
        grand_total = Decimal("0.00")

        for item in order.items.all():
            item.subtotal = item.price * item.quantity
            grand_total += item.subtotal

        order.grand_total = grand_total

    context = {
        "orders": orders,
    }

    context.update(navbar_counts(request.user))

    return render(request, "orders.html", context)


# ----------------------------
# CANCEL ORDER
# ----------------------------

@login_required
def cancel_order(request, order_id):

    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user
    )

    if order.status != "Cancelled":

        order.status = "Cancelled"
        order.save()

    return redirect("orders")

# ----------------------------
# DOWNLOAD INVOICE PDF
# ----------------------------

@login_required
def download_invoice(request, order_id):

    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user
    )

    items = order.items.all()

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="Invoice_{order.id}.pdf"'
    )

    doc = SimpleDocTemplate(
        response,
        rightMargin=25,
        leftMargin=25,
        topMargin=20,
        bottomMargin=20
    )

    styles = getSampleStyleSheet()
    elements = []

    # LOGO
    logo_path = os.path.join(
        settings.BASE_DIR,
        "audioapp",
        "static",
        "images",
        "logo.avif"
    )

    if os.path.exists(logo_path):
        logo = Image(logo_path, width=45, height=45)
        logo.hAlign = "CENTER"
        elements.append(logo)

    # TITLE
    title = ParagraphStyle(
        "title",
        parent=styles["Heading1"],
        alignment=TA_CENTER,
        textColor=colors.HexColor("#b43ae4"),
        fontSize=18,
        spaceAfter=10
    )

    elements.append(Paragraph("<b>SOUNDX MUSIC STORE</b>", title))
    elements.append(Paragraph("<b>INVOICE</b>", styles["Heading2"]))
    elements.append(Spacer(1, 10))

    # CUSTOMER DETAILS
    invoice = f"INV-{order.id:05d}"

    details = [
        ["Invoice No", invoice],
        ["Order Date", order.ordered_at.strftime("%d-%m-%Y %I:%M %p")],
        ["Customer", order.customer_name],
        ["Phone", order.phone],
        ["Address", f"{order.address}, {order.city}, {order.state} - {order.pincode}"],
        ["Payment", order.payment_method],
        ["Status", order.status],
    ]

    detail_table = Table(details, colWidths=[120, 340])
    detail_table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("BACKGROUND", (0,0), (0,-1), colors.HexColor("#b43ae4")),
        ("TEXTCOLOR", (0,0), (0,-1), colors.white),
        ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("BOTTOMPADDING", (0,0), (-1,-1), 7),
        ("TOPPADDING", (0,0), (-1,-1), 7),
    ]))
    elements.append(detail_table)
    elements.append(Spacer(1, 15))

    # PRODUCT TABLE
    data = [["Product", "Price", "Qty", "Total"]]

    grand_total = Decimal("0.00")

    for item in items:
        total = item.price * item.quantity
        grand_total += total

        data.append([
            item.product.name,
            f"₹ {item.price}",
            str(item.quantity),
            f"₹ {total}"
        ])

    product_table = Table(data, colWidths=[180,90,60,130])

    product_table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#b43ae4")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("TOPPADDING", (0,0), (-1,-1), 8),
    ]))

    elements.append(product_table)
    elements.append(Spacer(1, 15))

    # TOTAL TABLE
    total_table = Table([
        ["Subtotal", f"₹ {grand_total}"],
        ["Delivery", "FREE"],
        ["Grand Total", f"₹ {grand_total}"],
    ], colWidths=[300,160])

    total_table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("BACKGROUND", (0,2), (-1,2), colors.HexColor("#b43ae4")),
        ("TEXTCOLOR", (0,2), (-1,2), colors.white),
        ("FONTNAME", (0,2), (-1,2), "Helvetica-Bold"),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("TOPPADDING", (0,0), (-1,-1), 8),
    ]))

    elements.append(total_table)
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("<b>Authorized Signature</b>", styles["Heading3"]))
    elements.append(Paragraph("___________________________", styles["Normal"]))
    elements.append(Spacer(1, 10))

    thanks = ParagraphStyle(
        "thanks",
        alignment=TA_CENTER,
        fontSize=12,
        textColor=colors.HexColor("#b43ae4")
    )

    elements.append(Paragraph(
        "<b>Thank you for shopping with SoundX!</b>",
        thanks
    ))

    doc.build(elements)

    return response