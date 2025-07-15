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


# Degree api
from .models import DegreePrograms

def get_degree_admission_fee(request):
    session_id = request.GET.get('session')
    group_name = request.GET.get('group')

    if not session_id or not group_name:
        return JsonResponse({'amount': 0, 'error': 'Missing session or group'}, status=400)

    try:
        program = DegreePrograms.objects.get(deg_name__iexact=group_name)
        group = Group.objects.get(group_name__iexact=group_name)

        fee = Fee.objects.get(
            fee_session_id=session_id,
            fee_program__pro_name__iexact="Degree",
            fee_group=group
        )
        return JsonResponse({'amount': fee.amount})
    except Exception as e:
        print("❌ Degree Fee Fetch Error:", str(e))
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

        # messages.success(self.request, "Admission submitted successfully.")
        # return redirect(self.success_url)

        messages.success(self.request, "Admission submitted successfully.")
        return redirect("hsc_admission_view", pk=self.object.pk)


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
        # return redirect(self.success_url)
        return redirect("hsc_admission_view", pk=self.object.pk)

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
        # return redirect(self.success_url)
        return redirect("hsc_admission_view", pk=self.object.pk)

    def form_invalid(self, form):
        print("⛔ Form INVALID")
        print(form.errors)
        return super().form_invalid(form)



# Honours Admission Section


from django.views.generic.edit import FormView
from django.urls import reverse_lazy

from apps.admissions.forms import DegreeAdmissionForm
from apps.admissions.models import DegreePrograms, DegreeSubjects


class AdmissionBaCreateView(FormView):
    template_name = "admissions_others/admission_form_honours.html"
    form_class = DegreeAdmissionForm
    success_url = reverse_lazy("ba_admission_create")  # ✅ change this URL name as per your `urls.py`

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Layout setup
        context = TemplateLayout.init(self, context)
        context["layout"] = "vertical"
        context["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", context)

        group = "Ba"
        status = "active"

        context["subjects_all"] = DegreeSubjects.objects.filter(
            group=group,
            sub_status=status
        )

        return context

    def get_initial(self):
        return {
            "add_admission_group": "Ba"
        }

    def form_valid(self, form):
        # Set program and group
        # print("en")
        try:
            program = DegreePrograms.objects.get(deg_name__iexact="Ba")
            form.instance.add_program = program
            form.instance.add_admission_group = "Ba"
        except DegreePrograms.DoesNotExist:
            print("fsdf",form.errors)
            form.add_error(None, "BA program not found.")
            return self.form_invalid(form)

        # Set amount if needed – you can fetch from fee model if it exists
        form.instance.add_amount = 0  # default 0

        self.object = form.save()

        # Set ManyToMany subjects manually
        selected_subjects = self.request.POST.getlist("subjects")
        if selected_subjects:
            self.object.subjects.set(selected_subjects)

        # Optional: Set main subject
        form.instance.main_subject_id = self.request.POST.get("main_subject")
        self.object.save()

        messages.success(self.request, "✅ BA admission submitted successfully.")
        return redirect(self.success_url)

    def form_invalid(self, form):
        print("Form invalid:", form.errors)
        return super().form_invalid(form)



# Bss
class AdmissionBssCreateView(FormView):
    template_name = "admissions_others/admission_form_honours.html"
    form_class = DegreeAdmissionForm
    success_url = reverse_lazy("bss_admission_create")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Layout setup
        context = TemplateLayout.init(self, context)
        context["layout"] = "vertical"
        context["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", context)

        group = "Bss"
        status = "active"

        context["subjects_all"] = DegreeSubjects.objects.filter(
            group=group,
            sub_status=status
        )

        return context

    def get_initial(self):
        return {
            "add_admission_group": "Bss"
        }


    def form_valid(self, form):
        # Set program and group
        try:
            program = DegreePrograms.objects.get(deg_name__iexact="Bss")
            form.instance.add_program = program
            form.instance.add_admission_group = "Bss"
        except DegreePrograms.DoesNotExist:
            form.add_error(None, "BSS program not found.")
            return self.form_invalid(form)

        form.instance.add_amount = 0  # Default fee — optionally fetch from Fee model

        self.object = form.save()

        # Set ManyToMany subjects
        selected_subjects = self.request.POST.getlist("subjects")
        if selected_subjects:
            self.object.subjects.set(selected_subjects)

        form.instance.main_subject_id = self.request.POST.get("main_subject")
        self.object.save()

        messages.success(self.request, "✅ BSS admission submitted successfully.")
        return redirect(self.success_url)

    def form_invalid(self, form):
        print("Form invalid:", form.errors)
        return super().form_invalid(form)



# Bsc
from apps.admissions.forms import DegreeAdmissionForm

