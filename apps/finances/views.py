from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q

from .models import Expense, ExpenseCategory, Income, IncomeCategory
from .forms import ExpenseForm, ExpenseCategoryForm, IncomeForm, IncomeCategoryForm
from web_project import TemplateLayout, TemplateHelper
from django.http import JsonResponse



# Student Invoice List

from django.views.generic import ListView
from django.contrib.contenttypes.models import ContentType
from apps.admissions.models import HscAdmissions, DegreeAdmission, Session
from .models import StudentInvoice
from django.utils.dateparse import parse_date

class StudentInvoiceListView(ListView):
    model = StudentInvoice
    template_name = 'students/student_invoice_list.html'
    context_object_name = 'student_invoices'
    paginate_by = 25



    def get_queryset(self):
        queryset = super().get_queryset().select_related("invoice")

        invoice_id = self.request.GET.get("invoice")  # We’ll stop showing this on UI later if not needed
        search = self.request.GET.get("search", "")
        active_session_id = self.request.GET.get('session') or self.request.session.get('active_session_id')
        group = self.request.GET.get('group')
        purpose = self.request.GET.get('purpose')
        is_paid = self.request.GET.get('is_paid')
        assigned_from = self.request.GET.get('assigned_from')
        assigned_to = self.request.GET.get('assigned_to')

        # Filter by invoice ID (optional)
        if invoice_id:
            queryset = queryset.filter(invoice_id=invoice_id)

        # Session filtering using GenericForeignKey model type
        if active_session_id:
            hsc_ct = ContentType.objects.get_for_model(HscAdmissions)
            hsc_ids = HscAdmissions.objects.filter(add_session_id=active_session_id).values_list("id", flat=True)

            deg_ct = ContentType.objects.get_for_model(DegreeAdmission)
            deg_ids = DegreeAdmission.objects.filter(add_session_id=active_session_id).values_list("id", flat=True)

            queryset = queryset.filter(
                Q(content_type=hsc_ct, object_id__in=hsc_ids) |
                Q(content_type=deg_ct, object_id__in=deg_ids)
            )

        # Search across student name/mobile/etc.
        if search:
            hsc_ct = ContentType.objects.get_for_model(HscAdmissions)
            hsc_ids = HscAdmissions.objects.filter(
                Q(add_name__icontains=search) |
                Q(add_name_bangla__icontains=search) |
                Q(add_mobile__icontains=search)
            ).values_list("id", flat=True)

            deg_ct = ContentType.objects.get_for_model(DegreeAdmission)
            deg_ids = DegreeAdmission.objects.filter(
                Q(add_name__icontains=search) |
                Q(add_name_bangla__icontains=search) |
                Q(add_mobile__icontains=search)
            ).values_list("id", flat=True)

            queryset = queryset.filter(
                Q(content_type=hsc_ct, object_id__in=hsc_ids) |
                Q(content_type=deg_ct, object_id__in=deg_ids)
            )

        # ✅ Filter by group (from student object)
        if group:
            queryset = queryset.filter(
                Q(student__add_admission_group=group)
            )

        # ✅ Filter by purpose
        if purpose:
            queryset = queryset.filter(invoice__invoice_purpose_id=purpose)

        # ✅ Filter by paid status
        if is_paid in ["true", "false"]:
            queryset = queryset.filter(is_paid=(is_paid == "true"))

        # ✅ Filter by assigned date range
        if assigned_from:
            queryset = queryset.filter(assigned_at__date__gte=parse_date(assigned_from))
        if assigned_to:
            queryset = queryset.filter(assigned_at__date__lte=parse_date(assigned_to))

        return queryset


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Layout setup
        context = TemplateLayout.init(self, context)
        context["layout"] = "vertical"
        context["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", context)

        # Filter states
        context["search"] = self.request.GET.get('search', '')
        context["invoice_id"] = self.request.GET.get('invoice', '')
        context["selected_session"] = self.request.GET.get('session') or self.request.session.get('active_session_id')
        context["sessions"] = Session.objects.all()
        context["groups"] = ['science', 'arts', 'commerce', 'ba', 'bss', 'bba', 'bbs', 'bsc']
        context["purposes"] = Purpose.objects.all()

        return context

