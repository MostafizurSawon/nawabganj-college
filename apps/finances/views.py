from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q

from .models import Expense, ExpenseCategory, Income, IncomeCategory
from .forms import ExpenseForm, ExpenseCategoryForm, IncomeForm, IncomeCategoryForm
from web_project import TemplateLayout, TemplateHelper


# -------------------- EXPENSE VIEWS --------------------

from django.http import JsonResponse


class ExpenseDataAPIView(View):
    def get(self, request, *args, **kwargs):
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        search_value = request.GET.get('search[value]', '')

        queryset = Expense.objects.select_related('exp_category').order_by('-date')

        total_records = queryset.count()

        if search_value:
            queryset = queryset.filter(
                Q(exp_name__icontains=search_value) |
                Q(note__icontains=search_value) |
                Q(exp_category__name__icontains=search_value)
            )

        filtered_records = queryset.count()
        queryset = queryset[start:start + length]

        data = []

        for index, expense in enumerate(queryset, start=start + 1):
            data.append({
                'id': expense.id,
                'sl': index,
                'date': expense.date.strftime('%Y-%m-%d'),
                'category': expense.exp_category.name if expense.exp_category else '',
                'name': expense.exp_name,
                'amount': f"{expense.amount} ৳",
                'note': expense.note or '—',

            })

        return JsonResponse({
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': filtered_records,
            'data': data
        })


class ExpenseDetailAjaxView(View):
    def get(self, request, pk, *args, **kwargs):
        try:
            expense = Expense.objects.select_related("exp_category").get(pk=pk)
            return JsonResponse({
                "success": True,
                "expense": {
                    "id": expense.id,
                    "name": expense.exp_name,
                    "amount": str(expense.amount),
                    "date": expense.date.strftime('%Y-%m-%d'),
                    "note": expense.note,
                    "category_id": expense.exp_category.id if expense.exp_category else None,
                }
            })
        except Expense.DoesNotExist:
            return JsonResponse({"success": False, "message": "Expense not found."}, status=404)





class ExpenseView(View):
    template_name = "expense/expense_list.html"

    def get(self, request, *args, **kwargs):
        context = TemplateLayout.init(self, {})

        context["layout"] = "vertical"
        context["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", context)

        search_query = request.GET.get("search", "").strip()
        category_filter = request.GET.get("category", "")
        start_date = request.GET.get("start_date", "")
        end_date = request.GET.get("end_date", "")

        expenses = Expense.objects.select_related("exp_category").order_by("-date")

        if search_query:
            expenses = expenses.filter(
                Q(exp_name__icontains=search_query) |
                Q(note__icontains=search_query)
            )

        if category_filter:
            expenses = expenses.filter(exp_category_id=category_filter)
        if start_date:
            expenses = expenses.filter(date__gte=start_date)
        if end_date:
            expenses = expenses.filter(date__lte=end_date)

        paginator = Paginator(expenses, 10)
        page_number = request.GET.get("page")
        context["expenses"] = paginator.get_page(page_number)

        context["form"] = ExpenseForm()
        context["categories"] = ExpenseCategory.objects.all()
        context["search_query"] = search_query
        context["category_filter"] = category_filter
        context["start_date"] = start_date
        context["end_date"] = end_date
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        expense_id = kwargs.get("pk")
        instance = get_object_or_404(Expense, pk=expense_id) if expense_id else None
        form = ExpenseForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, f"Expense {'updated' if instance else 'added'} successfully.")
        else:
            messages.error(request, "Failed to submit expense.")
        return redirect("expense_list")



class ExpenseDeleteView(View):
    def post(self, request, pk):
        expense = get_object_or_404(Expense, pk=pk)
        expense.delete()
        messages.success(request, "Expense deleted successfully.")
        return redirect("expense_list")




# Ajax Expense category



class ExpenseCategoryAjaxView(View):
    def post(self, request, *args, **kwargs):
        category_id = request.POST.get("id", "").strip()
        name = request.POST.get("name", "").strip()

        instance = None
        if category_id.isdigit():
            instance = ExpenseCategory.objects.filter(pk=int(category_id)).first()

        form = ExpenseCategoryForm(request.POST, instance=instance)

        if form.is_valid():
            category = form.save()
            return JsonResponse({
                "success": True,
                "id": category.id,
                "name": category.name,
                "message": f"Category {'updated' if instance else 'created'} successfully."
            })
        else:
            return JsonResponse({
                "success": False,
                "errors": form.errors,
                "message": "Validation failed."
            }, status=400)





