from django.db import models

# College Fee
class FeeCategory(models.Model):
    fee_category = models.CharField(max_length=100, unique=True, verbose_name="Fee Category Main", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.fee_category

class Fee(models.Model):
    fee_category = models.ForeignKey(FeeCategory, on_delete=models.CASCADE, related_name='fee_cat', verbose_name="Fee Category")
    fee_name = models.CharField(max_length=100)
    amount = models.PositiveIntegerField()

    def __str__(self):
        return self.fee_name






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
