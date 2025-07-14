from django.contrib import admin
from .models import ExpenseCategory, Expense, IncomeCategory, Income, Invoice, Purpose

# Register your models here.

admin.site.register(Invoice)
admin.site.register(Purpose)
admin.site.register(ExpenseCategory)
admin.site.register(Expense)
admin.site.register(IncomeCategory)
admin.site.register(Income)
