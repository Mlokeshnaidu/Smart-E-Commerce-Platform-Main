import csv
import io
import json
from datetime import datetime
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.db.models import Sum, Count, F, Q
from django.contrib.admin.views.decorators import staff_member_required

from .models import User, Product, Order, OrderItem, Payment, Notification

# ReportLab for PDF generation
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors


def dashboard_view(request):
    # Summary Metrics
    total_orders = Order.objects.count()
    total_revenue = Order.objects.filter(~Q(order_status="cancelled")).aggregate(total=Sum("total"))["total"] or 0.0
    total_products = Product.objects.count()
    total_customers = User.objects.filter(role="customer").count()
    low_stock_products = list(Product.objects.filter(stock__lte=10).order_by("stock")[:8])
    recent_orders = Order.objects.select_related("user").order_by("-created_at")[:8]

    # Chart 1: Sales / Orders by Status
    status_counts = (
        Order.objects.values("order_status")
        .annotate(count=Count("id"))
        .order_by("order_status")
    )
    status_labels = [s["order_status"].title() for s in status_counts]
    status_data = [s["count"] for s in status_counts]

    # Chart 2: Top Selling Products
    top_prods = (
        OrderItem.objects.values("product__name")
        .annotate(sold=Sum("quantity"))
        .order_by("-sold")[:6]
    )
    top_prod_labels = [p["product__name"] for p in top_prods if p["product__name"]]
    top_prod_data = [p["sold"] for p in top_prods if p["product__name"]]

    # Chart 3: Low Stock Alerts Chart
    low_stock_labels = [p.name[:18] for p in low_stock_products]
    low_stock_data = [p.stock for p in low_stock_products]

    # Chart 4: Revenue breakdown by payment status
    pay_status = (
        Payment.objects.values("status")
        .annotate(total=Sum("amount"))
        .order_by("status")
    )
    pay_labels = [p["status"].title() for p in pay_status]
    pay_data = [round(p["total"], 2) for p in pay_status]

    context = {
        "total_orders": total_orders,
        "total_revenue": round(total_revenue, 2),
        "total_products": total_products,
        "total_customers": total_customers,
        "low_stock_count": len(low_stock_products),
        "low_stock_products": low_stock_products,
        "recent_orders": recent_orders,
        "status_labels_json": json.dumps(status_labels),
        "status_data_json": json.dumps(status_data),
        "top_prod_labels_json": json.dumps(top_prod_labels),
        "top_prod_data_json": json.dumps(top_prod_data),
        "low_stock_labels_json": json.dumps(low_stock_labels),
        "low_stock_data_json": json.dumps(low_stock_data),
        "pay_labels_json": json.dumps(pay_labels),
        "pay_data_json": json.dumps(pay_data),
    }
    return render(request, "ecommerce_admin/dashboard.html", context)


def reports_page_view(request):
    return render(request, "ecommerce_admin/reports.html")


def export_report_view(request, report_type, format_type):
    format_type = format_type.lower()
    report_type = report_type.lower()

    if format_type == "csv":
        return _generate_csv_report(report_type)
    elif format_type == "pdf":
        return _generate_pdf_report(report_type)
    else:
        return JsonResponse({"error": "Unsupported format"}, status=400)


def _generate_csv_report(report_type):
    response = HttpResponse(content_type="text/csv")
    timestamp_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    response["Content-Disposition"] = f'attachment; filename="{report_type}_report_{timestamp_str}.csv"'

    writer = csv.writer(response)

    if report_type == "orders":
        writer.writerow(["Order ID", "Customer Name", "Customer Email", "Total Amount ($)", "Order Status", "Payment Status", "Created At"])
        orders = Order.objects.select_related("user").order_by("-id")
        for o in orders:
            writer.writerow([
                o.id,
                o.user.name if o.user else "N/A",
                o.user.email if o.user else "N/A",
                f"{o.total:.2f}",
                o.order_status,
                o.payment_status,
                o.created_at.strftime("%Y-%m-%d %H:%M") if o.created_at else "N/A",
            ])

    elif report_type == "sales":
        writer.writerow(["Metric", "Value"])
        total_revenue = Order.objects.filter(~Q(order_status="cancelled")).aggregate(t=Sum("total"))["t"] or 0.0
        total_orders = Order.objects.count()
        paid_orders = Order.objects.filter(order_status__in=["paid", "shipped", "delivered"]).count()
        cancelled = Order.objects.filter(order_status="cancelled").count()
        avg_order = (total_revenue / total_orders) if total_orders > 0 else 0.0

        writer.writerow(["Total Revenue ($)", f"{total_revenue:.2f}"])
        writer.writerow(["Total Orders Count", total_orders])
        writer.writerow(["Successful/Paid Orders", paid_orders])
        writer.writerow(["Cancelled Orders", cancelled])
        writer.writerow(["Average Order Value ($)", f"{avg_order:.2f}"])
        writer.writerow([])
        writer.writerow(["Top Selling Products", "Units Sold"])
        top_prods = OrderItem.objects.values("product__name").annotate(sold=Sum("quantity")).order_by("-sold")[:10]
        for p in top_prods:
            writer.writerow([p["product__name"] or "Product", p["sold"]])

    elif report_type == "users":
        writer.writerow(["User ID", "Name", "Email", "Role", "Active Status", "Auth0 ID", "Joined Date"])
        users = User.objects.all().order_by("-id")
        for u in users:
            writer.writerow([
                u.id,
                u.name,
                u.email,
                u.role,
                "Active" if u.is_active else "Inactive",
                u.auth0_id or "N/A",
                u.created_at.strftime("%Y-%m-%d %H:%M") if u.created_at else "N/A",
            ])
    else:
        return JsonResponse({"error": "Invalid report type"}, status=400)

    return response