from django.views.generic.detail import DetailView
from .models import StudentInvoice

class StudentInvoiceDetailView(DetailView):
    model = StudentInvoice
    template_name = 'students/student_invoice_detail.html'
    context_object_name = 'invoice'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Optional: access student & differentiate types
        student = self.object.student
        context["student_type"] = (
            "HSC" if isinstance(student, HscAdmissions)
            else "Degree" if isinstance(student, DegreeAdmission)
            else "Unknown"
        )

        # 🔢 Final payable amount (Invoice amount - Discount)
        base_amount = self.object.invoice.amount or 0
        discount = self.object.discount_amount or 0
        context["final_amount"] = max(0, base_amount - discount)

        # 📐 Layout logic
        context = TemplateLayout.init(self, context)
        context["layout"] = "vertical"
        context["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", context)

        return context



from django.views.generic.edit import UpdateView
from .models import StudentInvoice

class StudentInvoiceUpdateView(UpdateView):
    model = StudentInvoice
    fields = []  # not using Django's form rendering
    http_method_names = ['post']
    template_name = None  # no page render, handled via modal

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        try:
            note = request.POST.get("note", "")
            is_paid = "is_paid" in request.POST
            payment_method = request.POST.get("add_payment_method")
            discount_amount = int(request.POST.get("discount_amount") or 0)
            discount_reason = request.POST.get("discount_reason")

            self.object.note = note
            self.object.is_paid = is_paid
            self.object.add_payment_method = payment_method
            self.object.discount_amount = discount_amount
            self.object.discount_reason = discount_reason

            self.object.save()

            messages.success(request, "Student invoice updated.")
        except Exception as e:
            messages.error(request, f"Update failed: {str(e)}")

        return redirect("student-invoice-list")






# Invoice Section

from django.views.generic import ListView

from apps.admissions.models import Programs
from .models import Invoice, Purpose
from .forms import InvoiceGenerateForm
from .utils import assign_invoice_to_students

from django.views.generic.edit import UpdateView
from django.urls import reverse_lazy


class InvoiceListCreateView(ListView):
    model = Invoice
    template_name = 'invoice/invoice_generate.html'
    context_object_name = 'invoices'
    paginate_by = 25

    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'invoice_session', 'invoice_program', 'invoice_group', 'invoice_purpose'
        )

        search = self.request.GET.get('search', '')
        purpose = self.request.GET.get('purpose')
        program = self.request.GET.get('program')
        session = self.request.GET.get('session')

        if search:
            queryset = queryset.filter(
                Q(invoice_session__ses_name__icontains=search) |
                Q(invoice_program__pro_name__icontains=search) |
                Q(invoice_group__group_name__icontains=search) |
                Q(invoice_purpose__name__icontains=search) |
                Q(amount__icontains=search)
            )

        if purpose:
            queryset = queryset.filter(invoice_purpose_id=purpose)
        if program:
            queryset = queryset.filter(invoice_program_id=program)
        if session:
            queryset = queryset.filter(invoice_session_id=session)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = TemplateLayout.init(self, context)
        context["layout"] = "vertical"
        context["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", context)
        context["form"] = InvoiceGenerateForm()

        # 🔃 Add dropdown lists
        context["invoice_purpose_list"] = Purpose.objects.all()
        context["session_list"] = Session.objects.all()
        context["program_list"] = Programs.objects.all()

        # 🪪 Repopulate filters
        context["selected_search"] = self.request.GET.get("search", "")
        context["selected_purpose"] = self.request.GET.get("purpose", "")
        context["selected_program"] = self.request.GET.get("program", "")
        context["selected_session"] = self.request.GET.get("session", "")

        return context



    def post(self, request, *args, **kwargs):
        form = InvoiceGenerateForm(request.POST)
        if form.is_valid():
            invoice = form.save()
            assigned = assign_invoice_to_students(invoice)
            messages.success(request, f"Invoice created and assigned to {assigned} students.")
            return redirect('invoice-generate')  # replace with your URL name
        else:
            # 🔁 Re-render page with form errors + layout
            context = self.get_context_data()
            context["form"] = form
            messages.error(self.request, "Failed!")
            return self.render_to_response(context)



