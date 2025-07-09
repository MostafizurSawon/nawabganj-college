from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q

from .models import Expense, ExpenseCategory, Income, IncomeCategory
from .forms import ExpenseForm, ExpenseCategoryForm, IncomeForm, IncomeCategoryForm
from web_project import TemplateLayout, TemplateHelper
from django.http import JsonResponse

# -------------------- EXPENSE VIEWS --------------------


from django.db.models import Sum


class ExpenseDataAPIView(View):
    def get(self, request, *args, **kwargs):
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        search_value = request.GET.get('search[value]', '').strip()

        # Optional filters from query params
        category = request.GET.get('category', '')
        start_date = request.GET.get('start_date', '')
        end_date = request.GET.get('end_date', '')

        queryset = Expense.objects.select_related('exp_category').order_by('-date')

        total_records = queryset.count()

        # Apply search filter
        if search_value:
            queryset = queryset.filter(
                Q(exp_name__icontains=search_value) |
                Q(note__icontains=search_value) |
                Q(exp_category__name__icontains=search_value)
            )

        # Apply additional filters
        if category:
            queryset = queryset.filter(exp_category_id=category)
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)

        filtered_records = queryset.count()

        # Get total sum of amount for filtered data
        total_amount = queryset.aggregate(total=Sum('amount'))['total'] or 0

        # Paginate
        paginated_queryset = queryset[start:start + length]

        data = []
        for index, expense in enumerate(paginated_queryset, start=start + 1):
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
            'data': data,
            'total_amount': float(total_amount)
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
            return JsonResponse({
                "success": True,
                "message": f"Expense {'updated' if instance else 'added'} successfully."
            })
        else:
            return JsonResponse({
                "success": False,
                "errors": form.errors,
                "message": "Failed to submit expense."
            }, status=400)



class ExpenseDeleteView(View):
    def post(self, request, pk):
        expense = get_object_or_404(Expense, pk=pk)
        expense.delete()
        return JsonResponse({
            "success": True,
            "message": "Expense deleted successfully."
        })




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
        return JsonResponse({"success": True, "message": "Expense category deleted."})


# -------------------- INCOME VIEWS --------------------


from django.utils.dateparse import parse_date


class IncomeDataAPIView(View):
    def get(self, request, *args, **kwargs):
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        search_value = request.GET.get('search[value]', '').strip()
        category = request.GET.get('category', '')
        start_date = request.GET.get('start_date', '')
        end_date = request.GET.get('end_date', '')

        queryset = Income.objects.select_related('income_category').order_by('-date')

        total_records = queryset.count()

        if search_value:
            queryset = queryset.filter(
                Q(income_name__icontains=search_value) |
                Q(note__icontains=search_value) |
                Q(income_category__name__icontains=search_value)
            )

        if category:
            queryset = queryset.filter(income_category_id=category)
        if start_date:
            queryset = queryset.filter(date__gte=parse_date(start_date))
        if end_date:
            queryset = queryset.filter(date__lte=parse_date(end_date))

        filtered_records = queryset.count()
        total_amount = queryset.aggregate(total=Sum('amount'))['total'] or 0

        paginated_queryset = queryset[start:start + length]
        data = []

        for index, income in enumerate(paginated_queryset, start=start + 1):
            data.append({
                'id': income.id,  # ✅ Add this line
                'sl': index,
                'date': income.date.strftime('%Y-%m-%d'),
                'category': income.income_category.name if income.income_category else '',
                'name': income.income_name,
                'amount': f"{income.amount:.2f} ৳",
                'note': income.note or '—',
            })


        return JsonResponse({
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': filtered_records,
            'total_amount': total_amount,
            'data': data
        })


class IncomeDetailAjaxView(View):
    def get(self, request, pk, *args, **kwargs):
        try:
            income = Income.objects.select_related("income_category").get(pk=pk)
            return JsonResponse({
                "success": True,
                "income": {
                    "id": income.id,
                    "name": income.income_name,
                    "amount": str(income.amount),
                    "date": income.date.strftime('%Y-%m-%d'),
                    "note": income.note,
                    "category_id": income.income_category.id if income.income_category else None,
                }
            })
        except Income.DoesNotExist:
            return JsonResponse({"success": False, "message": "Income not found."}, status=404)




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
            return JsonResponse({
                "success": True,
                "message": f"Income {'updated' if instance else 'added'} successfully."
            })
        else:
            return JsonResponse({
                "success": False,
                "errors": form.errors,
                "message": "Failed to submit income."
            }, status=400)



class IncomeDeleteView(View):
    def post(self, request, pk):
        income = get_object_or_404(Income, pk=pk)
        income.delete()
        return JsonResponse({
            "success": True,
            "message": "Income deleted successfully."
        })



class IncomeCategoryAjaxView(View):
    def post(self, request, *args, **kwargs):
        category_id = request.POST.get("id", "").strip()
        name = request.POST.get("name", "").strip()

        instance = None
        if category_id.isdigit():
            instance = IncomeCategory.objects.filter(pk=int(category_id)).first()

        form = IncomeCategoryForm(request.POST, instance=instance)

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
        return JsonResponse({
            "success": True,
            "message": "Income category deleted successfully."
        })




# Ledger

class LedgerView(View):
    template_name = "finance/ledger.html"  # you can change this path

    def get(self, request):
        context = TemplateLayout.init(self, {})
        context["layout"] = "vertical"
        context["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", context)

        # Filters
        search = request.GET.get("search", "").strip()
        income_category = request.GET.get("income_category", "")
        expense_category = request.GET.get("expense_category", "")
        start_date = request.GET.get("start_date", "")
        end_date = request.GET.get("end_date", "")

        # Income query
        incomes = Income.objects.select_related("income_category").order_by("-date")
        if search:
            incomes = incomes.filter(Q(income_name__icontains=search) | Q(note__icontains=search))
        if income_category:
            incomes = incomes.filter(income_category_id=income_category)
        if start_date:
            incomes = incomes.filter(date__gte=start_date)
        if end_date:
            incomes = incomes.filter(date__lte=end_date)

        # Expense query
        expenses = Expense.objects.select_related("exp_category").order_by("-date")
        if search:
            expenses = expenses.filter(Q(exp_name__icontains=search) | Q(note__icontains=search))
        if expense_category:
            expenses = expenses.filter(exp_category_id=expense_category)
        if start_date:
            expenses = expenses.filter(date__gte=start_date)
        if end_date:
            expenses = expenses.filter(date__lte=end_date)

        # Totals
        total_income = incomes.aggregate(total=Sum("amount"))["total"] or 0
        total_expense = expenses.aggregate(total=Sum("amount"))["total"] or 0

        # Pagination
        income_page = Paginator(incomes, 10).get_page(request.GET.get("income_page"))
        expense_page = Paginator(expenses, 10).get_page(request.GET.get("expense_page"))

        # Context
        context.update({
            "income_page": income_page,
            "expense_page": expense_page,
            "total_income": total_income,
            "total_expense": total_expense,
            "income_categories": IncomeCategory.objects.all(),
            "expense_categories": ExpenseCategory.objects.all(),
            "search": search,
            "income_category_filter": income_category,
            "expense_category_filter": expense_category,
            "start_date": start_date,
            "end_date": end_date,
        })
        return render(request, self.template_name, context)
