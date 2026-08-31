import re

path = "admin.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

if "from .emails import send_shipping_update_email" not in content:
    content = content.replace(
        "from .models import User, Product, Cart, CartItem, Order, OrderItem, Payment, Notification",
        "from .models import User, Product, Cart, CartItem, Order, OrderItem, Payment, Notification\ntry:\n    from .emails import send_shipping_update_email\nexcept ImportError:\n    def send_shipping_update_email(*args, **kwargs):\n        pass"
    )

shipped_pattern = re.compile(
    r'def mark_as_shipped\(self, request, queryset\):\n(?:.*?\n)*?(?=\n    @admin\.action\(description="Mark status: Delivered"\))',
    re.MULTILINE
)
new_shipped = '''def mark_as_shipped(self, request, queryset):
        for order in queryset:
            order.order_status = "shipped"
            order.save()
            Notification.objects.create(
                user=order.user,
                type="order_shipped",
                message=f"Order #{order.id} has been shipped.",
            )
            try:
                send_shipping_update_email(order.user.email, order.id, "shipped")
            except Exception:
                pass
        self.message_user(request, f"{queryset.count()} order(s) marked as Shipped.")

'''
content, n1 = shipped_pattern.subn(new_shipped, content)

delivered_pattern = re.compile(
    r'def mark_as_delivered\(self, request, queryset\):\n(?:.*?\n)*?(?=\n    @admin\.action\(description="Mark status: Cancelled"\))',
    re.MULTILINE
)
new_delivered = '''def mark_as_delivered(self, request, queryset):
        for order in queryset:
            order.order_status = "delivered"
            order.save()
            Notification.objects.create(
                user=order.user,
                type="order_delivered",
                message=f"Order #{order.id} has been delivered.",
            )
            try:
                send_shipping_update_email(order.user.email, order.id, "delivered")
            except Exception:
                pass
        self.message_user(request, f"{queryset.count()} order(s) marked as Delivered.")

'''
content, n2 = delivered_pattern.subn(new_delivered, content)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print(f"mark_as_shipped replaced: {n1}, mark_as_delivered replaced: {n2}")