class InvoiceUpdateView(UpdateView):
    model = Invoice
    form_class = InvoiceGenerateForm
    http_method_names = ['post']
    template_name = None  # Modal handles UI

    def form_valid(self, form):
        messages.success(self.request, "Invoice updated successfully.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Update failed. Please check the data.")
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('invoice-generate')


# Invoice Purpose
# views.py
from django.views.generic import ListView
from .forms import PurposeForm  # You’ll need a simple ModelForm

class PurposeListCreateView(ListView):
    model = Purpose
    template_name = "invoice/purpose_invoice_page.html"
    context_object_name = "purposes"
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = TemplateLayout.init(self, context)
        context["layout"] = "vertical"
        context["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", context)
        context["form"] = PurposeForm()
        context["edit_id"] = self.request.GET.get("edit")  # used to show edit modal if needed
        return context

    def post(self, request, *args, **kwargs):
        edit_id = request.POST.get("edit_id")
        if edit_id:
            instance = get_object_or_404(Purpose, id=edit_id)
            form = PurposeForm(request.POST, instance=instance)
            msg = "updated"
        else:
            form = PurposeForm(request.POST)
            msg = "created"

        if form.is_valid():
            form.save()
            messages.success(request, f"Purpose {msg} successfully.")
            return redirect("purpose-invoice-page")  # change if needed
        else:
            # Render page with errors
            context = self.get_context_data()
            context["form"] = form
            return self.render_to_response(context)



from django.views.generic import DeleteView

class PurposeDeleteView(DeleteView):
    model = Purpose
    success_url = reverse_lazy("purpose-invoice-page")

    def post(self, request, *args, **kwargs):
        messages.success(request, "Purpose deleted.")
        return super().post(request, *args, **kwargs)



from django.views.generic.edit import DeleteView


class InvoiceDeleteView(DeleteView):
    model = Invoice
    success_url = reverse_lazy('invoice-generate')
    template_name = None  # No separate template needed

    def post(self, request, *args, **kwargs):
        messages.success(request, "Invoice deleted successfully.")
        return super().post(request, *args, **kwargs)





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
        income_page = Paginator(incomes, 15).get_page(request.GET.get("income_page"))
        expense_page = Paginator(expenses, 15).get_page(request.GET.get("expense_page"))

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





# views.py
import csv
from django.http import HttpResponse

def export_ledger_csv(request):
    # Create HTTP response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="ledger.csv"'

    writer = csv.writer(response)
    writer.writerow(['Type', 'Date', 'Category', 'Name', 'Amount', 'Note'])

    # Get filters
    search = request.GET.get("search")
    income_cat = request.GET.get("income_category")
    expense_cat = request.GET.get("expense_category")
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    # Apply filters to income
    income_qs = Income.objects.all()
    if income_cat:
        income_qs = income_qs.filter(income_category_id=income_cat)
    if start_date:
        income_qs = income_qs.filter(date__gte=start_date)
    if end_date:
        income_qs = income_qs.filter(date__lte=end_date)
    if search:
        income_qs = income_qs.filter(Q(note__icontains=search) | Q(income_name__icontains=search))

    for i in income_qs:
        writer.writerow(['Income', i.date, i.income_category.name, i.income_name, i.amount, i.note])

    # Apply filters to expense
    expense_qs = Expense.objects.all()
    if expense_cat:
        expense_qs = expense_qs.filter(exp_category_id=expense_cat)
    if start_date:
        expense_qs = expense_qs.filter(date__gte=start_date)
    if end_date:
        expense_qs = expense_qs.filter(date__lte=end_date)
    if search:
        expense_qs = expense_qs.filter(Q(note__icontains=search) | Q(exp_name__icontains=search))

    for e in expense_qs:
        writer.writerow(['Expense', e.date, e.exp_category.name, e.exp_name, e.amount, e.note])

    return response
