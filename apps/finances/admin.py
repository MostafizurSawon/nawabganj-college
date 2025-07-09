from django.contrib import admin
from .models import ExpenseCategory, Expense, IncomeCategory, Income

# Register your models here.

admin.site.register(ExpenseCategory)
admin.site.register(Expense)
admin.site.register(IncomeCategory)
admin.site.register(Income)
