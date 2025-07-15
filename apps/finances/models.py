from django.db import models

from apps.admissions.models import Session, Programs, Group

class Purpose(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.name

class Invoice(models.Model):
    invoice_session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='invoice_session', verbose_name="invoice Session", null=True, blank=True)
    invoice_program = models.ForeignKey(Programs, on_delete=models.CASCADE, related_name='invoice_program', verbose_name="invoice Program", null=True, blank=True)    #Hsc
    invoice_group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='invoice_group', verbose_name="invoice Group", null=True, blank=True)
    invoice_purpose = models.ForeignKey(Purpose, on_delete=models.CASCADE, related_name='invoice_purpose', verbose_name="invoice Purpose", null=True, blank=True)
    amount = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True,null=True, blank=True)

    def __str__(self):
        return self.invoice_group.group_name



from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

class StudentInvoice(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    student = GenericForeignKey('content_type', 'object_id')

    invoice = models.ForeignKey('Invoice', on_delete=models.CASCADE, related_name='student_invoices')
    is_paid = models.BooleanField(default=False)
    note = models.TextField(null=True, blank=True)

    # ✅ Add these:
    add_payment_method = models.CharField(
        max_length=15,
        choices=[
            ('office', 'Office Cash'),
            ('bkash', 'Bkash'),
            ('rocket', 'Rocket'),
            ('nagad', 'Nagad'),
            ('bank', 'Bank'),
            ('others', 'Others'),
        ],
        null=True,
        blank=True
    )

    discount_amount = models.PositiveIntegerField(null=True, blank=True)
    discount_reason = models.CharField(max_length=255, null=True, blank=True)

    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('content_type', 'object_id', 'invoice')

    def __str__(self):
        if self.discount_amount:
            final = max(0, self.invoice.amount - self.discount_amount)
            return f"{self.student} | {self.invoice.invoice_purpose} | {final} Tk (after discount)"
        return f"{self.student} | {self.invoice.invoice_purpose} | {self.invoice.amount} Tk"







# Expense Section
class ExpenseCategory(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Expense Type", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Expense(models.Model):
    exp_category = models.ForeignKey(ExpenseCategory, on_delete=models.CASCADE, related_name='expenses', verbose_name="Expense Category")
    exp_name = models.CharField(max_length=255, verbose_name="Expense Name", null=True, blank=True)
    date = models.DateField(verbose_name="Date")
    amount = models.IntegerField(verbose_name="Expense Amount")
    note = models.TextField(blank=True, null=True, verbose_name="Expense Note")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.exp_name} - {self.amount} ৳"




# Income Section
class IncomeCategory(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Income Type", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Income(models.Model):
    income_category = models.ForeignKey(IncomeCategory, on_delete=models.CASCADE, related_name='incomes', verbose_name="Income Category")
    income_name = models.CharField(max_length=255, verbose_name="income Name", null=True, blank=True)
    date = models.DateField(verbose_name="Date")
    amount = models.IntegerField(verbose_name="Income Amount")
    note = models.TextField(blank=True, null=True, verbose_name="Income Note")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.amount} ৳"
