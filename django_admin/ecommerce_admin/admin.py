from django.contrib import admin
from django.utils.html import format_html
from .models import User, Product, Cart, CartItem, Order, OrderItem, Payment, Notification
try:
    from .emails import send_shipping_update_email
except ImportError:
    def send_shipping_update_email(*args, **kwargs):
        pass


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "email", "role_badge", "is_active", "created_at")
    list_filter = ("role", "is_active", "created_at")
    search_fields = ("name", "email")
    ordering = ("-id",)
    actions = ["activate_users", "deactivate_users", "make_admin", "make_staff", "make_customer"]

    def role_badge(self, obj):
        colors = {
            "admin": "#dc3545",
            "staff": "#0d6efd",
            "customer": "#198754",
        }
        color = colors.get(obj.role, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold; text-transform: uppercase; font-size: 11px;">{}</span>',
            color,
            obj.role,
        )
    role_badge.short_description = "Role"

    @admin.action(description="Activate selected users")
    def activate_users(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f"{count} user(s) activated successfully.")

    @admin.action(description="Deactivate selected users")
    def deactivate_users(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f"{count} user(s) deactivated successfully.")

    @admin.action(description="Assign role: Admin")
    def make_admin(self, request, queryset):
        count = queryset.update(role="admin")
        self.message_user(request, f"{count} user(s) promoted to Admin.")

    @admin.action(description="Assign role: Staff")
    def make_staff(self, request, queryset):
        count = queryset.update(role="staff")
        self.message_user(request, f"{count} user(s) assigned as Staff.")

    @admin.action(description="Assign role: Customer")
    def make_customer(self, request, queryset):
        count = queryset.update(role="customer")
        self.message_user(request, f"{count} user(s) set to Customer.")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "category", "formatted_price", "stock_badge", "popularity", "created_at")
    list_filter = ("category", "created_at")
    search_fields = ("name", "description", "category")
    list_editable = ("category",)
    ordering = ("-id",)
    actions = ["add_10_stock", "mark_popular"]

    def formatted_price(self, obj):
        return f"${obj.price:.2f}"
    formatted_price.short_description = "Price"

    def stock_badge(self, obj):
        if obj.stock <= 5:
            color = "#dc3545"
            status = f"CRITICAL ({obj.stock})"
        elif obj.stock <= 15:
            color = "#ffc107; color: #212529"
            status = f"LOW ({obj.stock})"
        else:
            color = "#198754"
            status = f"OK ({obj.stock})"
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 7px; border-radius: 4px; font-weight: bold; font-size: 11px;">{}</span>',
            color,
            status,
        )
    stock_badge.short_description = "Stock Status"

    @admin.action(description="Add +10 units to stock")
    def add_10_stock(self, request, queryset):
        for prod in queryset:
            prod.stock += 10
            prod.save()
        self.message_user(request, f"Updated stock for {queryset.count()} product(s).")

    @admin.action(description="Boost popularity score (+10)")
    def mark_popular(self, request, queryset):
        for prod in queryset:
            prod.popularity += 10
            prod.save()
        self.message_user(request, f"Boosted popularity for {queryset.count()} product(s).")


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ("product", "quantity", "price")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user_email", "formatted_total", "payment_badge", "status_badge", "created_at")
    list_filter = ("order_status", "payment_status", "created_at")
    search_fields = ("id", "user__email", "user__name")
    inlines = [OrderItemInline]
    ordering = ("-id",)
    actions = ["mark_as_paid", "mark_as_shipped", "mark_as_delivered", "mark_as_cancelled"]

    def user_email(self, obj):
        return obj.user.email if obj.user else "N/A"
    user_email.short_description = "Customer Email"

    def formatted_total(self, obj):
        return f"${obj.total:.2f}"
    formatted_total.short_description = "Total Amount"

    def payment_badge(self, obj):
        colors = {
            "paid": "#198754",
            "unpaid": "#ffc107; color: #212529",
            "failed": "#dc3545",
            "refunded": "#6c757d",
        }
        color = colors.get(obj.payment_status, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold; text-transform: uppercase; font-size: 11px;">{}</span>',
            color,
            obj.payment_status,
        )
    payment_badge.short_description = "Payment"

    def status_badge(self, obj):
        colors = {
            "paid": "#0d6efd",
            "pending": "#ffc107; color: #212529",
            "shipped": "#0dcaf0; color: #212529",
            "delivered": "#198754",
            "cancelled": "#dc3545",
        }
        color = colors.get(obj.order_status, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold; text-transform: uppercase; font-size: 11px;">{}</span>',
            color,
            obj.order_status,
        )
    status_badge.short_description = "Order Status"

    @admin.action(description="Mark status: Paid")
    def mark_as_paid(self, request, queryset):
        queryset.update(order_status="paid", payment_status="paid")
        self.message_user(request, f"{queryset.count()} order(s) updated to Paid.")

    @admin.action(description="Mark status: Shipped")
    def mark_as_shipped(self, request, queryset):
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


    @admin.action(description="Mark status: Delivered")
    def mark_as_delivered(self, request, queryset):
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


    @admin.action(description="Mark status: Cancelled")
    def mark_as_cancelled(self, request, queryset):
        queryset.update(order_status="cancelled")
        self.message_user(request, f"{queryset.count()} order(s) marked as Cancelled.")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "order_link", "formatted_amount", "payment_method", "transaction_id", "status_badge", "timestamp")
    list_filter = ("status", "payment_method", "timestamp")
    search_fields = ("transaction_id", "order__id")
    ordering = ("-id",)

    def order_link(self, obj):
        return f"Order #{obj.order_id}"
    order_link.short_description = "Order"

    def formatted_amount(self, obj):
        return f"${obj.amount:.2f}"
    formatted_amount.short_description = "Amount"

    def status_badge(self, obj):
        colors = {
            "succeeded": "#198754",
            "pending": "#ffc107; color: #212529",
            "failed": "#dc3545",
        }
        color = colors.get(obj.status, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 11px;">{}</span>',
            color,
            obj.status.upper(),
        )
    status_badge.short_description = "Status"


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "user_email", "type", "message_preview", "read_status", "timestamp")
    list_filter = ("type", "read_status", "timestamp")
    search_fields = ("message", "user__email")
    ordering = ("-id",)
    actions = ["mark_as_read"]

    def user_email(self, obj):
        return obj.user.email if obj.user else "N/A"
    user_email.short_description = "User"

    def message_preview(self, obj):
        return obj.message[:60] + "..." if len(obj.message) > 60 else obj.message
    message_preview.short_description = "Message"

    @admin.action(description="Mark notifications as Read")
    def mark_as_read(self, request, queryset):
        queryset.update(read_status=True)
        self.message_user(request, f"{queryset.count()} notification(s) marked as read.")


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    fields = ("product", "quantity")


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "user_email", "items_count")
    search_fields = ("user__email", "user__name")
    inlines = [CartItemInline]

    def user_email(self, obj):
        return obj.user.email if obj.user else "N/A"
    user_email.short_description = "User"

    def items_count(self, obj):
        return obj.items.count()
    items_count.short_description = "Cart Items"
