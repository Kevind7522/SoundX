from django.urls import path
from . import views

urlpatterns = [

    path("", views.index, name="index"),
    path("register/", views.register, name="register"),
    path("login/", views.user_login, name="login"),
    path("logout/", views.user_logout, name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("wishlist/<int:product_id>/", views.toggle_wishlist, name="toggle_wishlist"),
    path("wishlist/", views.wishlist, name="wishlist"),
    path("cart/", views.cart, name="cart"),
    path("add-to-cart/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
    path("increase/<int:cart_id>/", views.increase_quantity, name="increase_quantity"),
    path("decrease/<int:cart_id>/", views.decrease_quantity, name="decrease_quantity"),
    path("remove-cart/<int:cart_id>/", views.remove_from_cart, name="remove_from_cart"),
    path("checkout/<int:product_id>/", views.checkout, name="checkout"),
    path("checkout-cart/", views.checkout_cart, name="checkout_cart"),
    path("orders/", views.orders, name="orders"),
    path("cancel-order/<int:order_id>/", views.cancel_order, name="cancel_order"),
    path("invoice/<int:order_id>/", views.download_invoice, name="download_invoice"),
]