class AdmissionBscCreateView(FormView):
    template_name = "admissions_others/admission_form_honours.html"
    form_class = DegreeAdmissionForm
    success_url = reverse_lazy("bsc_admission_create")

    def get_initial(self):
        return {
            "add_admission_group": "Bsc"
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Layout setup
        context = TemplateLayout.init(self, context)
        context["layout"] = "vertical"
        context["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", context)

        group = "Bsc"
        status = "active"

        context["subjects_all"] = DegreeSubjects.objects.filter(
            group=group,
            sub_status=status
        )

        return context

    def form_valid(self, form):
        try:
            program = DegreePrograms.objects.get(deg_name__iexact="Bsc")
            form.instance.add_program = program
            form.instance.add_admission_group = "Bsc"
        except DegreePrograms.DoesNotExist:
            form.add_error(None, "BSc program not found.")
            return self.form_invalid(form)

        # Admission fee (auto-fetch optional)
        form.instance.add_amount = 0  # optionally fetch from Fee

        self.object = form.save()

        selected_subjects = self.request.POST.getlist("subjects")
        if selected_subjects:
            self.object.subjects.set(selected_subjects)

        form.instance.main_subject_id = self.request.POST.get("main_subject")
        self.object.save()

        messages.success(self.request, "✅ BSc admission submitted successfully.")
        return redirect(self.success_url)

    def form_invalid(self, form):
        print("⛔ Form INVALID", form.errors)
        return super().form_invalid(form)


# Bbs
from apps.admissions.forms import DegreeAdmissionForm

class AdmissionBbsCreateView(FormView):
    template_name = "admissions_others/admission_form_honours.html"
    form_class = DegreeAdmissionForm
    success_url = reverse_lazy("bbs_admission_create")

    def get_initial(self):
        return {
            "add_admission_group": "Bbs"
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Layout setup
        context = TemplateLayout.init(self, context)
        context["layout"] = "vertical"
        context["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", context)

        group = "Bbs"
        status = "active"

        context["subjects_all"] = DegreeSubjects.objects.filter(
            group=group,
            sub_status=status
        )

        return context

    def form_valid(self, form):
        try:
            program = DegreePrograms.objects.get(deg_name__iexact="Bbs")
            form.instance.add_program = program
            form.instance.add_admission_group = "Bbs"
        except DegreePrograms.DoesNotExist:
            form.add_error(None, "BBS program not found.")
            return self.form_invalid(form)

        form.instance.add_amount = 0  # optionally: fetch from Fee model

        self.object = form.save()

        selected_subjects = self.request.POST.getlist("subjects")
        if selected_subjects:
            self.object.subjects.set(selected_subjects)

        form.instance.main_subject_id = self.request.POST.get("main_subject")
        self.object.save()

        messages.success(self.request, "✅ BBS admission submitted successfully.")
        return redirect(self.success_url)

    def form_invalid(self, form):
        print("⛔ Form INVALID", form.errors)
        return super().form_invalid(form)







# Fee Section

from django.db.models import Q
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .forms import FeeForm

class FeeListView(ListView):
    template_name = 'admissions/fee_list.html'
    model = Fee
    context_object_name = 'fees'
    paginate_by = 25  # 👈 enable pagination

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filters from GET
        session = self.request.GET.get('session')
        program = self.request.GET.get('program')
        group = self.request.GET.get('group')
        search = self.request.GET.get('search')

        if session:
            queryset = queryset.filter(fee_session_id=session)
        if program:
            queryset = queryset.filter(fee_program_id=program)
        if group:
            queryset = queryset.filter(fee_group_id=group)
        if search:
            queryset = queryset.filter(
                Q(fee_program__pro_name__icontains=search) |
                Q(fee_group__group_name__icontains=search)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = TemplateLayout.init(self, context)
        context["layout"] = "vertical"
        context["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", context)
        context["form"] = FeeForm()

        # For filters
        context['sessions'] = Session.objects.all()
        context['programs'] = Programs.objects.all()
        context['groups'] = Group.objects.all()

        # For repopulating filter fields
        context['search'] = self.request.GET.get('search', '')
        context['selected_session'] = self.request.GET.get('session', '')
        context['selected_program'] = self.request.GET.get('program', '')
        context['selected_group'] = self.request.GET.get('group', '')

        return context


from django.db import IntegrityError

class FeeCreateView(CreateView):
    model = Fee
    form_class = FeeForm
    template_name = 'admissions/fee_list.html'
    success_url = reverse_lazy('fee_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = TemplateLayout.init(self, context)
        context["layout"] = "vertical"
        context["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", context)
        context["fees"] = Fee.objects.all()
        context["sessions"] = Session.objects.all()
        context["programs"] = Programs.objects.all()
        context["groups"] = Group.objects.all()
        return context

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except IntegrityError:
            # Re-render form with error inside fee_list.html
            form.add_error(None, "Fee for this Session, Program, and Group already exists.")
            return self.form_invalid(form)


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
    template_name = None  # 👈 no HTML template used

    def post(self, request, *args, **kwargs):
        messages.success(request, "Fee deleted successfully.")
        return super().post(request, *args, **kwargs)







# Global session filter
from .forms import SessionSelectForm

def set_session_view(request):
    if request.method == 'POST':
        form = SessionSelectForm(request.POST)
        if form.is_valid():
            request.session['active_session_id'] = form.cleaned_data['session'].id
    return redirect(request.META.get('HTTP_REFERER', '/'))
