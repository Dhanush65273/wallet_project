from decimal import Decimal
from datetime import datetime
from .forms import PaymentForm
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.db.models import Sum, Count, Q
from collections import defaultdict
from .models import Payment, PAYMENT_METHODS, PAYMENT_STATUS
from customers.models import Customer
from invoices.models import Invoice, InvoiceItem
import csv
from django.utils import timezone


def payment_list(request):
    payments = Payment.objects.select_related("invoice", "invoice__customer").order_by("-id")
    return render(request, "payments/payment_list.html", {
        "payments": payments
    })


def payment_create(request):
    invoice_id = request.GET.get("invoice_id")

    if request.method == "POST":
        form = PaymentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("payment_list")
    else:
        if invoice_id:
            invoice = get_object_or_404(Invoice, pk=invoice_id)
            form = PaymentForm(initial={
                "invoice": invoice,
                "amount": invoice.total_amount,
            })
        else:
            form = PaymentForm()

    return render(request, "payments/payment_form.html", {
        "form": form
    })

def payment_update(request, pk):
    payment = get_object_or_404(Payment, pk=pk)

    if request.method == "POST":
        form = PaymentForm(request.POST, instance=payment)
        if form.is_valid():
            form.save()
            return redirect("payment_list")
    else:
        form = PaymentForm(instance=payment)

    return render(request, "payments/payment_form.html", {
        "form": form,
        "title": "Edit Payment"
    })

