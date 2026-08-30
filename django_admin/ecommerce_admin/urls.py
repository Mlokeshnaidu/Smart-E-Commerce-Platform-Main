from django.urls import path
from . import views

urlpatterns = [
    path("dashboard/", views.dashboard_view, name="admin_dashboard"),
    path("reports/", views.reports_page_view, name="admin_reports"),
    path("reports/export/<str:report_type>/<str:format_type>/", views.export_report_view, name="export_report"),
]
