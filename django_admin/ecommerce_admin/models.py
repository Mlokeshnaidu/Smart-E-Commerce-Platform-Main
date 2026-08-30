from django.db import models


class User(models.Model):
    ROLE_CHOICES = [
        ("admin", "Admin"),
        ("staff", "Staff"),
        ("customer", "Customer"),
    ]

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=120)
    email = models.CharField(max_length=120, unique=True)
    password = models.CharField(max_length=255, null=True, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="customer")
    is_active = models.BooleanField(default=True)
    auth0_id = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        db_table = "users"
        managed = False
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return f"{self.name} ({self.email}) - {self.role}"


class Product(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    category = models.CharField(max_length=100, null=True, blank=True)
    price = models.FloatField()
    stock = models.IntegerField(default=0)
    images = models.JSONField(default=list, blank=True)
    popularity = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        db_table = "products"
        managed = False
        verbose_name = "Product"
        verbose_name_plural = "Products"

    def __str__(self):
        return f"{self.name} (${self.price:.2f}) [Stock: {self.stock}]"


class Cart(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, db_column="user_id", related_name="cart")

    class Meta:
        db_table = "carts"
        managed = False
        verbose_name = "Cart"
        verbose_name_plural = "Carts"

    def __str__(self):
        return f"Cart #{self.id} (User: {self.user.name if self.user else 'Unknown'})"


class CartItem(models.Model):
    id = models.AutoField(primary_key=True)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, db_column="cart_id", related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, db_column="product_id", related_name="cart_items")
    quantity = models.IntegerField(default=1)

    class Meta:
        db_table = "cart_items"
        managed = False
        verbose_name = "Cart Item"
        verbose_name_plural = "Cart Items"

    def __str__(self):
        return f"{self.quantity}x {self.product.name if self.product else 'Product'} (Cart #{self.cart_id})"


class Order(models.Model):
    ORDER_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    ]

    PAYMENT_STATUS_CHOICES = [
        ("unpaid", "Unpaid"),
        ("paid", "Paid"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
    ]

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column="user_id", related_name="orders")
    total = models.FloatField()
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default="unpaid")
    order_status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        db_table = "orders"
        managed = False
        verbose_name = "Order"
        verbose_name_plural = "Orders"

    def __str__(self):
        return f"Order #{self.id} - ${self.total:.2f} [{self.order_status}]"


class OrderItem(models.Model):
    id = models.AutoField(primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, db_column="order_id", related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, db_column="product_id", related_name="order_items")
    quantity = models.IntegerField()
    price = models.FloatField()

    class Meta:
        db_table = "order_items"
        managed = False
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"

    def __str__(self):
        return f"{self.quantity}x {self.product.name if self.product else 'Item'} @ ${self.price:.2f}"


class Payment(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("succeeded", "Succeeded"),
        ("failed", "Failed"),
    ]

    id = models.AutoField(primary_key=True)
    order = models.OneToOneField(Order, on_delete=models.CASCADE, db_column="order_id", related_name="payment")
    amount = models.FloatField()
    payment_method = models.CharField(max_length=50, default="stripe")
    transaction_id = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    timestamp = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        db_table = "payments"
        managed = False
        verbose_name = "Payment"
        verbose_name_plural = "Payments"

    def __str__(self):
        return f"Payment #{self.id} for Order #{self.order_id} - ${self.amount:.2f} [{self.status}]"


class Notification(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column="user_id", related_name="notifications")
    type = models.CharField(max_length=50)
    message = models.CharField(max_length=500)
    read_status = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        db_table = "notifications"
        managed = False
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"

    def __str__(self):
        return f"[{self.type}] {self.user.email if self.user else 'User'}: {self.message[:30]}"
