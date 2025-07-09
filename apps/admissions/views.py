from django.views.generic.edit import FormView
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.http import JsonResponse

from apps.admissions.forms import HscAdmissionForm
from web_project import TemplateLayout, TemplateHelper


# 🔹 Fee API endpoint
from .models import Group, Fee, Subjects, Programs, Session

def get_admission_fee(request):
    session_id = request.GET.get('session')
    group_name = request.GET.get('group')  # ✅ dynamic

    if not session_id or not group_name:
        return JsonResponse({'amount': 0, 'error': 'Missing session or group'}, status=400)

    try:
        hsc_program = Programs.objects.get(pro_name__iexact="HSC")
        group = Group.objects.get(group_name__iexact=group_name)

        fee = Fee.objects.get(
            fee_session_id=session_id,
            fee_program=hsc_program,
            fee_group=group
        )
        return JsonResponse({'amount': fee.amount})

    except (Programs.DoesNotExist, Group.DoesNotExist, Fee.DoesNotExist):
        return JsonResponse({'amount': 0})




# 🔹 Form View

# science admission
class HscAdmissionCreateView(FormView):
    template_name = "admissions/admission_form.html"
    form_class = HscAdmissionForm
    success_url = reverse_lazy("hsc_admission_create")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Layout
        context = TemplateLayout.init(self, context)
        context["layout"] = "vertical"
        context["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", context)

        # Subject filter for group = "science"
        group = "science"
        status = "active"

        context["subjects_all"] = Subjects.objects.filter(
            group=group,
            sub_status=status,
            sub_select="all"
        )
        context["subjects_optional"] = Subjects.objects.filter(
            group=group,
            sub_status=status,
            sub_select="optional"
        )

        context["subjects_main"] = Subjects.objects.filter(
            group=group,
            sub_status=status,
            sub_select="main"
        )

        context["subjects_fourth"] = Subjects.objects.filter(
            group=group,
            sub_status=status,
            sub_select="fourth"
        )

        return context

    def form_valid(self, form):
        # Set program manually (assumes HSC exists and is unique)
        try:
            hsc_program = Programs.objects.get(pro_name__iexact="hsc")
            form.instance.add_program = hsc_program
            form.instance.add_admission_group = "science"

        except Programs.DoesNotExist:
            form.add_error(None, "HSC program not found. Please add it from admin.")
            return self.form_invalid(form)

        # Set admission fee (based on session and group)
        session_id = self.request.POST.get("add_session")
        try:
            fee = Fee.objects.get(
                fee_session_id=session_id,
                fee_program=hsc_program,
                fee_group__group_name__iexact="science"
            )
            form.instance.add_amount = fee.amount
        except Fee.DoesNotExist:
            form.instance.add_amount = 0

        # Save subjects
        form.instance.main_subject_id = self.request.POST.get("main_subject")
        form.instance.fourth_subject_id = self.request.POST.get("fourth_subject")
        self.object = form.save()

        # Auto-select all related subjects
        subjects_all = Subjects.objects.filter(
            group="science",
            sub_status="active",
            sub_select__in=["all", "optional"]
        )
        self.object.subjects.set(subjects_all)

        messages.success(self.request, "Admission submitted successfully.")
        return redirect(self.success_url)

    def form_invalid(self, form):
        print("⛔ Form INVALID")
        print(form.errors)
        return super().form_invalid(form)


# Commerce admission
class HscAdmissionCreateCommerceView(FormView):
    template_name = "admissions/admission_form.html"
    form_class = HscAdmissionForm
    success_url = reverse_lazy("hsc_admission_create_commerce")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Layout
        context = TemplateLayout.init(self, context)
        context["layout"] = "vertical"
        context["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", context)

        # Subject filter for group = "commerce"
        group = "commerce"
        status = "active"

        context["subjects_all"] = Subjects.objects.filter(
            group=group,
            sub_status=status,
            sub_select="all"
        )
        context["subjects_optional"] = Subjects.objects.filter(
            group=group,
            sub_status=status,
            sub_select="optional"
        )
        context["subjects_main"] = Subjects.objects.filter(
            group=group,
            sub_status=status,
            sub_select="main"
        )
        context["subjects_fourth"] = Subjects.objects.filter(
            group=group,
            sub_status=status,
            sub_select="fourth"
        )

        return context

    def form_valid(self, form):
        # Set program manually (assumes HSC exists)
        try:
            hsc_program = Programs.objects.get(pro_name__iexact="hsc")
            form.instance.add_program = hsc_program
            form.instance.add_admission_group = "commerce"

        except Programs.DoesNotExist:
            form.add_error(None, "HSC program not found. Please add it from admin.")
            return self.form_invalid(form)

        # Set admission fee for commerce
        session_id = self.request.POST.get("add_session")
        try:
            fee = Fee.objects.get(
                fee_session_id=session_id,
                fee_program=hsc_program,
                fee_group__group_name__iexact="commerce"
            )
            form.instance.add_amount = fee.amount
        except Fee.DoesNotExist:
            form.instance.add_amount = 0

        # Save subjects
        form.instance.main_subject_id = self.request.POST.get("main_subject")
        form.instance.fourth_subject_id = self.request.POST.get("fourth_subject")
        self.object = form.save()

        # Auto-select all related subjects
        subjects_all = Subjects.objects.filter(
            group="commerce",
            sub_status="active",
            sub_select__in=["all", "optional"]
        )
        self.object.subjects.set(subjects_all)

        messages.success(self.request, "Commerce admission submitted successfully.")
        return redirect(self.success_url)

    def form_invalid(self, form):
        print("⛔ Form INVALID")
        print(form.errors)
        return super().form_invalid(form)