def _generate_pdf_report(report_type):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        name="ReportTitle",
        parent=styles["Heading1"],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        name="ReportSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=14,
    )

    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    if report_type == "orders":
        elements.append(Paragraph("Smart E-Commerce — Orders Report", title_style))
        elements.append(Paragraph(f"Generated on {now_str}", subtitle_style))
        elements.append(Spacer(1, 10))

        data = [["Order #", "Customer", "Total", "Status", "Payment", "Date"]]
        orders = Order.objects.select_related("user").order_by("-id")[:50]
        for o in orders:
            data.append([
                f"#{o.id}",
                o.user.name[:18] if o.user else "N/A",
                f"${o.total:.2f}",
                o.order_status.title(),
                o.payment_status.title(),
                o.created_at.strftime("%m/%d %H:%M") if o.created_at else "-",
            ])

        table = Table(data, colWidths=[55, 130, 65, 80, 80, 100])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.white]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
        ]))
        elements.append(table)

    elif report_type == "sales":
        elements.append(Paragraph("Smart E-Commerce — Executive Sales Report", title_style))
        elements.append(Paragraph(f"Generated on {now_str}", subtitle_style))
        elements.append(Spacer(1, 10))

        total_revenue = Order.objects.filter(~Q(order_status="cancelled")).aggregate(t=Sum("total"))["t"] or 0.0
        total_orders = Order.objects.count()
        paid_orders = Order.objects.filter(order_status__in=["paid", "shipped", "delivered"]).count()
        avg_val = (total_revenue / total_orders) if total_orders > 0 else 0.0

        summary_data = [
            ["Metric", "Value"],
            ["Total Platform Revenue", f"${total_revenue:,.2f}"],
            ["Total Orders Placed", str(total_orders)],
            ["Completed / Paid Orders", str(paid_orders)],
            ["Average Order Value", f"${avg_val:,.2f}"],
        ]
        summary_table = Table(summary_data, colWidths=[240, 240])
        summary_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f766e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f0fdfa"), colors.white]),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 18))

        elements.append(Paragraph("Top 10 Products by Volume Sold", styles["Heading2"]))
        elements.append(Spacer(1, 6))

        top_data = [["Product Name", "Units Sold"]]
        top_prods = OrderItem.objects.values("product__name").annotate(sold=Sum("quantity")).order_by("-sold")[:10]
        for p in top_prods:
            top_data.append([p["product__name"] or "Product", str(p["sold"])])

        top_table = Table(top_data, colWidths=[360, 120])
        top_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.white]),
        ]))
        elements.append(top_table)

    elif report_type == "users":
        elements.append(Paragraph("Smart E-Commerce — User Accounts Report", title_style))
        elements.append(Paragraph(f"Generated on {now_str}", subtitle_style))
        elements.append(Spacer(1, 10))

        data = [["ID", "Name", "Email", "Role", "Status", "Joined"]]
        users = User.objects.all().order_by("-id")[:50]
        for u in users:
            data.append([
                f"#{u.id}",
                u.name[:18],
                u.email[:25],
                u.role.upper(),
                "Active" if u.is_active else "Inactive",
                u.created_at.strftime("%Y-%m-%d") if u.created_at else "-",
            ])

        table = Table(data, colWidths=[40, 110, 150, 65, 65, 80])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.white]),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
        ]))
        elements.append(table)

    doc.build(elements)
    buffer.seek(0)

    timestamp_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{report_type}_report_{timestamp_str}.pdf"'
    return response
