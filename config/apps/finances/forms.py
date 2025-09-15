from django import forms

from .models import Invoice

class InvoiceAssignForm(forms.Form):
    invoice = forms.ModelChoiceField(queryset=Invoice.objects.all())
    student_type = forms.ChoiceField(choices=[
        ('hsc', 'HSC'),
        ('degree', 'Degree')
    ])


# invoice Purpose
# forms.py
from .models import Purpose

class PurposeForm(forms.ModelForm):
    class Meta:
        model = Purpose
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter purpose name',
                'required': True
            })
        }




# invoice for all students


from .models import Invoice

class InvoiceGenerateForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['invoice_session', 'invoice_program', 'invoice_group', 'invoice_purpose', 'amount']
        widgets = {
            'amount': forms.NumberInput(attrs={'min': 0}),
        }










# Income Expense
from .models import Expense, ExpenseCategory, Income, IncomeCategory



class ExpenseCategoryForm(forms.ModelForm):
    class Meta:
        model = ExpenseCategory
        fields = ['name']


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['exp_category', 'exp_name', 'date', 'amount', 'note']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }


class IncomeCategoryForm(forms.ModelForm):
    class Meta:
        model = IncomeCategory
        fields = ['name']


class IncomeForm(forms.ModelForm):
    class Meta:
        model = Income
        fields = ['income_category', 'income_name', 'date', 'amount', 'note']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }
