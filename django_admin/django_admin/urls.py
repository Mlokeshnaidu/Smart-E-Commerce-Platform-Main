from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

admin.site.site_header = "Smart E-Commerce Administration"
admin.site.site_title = "Smart E-Commerce Admin Portal"
admin.site.index_title = "Admin Management & Operations"

urlpatterns = [
    path("", lambda request: redirect("/admin/dashboard/")),
    path("admin/", include("ecommerce_admin.urls")),
    path("admin/", admin.site.urls),
]
