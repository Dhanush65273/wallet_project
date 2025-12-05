from django.urls import path
from . import views

urlpatterns = [
    # ==== normal Payments screens ====
    path("", views.payment_list, name="payment_list"),
    path("add/", views.payment_create, name="payment_create"),
    path("<int:pk>/edit/", views.payment_update, name="payment_update"),
    path("<int:pk>/delete/", views.payment_delete, name="payment_delete"),

    # ==== Reports main (Payments report) ====
    path("reports/", views.payment_report, name="payment_report"),
    path("reports/export-csv/", views.export_payments_csv, name="export-csv"),

    # ---- Customer-wise ----
    path("reports/customers/", views.customer_report, name="customer_report"),
    path("reports/customers/export-csv/",
         views.export_customer_report_csv,
         name="customer-report-csv"),

    # ---- Product-wise ----
    path("reports/products/", views.product_report, name="product_report"),
    path("reports/products/export-csv/",
         views.export_product_report_csv,
         name="product-report-csv"),

    # ---- Invoice-wise ----
    path("reports/invoices/", views.invoice_report, name="invoice_report"),
    path("reports/invoices/export-csv/",
         views.export_invoice_report_csv,
         name="invoice-report-csv"),

    # ---- Monthly summary ----
    path("reports/monthly/", views.monthly_report, name="monthly_report"),
    path("reports/monthly/export-csv/",
         views.export_monthly_report_csv,
         name="monthly-report-csv"),

    # ---- Outstanding ----
    path("reports/outstanding/", views.outstanding_report, name="outstanding_report"),
    path("reports/outstanding/export-csv/",
         views.export_outstanding_report_csv,
         name="outstanding-report-csv"),
]