def payment_delete(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    payment.delete()
    return redirect("payment_list")

def payment_report(request):
    payments = Payment.objects.select_related("invoice__customer")

    invoice_id = request.GET.get("invoice_id") or ""
    status = request.GET.get("status") or ""
    date_from = request.GET.get("date_from") or ""
    date_to = request.GET.get("date_to") or ""

    if invoice_id:
        payments = payments.filter(invoice_id=invoice_id)

    if status:
        payments = payments.filter(status=status)

    if date_from:
        payments = payments.filter(payment_date__gte=date_from)

    if date_to:
        payments = payments.filter(payment_date__lte=date_to)

    invoices = Invoice.objects.all()

    return render(request, "payments/reports.html", {
        "payments": payments,
        "invoices": invoices,
        "selected_invoice_id": invoice_id,
        "selected_status": status,
        "date_from": date_from,
        "date_to": date_to,
    })
def export_payments_csv(request):
    # same filters as payment_report
    payments = Payment.objects.select_related("invoice__customer")

    invoice_id = request.GET.get("invoice_id") or ""
    status = request.GET.get("status") or ""
    date_from = request.GET.get("date_from") or ""
    date_to = request.GET.get("date_to") or ""

    if invoice_id:
        payments = payments.filter(invoice_id=invoice_id)

    if status:
        payments = payments.filter(status=status)

    if date_from:
        payments = payments.filter(payment_date__gte=date_from)

    if date_to:
        payments = payments.filter(payment_date__lte=date_to)

    # CSV response
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="payments_report.csv"'

    writer = csv.writer(response)
    writer.writerow(["ID", "Invoice", "Customer", "Method",
                     "Status", "Amount", "Payment Date"])

    for p in payments:
        writer.writerow([
            p.id,
            p.invoice.id,
            p.invoice.customer.name,
            p.payment_method or "",
            p.status,
            p.amount,
            p.payment_date,
        ])

    return response

# coustemer report

def customer_report(request):
    payments = Payment.objects.select_related("invoice__customer")

    date_from = request.GET.get("date_from") or ""
    date_to = request.GET.get("date_to") or ""

    if date_from:
        payments = payments.filter(payment_date__gte=date_from)
    if date_to:
        payments = payments.filter(payment_date__lte=date_to)

    # * CORRECT GROUP BY *
    summary = (
        payments
        .values("invoice__customer__name")           # <-- UNMAI FIELD
        .annotate(
            payment_count=Count("id"),
            total_amount=Sum("amount"),
        )
        .order_by("invoice__customer__name")
    )

    return render(request, "payments/customer_report.html", {
        "summary": summary,
        "date_from": date_from,
        "date_to": date_to,
    })


# -----------------------------
# CUSTOMER-WISE CSV EXPORT
# -----------------------------
def export_customer_report_csv(request):
    payments = Payment.objects.select_related("invoice__customer")

    date_from = request.GET.get("date_from") or ""
    date_to = request.GET.get("date_to") or ""

    if date_from:
        payments = payments.filter(payment_date__gte=date_from)
    if date_to:
        payments = payments.filter(payment_date__lte=date_to)

    summary = (
        payments
        .values("invoice__customer__name")
        .annotate(
            payment_count=Count("id"),
            total_amount=Sum("amount"),
        )
        .order_by("invoice__customer__name")
    )

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="customer_report.csv"'

    writer = csv.writer(response)
    writer.writerow(["Customer", "No. of Payments", "Total Amount"])

    for row in summary:
        writer.writerow([
            row["invoice__customer__name"],
            row["payment_count"],
            row["total_amount"],
        ])

    return response
    
def product_report(request):
    date_from = request.GET.get("date_from") or ""
    date_to = request.GET.get("date_to") or ""

    items = InvoiceItem.objects.select_related("invoice", "product")

    if date_from:
        items = items.filter(invoice_invoice_date_gte=date_from)
    if date_to:
        items = items.filter(invoice_invoice_date_lte=date_to)

    summary = (
        items
        .values("product__name")
        .annotate(
            total_quantity=Sum("quantity"),
            total_amount=Sum("amount"),
        )
        .order_by("product__name")
    )

    return render(request, "payments/product_report.html", {
        "summary": summary,
        "date_from": date_from,
        "date_to": date_to,
    })

def export_product_report_csv(request):
    date_from = request.GET.get("date_from") or ""
    date_to = request.GET.get("date_to") or ""

    items = InvoiceItem.objects.select_related("invoice", "product")

    if date_from:
        items = items.filter(invoice_invoice_date_gte=date_from)
    if date_to:
        items = items.filter(invoice_invoice_date_lte=date_to)

    summary = (
        items
        .values("product__name")
        .annotate(
            total_quantity=Sum("quantity"),
            total_amount=Sum("amount"),
        )
        .order_by("product__name")
    )

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename=\"product_report.csv\"'

    writer = csv.writer(response)
    writer.writerow(["Product", "Quantity", "Total Amount"])

    for row in summary:
        writer.writerow([
            row["product__name"],
            row["total_quantity"],
            row["total_amount"],
        ])

    return response

def invoice_report(request):
    customer_id = request.GET.get("customer_id") or ""
    date_from = request.GET.get("date_from") or ""
    date_to = request.GET.get("date_to") or ""

    invoices = Invoice.objects.select_related("customer").all()

    if customer_id:
        invoices = invoices.filter(customer_id=customer_id)
    if date_from:
        invoices = invoices.filter(invoice_date__gte=date_from)
    if date_to:
        invoices = invoices.filter(invoice_date__lte=date_to)

    rows = []
    for inv in invoices:
        payments = Payment.objects.filter(invoice=inv, status="success")
        paid = payments.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        balance = inv.total_amount - paid

        rows.append({
            "invoice_id": inv.id,
            "customer_name": inv.customer.name,
            "invoice_date": inv.invoice_date,
            "total_amount": inv.total_amount,
            "paid_amount": paid,
            "balance": balance,
        })

    customers = Invoice.objects.select_related("customer").values(
        "customer_id", "customer__name"
    ).distinct()

    return render(request, "payments/invoice_report.html", {
        "rows": rows,
        "customers": customers,
        "selected_customer_id": int(customer_id) if customer_id else "",
        "date_from": date_from,
        "date_to": date_to,
    })

def export_invoice_report_csv(request):
    customer_id = request.GET.get("customer_id") or ""
    date_from = request.GET.get("date_from") or ""
    date_to = request.GET.get("date_to") or ""

    invoices = Invoice.objects.select_related("customer").all()

    if customer_id:
        invoices = invoices.filter(customer_id=customer_id)
    if date_from:
        invoices = invoices.filter(invoice_date__gte=date_from)
    if date_to:
        invoices = invoices.filter(invoice_date__lte=date_to)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="invoice_report.csv"'

    writer = csv.writer(response)
    writer.writerow(["Invoice ID", "Customer", "Date",
                     "Total Amount", "Paid Amount", "Balance"])

    for inv in invoices:
        payments = Payment.objects.filter(invoice=inv, status="success")
        paid = payments.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        balance = inv.total_amount - paid

        writer.writerow([
            inv.id,
            inv.customer.name,
            inv.invoice_date,
            inv.total_amount,
            paid,
            balance,
        ])

    return response

def monthly_report(request):
    date_from = request.GET.get("date_from") or ""
    date_to = request.GET.get("date_to") or ""

    invoices = Invoice.objects.all()

    if date_from:
        invoices = invoices.filter(invoice_date__gte=date_from)
    if date_to:
        invoices = invoices.filter(invoice_date__lte=date_to)

    summary_map = {}

    for inv in invoices:
        year = inv.invoice_date.year
        month = inv.invoice_date.month
        key = (year, month)

        payments = Payment.objects.filter(invoice=inv, status="success")
        paid = payments.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        balance = inv.total_amount - paid

        if key not in summary_map:
            summary_map[key] = {
                "year": year,
                "month": month,
                "invoice_count": 0,
                "total_invoice_amount": Decimal("0.00"),
                "total_paid": Decimal("0.00"),
                "total_balance": Decimal("0.00"),
            }

        summary_map[key]["invoice_count"] += 1
        summary_map[key]["total_invoice_amount"] += inv.total_amount
        summary_map[key]["total_paid"] += paid
        summary_map[key]["total_balance"] += balance

    summary = sorted(summary_map.values(), key=lambda r: (r["year"], r["month"]))

    return render(request, "payments/monthly_report.html", {
        "summary": summary,
        "date_from": date_from,
        "date_to": date_to,
    })
def export_monthly_report_csv(request):
    date_from = request.GET.get("date_from") or ""
    date_to = request.GET.get("date_to") or ""

    invoices = Invoice.objects.all()

    if date_from:
        invoices = invoices.filter(invoice_date__gte=date_from)
    if date_to:
        invoices = invoices.filter(invoice_date__lte=date_to)

    summary_map = {}

    for inv in invoices:
        year = inv.invoice_date.year
        month = inv.invoice_date.month
        key = (year, month)

        payments = Payment.objects.filter(invoice=inv, status="success")
        paid = payments.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        balance = inv.total_amount - paid

        if key not in summary_map:
            summary_map[key] = {
                "year": year,
                "month": month,
                "invoice_count": 0,
                "total_invoice_amount": Decimal("0.00"),
                "total_paid": Decimal("0.00"),
                "total_balance": Decimal("0.00"),
            }

        summary_map[key]["invoice_count"] += 1
        summary_map[key]["total_invoice_amount"] += inv.total_amount
        summary_map[key]["total_paid"] += paid
        summary_map[key]["total_balance"] += balance

    summary = sorted(summary_map.values(), key=lambda r: (r["year"], r["month"]))

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="monthly_report.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "Year", "Month", "No. of Invoices",
        "Total Invoice Amount", "Total Paid", "Total Balance"
    ])

    for row in summary:
        writer.writerow([
            row["year"],
            row["month"],
            row["invoice_count"],
            row["total_invoice_amount"],
            row["total_paid"],
            row["total_balance"],
        ])

    return response