class ExpenseCategoryView(View):
    template_name = "expense/expense_category_list.html"

    def get(self, request, *args, **kwargs):
        context = TemplateLayout.init(self, {})
        context["layout"] = "vertical"
        context["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", context)

        search_query = request.GET.get("search", "").strip()
        categories = ExpenseCategory.objects.all().order_by("-created_at")

        if search_query:
            categories = categories.filter(name__icontains=search_query)

        paginator = Paginator(categories, 10)
        page_number = request.GET.get("page")
        context["categories"] = paginator.get_page(page_number)
        context["form"] = ExpenseCategoryForm()
        context["search_query"] = search_query
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        category_id = kwargs.get("pk")
        instance = get_object_or_404(ExpenseCategory, pk=category_id) if category_id else None
        form = ExpenseCategoryForm(request.POST, instance=instance)

        if form.is_valid():
            form.save()
            messages.success(request, f"Expense category {'updated' if instance else 'created'} successfully.")
        else:
            messages.error(request, "Failed to save category.")

        return redirect("expense_category_list")



class ExpenseCategoryDeleteView(View):
    def post(self, request, pk):
        category = get_object_or_404(ExpenseCategory, pk=pk)
        category.delete()
        messages.success(request, "Expense category deleted.")
        return redirect("expense_category_list")


# -------------------- INCOME VIEWS --------------------


class IncomeView(View):
    template_name = "income/income_list.html"

    def get(self, request, *args, **kwargs):
        context = TemplateLayout.init(self, {})
        context["layout"] = "vertical"
        context["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", context)

        search_query = request.GET.get("search", "").strip()
        category_filter = request.GET.get("category", "")
        start_date = request.GET.get("start_date", "")
        end_date = request.GET.get("end_date", "")

        incomes = Income.objects.select_related("income_category").order_by("-date")

        if search_query:
            incomes = incomes.filter(
                Q(income_name__icontains=search_query) |
                Q(note__icontains=search_query)
            )

        if category_filter:
            incomes = incomes.filter(income_category_id=category_filter)
        if start_date:
            incomes = incomes.filter(date__gte=start_date)
        if end_date:
            incomes = incomes.filter(date__lte=end_date)

        paginator = Paginator(incomes, 10)
        page_number = request.GET.get("page")
        context["incomes"] = paginator.get_page(page_number)

        context["form"] = IncomeForm()
        context["categories"] = IncomeCategory.objects.all()
        context["search_query"] = search_query
        context["category_filter"] = category_filter
        context["start_date"] = start_date
        context["end_date"] = end_date
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        income_id = kwargs.get("pk")
        instance = get_object_or_404(Income, pk=income_id) if income_id else None
        form = IncomeForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, f"Income {'updated' if instance else 'added'} successfully.")
        else:
            messages.error(request, "Failed to submit income.")
        return redirect("income_list")



class IncomeDeleteView(View):
    def post(self, request, pk):
        income = get_object_or_404(Income, pk=pk)
        income.delete()
        messages.success(request, "Income deleted.")
        return redirect("income_list")



class IncomeCategoryView(View):
    template_name = "income/income_category_list.html"

    def get(self, request, *args, **kwargs):
        context = TemplateLayout.init(self, {})
        context["layout"] = "vertical"
        context["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", context)

        search_query = request.GET.get("search", "").strip()
        categories = IncomeCategory.objects.all().order_by("-created_at")

        if search_query:
            categories = categories.filter(name__icontains=search_query)

        paginator = Paginator(categories, 10)
        page_number = request.GET.get("page")
        context["categories"] = paginator.get_page(page_number)
        context["form"] = IncomeCategoryForm()
        context["search_query"] = search_query
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        category_id = kwargs.get("pk")
        instance = get_object_or_404(IncomeCategory, pk=category_id) if category_id else None
        form = IncomeCategoryForm(request.POST, instance=instance)

        if form.is_valid():
            form.save()
            messages.success(request, f"Income category {'updated' if instance else 'created'} successfully.")
        else:
            messages.error(request, "Failed to save category.")

        return redirect("income_category_list")



class IncomeCategoryDeleteView(View):
    def post(self, request, pk):
        category = get_object_or_404(IncomeCategory, pk=pk)
        category.delete()
        messages.success(request, "Income category deleted.")
        return redirect("income_category_list")