# Arts Admission

from .forms import ArtsAdmissionForm


class HscAdmissionCreateArtsView(FormView):
    template_name = "admissions/admission_form_arts.html"
    form_class = ArtsAdmissionForm
    success_url = reverse_lazy("hsc_admission_create_arts")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Layout setup
        context = TemplateLayout.init(self, context)
        context["layout"] = "vertical"
        context["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", context)

        # Arts subject filtering
        group = "arts"
        status = "active"

        context["subjects_all"] = Subjects.objects.filter(group=group, sub_status=status, sub_select="all")
        context["subjects_optional"] = Subjects.objects.filter(group=group, sub_status=status, sub_select="optional")
        context["subjects_optional2"] = Subjects.objects.filter(group=group, sub_status=status, sub_select="optional2")
        context["subjects_main"] = Subjects.objects.filter(group=group, sub_status=status, sub_select="main")
        context["subjects_fourth"] = Subjects.objects.filter(group=group, sub_status=status, sub_select="fourth")

        return context

    def form_valid(self, form):
        try:
            hsc_program = Programs.objects.get(pro_name__iexact="hsc")
            form.instance.add_program = hsc_program
            form.instance.add_admission_group = "arts"
        except Programs.DoesNotExist:
            form.add_error(None, "HSC program not found. Please add it from admin.")
            return self.form_invalid(form)

        session_id = self.request.POST.get("add_session")
        try:
            fee = Fee.objects.get(
                fee_session_id=session_id,
                fee_program=hsc_program,
                fee_group__group_name__iexact="Arts"
            )
            form.instance.add_amount = fee.amount
        except Fee.DoesNotExist:
            form.instance.add_amount = 0

        # Main + Fourth subject set from form
        form.instance.main_subject_id = self.request.POST.get("main_subject")
        form.instance.fourth_subject_id = self.request.POST.get("fourth_subject")

        # Optional subjects from form
        form.instance.optional_subject_id = self.request.POST.get("optional_subject")
        form.instance.optional_subject_2_id = self.request.POST.get("optional_subject_2")

        self.object = form.save()

        # Auto-select all
        selected_subjects = Subjects.objects.filter(
            group="arts",
            sub_status="active",
            sub_select__in=["all"]
        )
        self.object.subjects.set(selected_subjects)

        messages.success(self.request, "Arts admission submitted successfully.")
        return redirect(self.success_url)

    def form_invalid(self, form):
        print("⛔ Form INVALID")
        print(form.errors)
        return super().form_invalid(form)









from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .forms import FeeForm

class FeeListView(ListView):
    template_name = 'Admissions/fee_list.html'
    model = Fee
    context_object_name = 'fees'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = TemplateLayout.init(self, context)
        context["layout"] = "vertical"
        context["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", context)
        context["form"] = FeeForm()
        context['sessions'] = Session.objects.all()
        context['programs'] = Programs.objects.all()
        context['groups'] = Group.objects.all()

        return context

class FeeCreateView(CreateView):
    model = Fee
    form_class = FeeForm
    success_url = reverse_lazy('fee_list')

    def form_valid(self, form):
        messages.success(self.request, "Fee added successfully.")
        return super().form_valid(form)

class FeeUpdateView(UpdateView):
    model = Fee
    form_class = FeeForm
    success_url = reverse_lazy('fee_list')

    def form_valid(self, form):
        messages.success(self.request, "Fee updated successfully.")
        return super().form_valid(form)

class FeeDeleteView(DeleteView):
    model = Fee
    success_url = reverse_lazy('fee_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Fee deleted successfully.")
        return super().delete(request, *args, **kwargs)