def outstanding_report(request):
    date_from = request.GET.get("date_from") or ""
    date_to = request.GET.get("date_to") or ""

    invoices = Invoice.objects.select_related("customer").all()

    if date_from:
        invoices = invoices.filter(invoice_date__gte=date_from)
    if date_to:
        invoices = invoices.filter(invoice_date__lte=date_to)

    summary_map = {}

    for inv in invoices:
        payments = Payment.objects.filter(invoice=inv, status="success")
        paid = payments.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        balance = inv.total_amount - paid

        if balance <= 0:
            continue  # only outstanding

        cid = inv.customer_id

        if cid not in summary_map:
            summary_map[cid] = {
                "customer_name": inv.customer.name,
                "total_invoice_amount": Decimal("0.00"),
                "total_paid": Decimal("0.00"),
                "total_balance": Decimal("0.00"),
            }

        summary_map[cid]["total_invoice_amount"] += inv.total_amount
        summary_map[cid]["total_paid"] += paid
        summary_map[cid]["total_balance"] += balance

    summary = sorted(
        summary_map.values(),
        key=lambda r: r["total_balance"],
        reverse=True
    )

    return render(request, "payments/outstanding_report.html", {
        "summary": summary,
        "date_from": date_from,
        "date_to": date_to,
    })
def export_outstanding_report_csv(request):
    date_from = request.GET.get("date_from") or ""
    date_to = request.GET.get("date_to") or ""

    invoices = Invoice.objects.select_related("customer").all()

    if date_from:
        invoices = invoices.filter(invoice_date__gte=date_from)
    if date_to:
        invoices = invoices.filter(invoice_date__lte=date_to)

    summary_map = {}

    for inv in invoices:
        payments = Payment.objects.filter(invoice=inv, status="success")
        paid = payments.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        balance = inv.total_amount - paid

        if balance <= 0:
            continue

        cid = inv.customer_id

        if cid not in summary_map:
            summary_map[cid] = {
                "customer_name": inv.customer.name,
                "total_invoice_amount": Decimal("0.00"),
                "total_paid": Decimal("0.00"),
                "total_balance": Decimal("0.00"),
            }

        summary_map[cid]["total_invoice_amount"] += inv.total_amount
        summary_map[cid]["total_paid"] += paid
        summary_map[cid]["total_balance"] += balance

    summary = sorted(
        summary_map.values(),
        key=lambda r: r["total_balance"],
        reverse=True
    )

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="outstanding_report.csv"'

    writer = csv.writer(response)
    writer.writerow(["Customer", "Total Invoice", "Total Paid", "Outstanding"])

    for row in summary:
        writer.writerow([
            row["customer_name"],
            row["total_invoice_amount"],
            row["total_paid"],
            row["total_balance"],
        ])

    return response