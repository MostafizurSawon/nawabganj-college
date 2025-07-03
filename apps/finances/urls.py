from django.urls import path
from .views import (
    ExpenseView, ExpenseDeleteView, ExpenseCategoryView, ExpenseCategoryDeleteView,
    IncomeView, IncomeDeleteView, IncomeCategoryView, IncomeCategoryDeleteView
)

from .views import ExpenseDataAPIView,ExpenseCategoryAjaxView,ExpenseDetailAjaxView

urlpatterns = [
    # Expense
    path('expenses/data/', ExpenseDataAPIView.as_view(), name='expense_data'),  # Ajax Api setup
    path('expenses/data/<int:pk>/', ExpenseDetailAjaxView.as_view(), name='expense_detail_ajax'),
    # path('expenses/data/<int:pk>/', ExpenseDetailAPI.as_view(), name='expense_detail_api'),

    path('expenses/', ExpenseView.as_view(), name='expense_list'),
    path('expenses/edit/<int:pk>/', ExpenseView.as_view(), name='edit_expense'),
    path('expenses/delete/<int:pk>/', ExpenseDeleteView.as_view(), name='delete_expense'),

    # Expense Categories
    path("expense-categories/ajax/save/", ExpenseCategoryAjaxView.as_view(), name="ajax_expense_category_save"),    # Ajax
    path('expense-categories/', ExpenseCategoryView.as_view(), name='expense_category_list'),
    path('expense-categories/edit/<int:pk>/', ExpenseCategoryView.as_view(), name='edit_expense_category'),
    path('expense-categories/delete/<int:pk>/', ExpenseCategoryDeleteView.as_view(), name='delete_expense_category'),

    # Income
    path('incomes/', IncomeView.as_view(), name='income_list'),
    path('incomes/edit/<int:pk>/', IncomeView.as_view(), name='edit_income'),
    path('incomes/delete/<int:pk>/', IncomeDeleteView.as_view(), name='delete_income'),

    # Income Categories
    path('income-categories/', IncomeCategoryView.as_view(), name='income_category_list'),
    path('income-categories/edit/<int:pk>/', IncomeCategoryView.as_view(), name='edit_income_category'),
    path('income-categories/delete/<int:pk>/', IncomeCategoryDeleteView.as_view(), name='delete_income_category'),
]
