from django.views.generic.edit import FormView
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.http import JsonResponse

from apps.admissions.forms import HscAdmissionForm
from web_project import TemplateLayout, TemplateHelper

from apps.accounts.utils import role_required
from django.utils.decorators import method_decorator

# @method_decorator(role_required(['master_admin', 'admin', 'sub_admin', 'teacher']), name='dispatch')


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



# (HSC only)

from django.views.generic.edit import FormView
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.db.models import Q, Count
from django.utils.decorators import method_decorator

from apps.accounts.utils import role_required
from web_project import TemplateLayout, TemplateHelper

from .forms import HscAdmissionForm, ArtsAdmissionForm
from .models import HscAdmissions, Subjects, Programs, Fee

# --- helpers ---
def _normalize_bd_mobile(msisdn: str | None) -> str | None:
    """+880/880 prefixed নম্বরকে 01XXXXXXXXX ফরম্যাটে নামাই"""
    if not msisdn:
        return None
    s = str(msisdn).strip()
    s = s.replace('+880', '').replace('880', '')
    if not s.startswith('0'):
        s = '0' + s
    return s

class SingleApplicationGuardMixin:
    """
    student হলে phone_number দিয়ে আগের আবেদন আছে কিনা চেক।
    থাকলে warning সহ details পেজে পাঠায়।
    """
    def dispatch(self, request, *args, **kwargs):
        u = getattr(request, 'user', None)
        if getattr(u, 'is_authenticated', False) and getattr(u, 'role', None) == 'student':
            phone = _normalize_bd_mobile(getattr(u, 'phone_number', '') or '')
            if phone:
                existing = HscAdmissions.objects.filter(add_mobile=phone).order_by('id').first()
                if existing:
                    messages.warning(request, "আপনি ইতিমধ্যে একটি HSC আবেদন করেছেন—নতুন করে আবেদন করা যাবে না। কোন ভুল থাকলে কলেজ থেকে ঠিক করে নিতে হবে ")
                    # details view থাকলে ওটাই; না থাকলে fallback success_url
                    try:
                        return redirect("index")
                        # return redirect("hsc_admission_view", pk=existing.pk)
                    except Exception:
                        return redirect(getattr(self, 'success_url', '/'))
        return super().dispatch(request, *args, **kwargs)


# ------------------ SCIENCE ------------------

from django.utils.decorators import method_decorator
from django.views.generic.edit import FormView
from django.shortcuts import redirect
from django.contrib import messages
from django.db.models import Q
from django.db import transaction
from .models import HscAdmissions, Programs, Subjects, Fee
from .forms import HscAdmissionForm

@method_decorator(
    role_required(['master_admin', 'admin', 'sub_admin', 'teacher', 'student']),
    name='dispatch'
)
class HscAdmissionCreateView(SingleApplicationGuardMixin, FormView):
    """SCIENCE"""
    template_name = "admissions/admission_form.html"
    form_class = HscAdmissionForm
    success_url = reverse_lazy("hsc_admission_create")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user"] = self.request.user
        context = TemplateLayout.init(self, context)
        context["layout"] = "vertical"
        context["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", context)

        group, status = "science", "active"
        context["subjects_all"] = Subjects.objects.filter(sub_status=status, sub_select__contains="all").order_by("sub_name")
        context["subjects_optional"] = Subjects.objects.filter(group=group, sub_status=status, sub_select__contains="optional").order_by("sub_name")
        context["subjects_main"] = Subjects.objects.filter(group=group, sub_status=status, sub_select__contains="main").order_by("sub_name")
        context["subjects_fourth"] = Subjects.objects.filter(group=group, sub_status=status, sub_select__contains="fourth").order_by("sub_name")
        context["admission_group"] = group
        return context

    def form_valid(self, form):
        # Program & group
        try:
            hsc_program = Programs.objects.get(pro_name__iexact="hsc")
            form.instance.add_program = hsc_program
            form.instance.add_admission_group = "science"
        except Programs.DoesNotExist:
            form.add_error(None, "HSC program not found. Please add it from admin.")
            return self.form_invalid(form)

        # Session → Fee (handle disabled field via hidden mirror)
        session_id = self.request.POST.get("add_session") or self.request.POST.get("add_session_hidden")
        try:
            fee = Fee.objects.get(
                fee_session_id=session_id,
                fee_program=hsc_program,
                fee_group__group_name__iexact="science",
            )
            form.instance.add_amount = fee.amount
        except Fee.DoesNotExist:
            form.instance.add_amount = 0

        # Audit trail
        u = self.request.user
        if getattr(u, "is_authenticated", False):
            form.instance.created_by = u
            form.instance.submitted_via = "student_self" if getattr(u, "role", None) == "student" else "staff"
            if getattr(u, "role", None) == "student":
                form.instance.add_mobile = _normalize_bd_mobile(getattr(u, "phone_number", "") or "")
        else:
            form.instance.created_by = None
            form.instance.submitted_via = "api"

        # Subjects (PKs from POST)
        form.instance.main_subject_id = self.request.POST.get("main_subject") or None
        form.instance.fourth_subject_id = self.request.POST.get("fourth_subject") or None

        # Validate unique roll per group
        try:
            with transaction.atomic():
                self.object = form.save()
        except IntegrityError:
            form.add_error('add_class_roll', "এই গ্রুপে এই রোল নম্বর ইতিমধ্যেই আছে।")
            return self.form_invalid(form)

        # Auto-attach "all" + group's "optional"
        subjects_auto = Subjects.objects.filter(sub_status="active").filter(
            Q(sub_select__contains="all") |
            (Q(group="science") & Q(sub_select__contains="optional"))
        )
        self.object.subjects.set(subjects_auto)

        messages.success(self.request, "Science admission submitted successfully.")
        return redirect("hsc_admission_view", pk=self.object.pk)

    def form_invalid(self, form):
        print("⛔ Form INVALID", form.errors)
        return super().form_invalid(form)

# Commrce

from django.views.generic.edit import FormView
from django.shortcuts import redirect
from django.contrib import messages
from django.db.models import Q
from django.db import transaction
from .models import HscAdmissions, Programs, Subjects, Fee
from .forms import HscAdmissionForm

@method_decorator(
    role_required(['master_admin', 'admin', 'sub_admin', 'teacher', 'student']),
    name='dispatch'
)
class HscAdmissionCreateCommerceView(SingleApplicationGuardMixin, FormView):
    """COMMERCE"""
    template_name = "admissions/admission_form_commerce.html"
    form_class = HscAdmissionForm
    success_url = reverse_lazy("hsc_admission_create_commerce")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        kwargs["user"] = self.request.user
        return kwargs

    def get_form(self, form_class=None):
        """
        Commerce এ main_subject selectable নয়, fourth auto-assign হবে।
        তাই এ দুটো field-কে required না রাখি—template থেকেও post নাও আসতে পারে।
        """
        form = super().get_form(form_class)
        if "main_subject" in form.fields:
            form.fields["main_subject"].required = False
        if "fourth_subject" in form.fields:
            form.fields["fourth_subject"].required = False
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = TemplateLayout.init(self, context)
        context["layout"] = "vertical"
        context["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", context)

        group, status = "commerce", "active"
        context["subjects_all"] = Subjects.objects.filter(
            sub_status=status, sub_select__contains="all"
        ).order_by("sub_name")
        context["subjects_optional"] = Subjects.objects.filter(
            group=group, sub_status=status, sub_select__contains="optional"
        ).order_by("sub_name")
        context["subjects_main"] = Subjects.objects.filter(
            group=group, sub_status=status, sub_select__contains="main"
        ).order_by("sub_name")
        context["subjects_fourth"] = Subjects.objects.filter(
            group=group, sub_status=status, sub_select__contains="fourth"
        ).order_by("sub_name")
        context["admission_group"] = group

        # Debugging
        print("subjects_fourth:", list(context["subjects_fourth"].values("id", "sub_name", "sub_select")))
        print("subjects_fourth count:", context["subjects_fourth"].count())
        return context

    def form_valid(self, form):
        # Program & group
        try:
            hsc_program = Programs.objects.get(pro_name__iexact="hsc")
            form.instance.add_program = hsc_program
            form.instance.add_admission_group = "commerce"
        except Programs.DoesNotExist:
            form.add_error(None, "HSC program not found. Please add it from admin.")
            return self.form_invalid(form)

        # Session → Fee (handle disabled field via hidden mirror)
        session_id = self.request.POST.get("add_session") or self.request.POST.get("add_session_hidden")
        try:
            fee = Fee.objects.get(
                fee_session_id=session_id,
                fee_program=hsc_program,
                fee_group__group_name__iexact="commerce",
            )
            form.instance.add_amount = fee.amount
        except Fee.DoesNotExist:
            form.instance.add_amount = 0

        # Audit trail
        u = self.request.user
        if getattr(u, "is_authenticated", False):
            form.instance.created_by = u
            form.instance.submitted_via = "student_self" if getattr(u, "role", None) == "student" else "staff"
            if getattr(u, "role", None) == "student":
                form.instance.add_mobile = _normalize_bd_mobile(getattr(u, "phone_number", "") or "")
        else:
            form.instance.created_by = None
            form.instance.submitted_via = "api"

        # Commerce logic: main_subject ব্যবহার হবে না
        form.instance.main_subject_id = None
        posted_fourth = self.request.POST.get("fourth_subject") or None
        form.instance.fourth_subject_id = posted_fourth

        if not form.instance.fourth_subject_id:
            default_fourth = Subjects.objects.filter(
                group="commerce", sub_status="active", sub_select__contains="fourth"
            ).order_by("sub_name").first()
            if default_fourth:
                form.instance.fourth_subject = default_fourth

        # Validate unique roll per group
        try:
            with transaction.atomic():
                self.object = form.save()
        except IntegrityError:
            form.add_error('add_class_roll', "এই গ্রুপে এই রোল নম্বর ইতিমধ্যেই আছে।")
            return self.form_invalid(form)

        # Auto-attach "all" + group's "optional"
        subjects_auto = Subjects.objects.filter(sub_status="active").filter(
            Q(sub_select__contains="all") |
            (Q(group="commerce") & Q(sub_select__contains="optional"))
        )
        self.object.subjects.set(subjects_auto)

        messages.success(self.request, "Commerce admission submitted successfully.")
        return redirect("hsc_admission_view", pk=self.object.pk)

    def form_invalid(self, form):
        print("⛔ Form INVALID", form.errors)
        return super().form_invalid(form)

# Arts
from django.views.generic.edit import FormView
from django.shortcuts import redirect
from django.contrib import messages
from django.db.models import Q
from django.db import transaction
from django.db.models import Count
from .models import HscAdmissions, Programs, Subjects, Fee
from .forms import ArtsAdmissionForm

@method_decorator(
    role_required(['master_admin', 'admin', 'sub_admin', 'teacher', 'student']),
    name='dispatch'
)
class HscAdmissionCreateArtsView(SingleApplicationGuardMixin, FormView):
    """ARTS"""
    template_name = "admissions/admission_form_arts.html"
    form_class = ArtsAdmissionForm
    success_url = reverse_lazy("hsc_admission_create_arts")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = TemplateLayout.init(self, context)
        context["layout"] = "vertical"
        context["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", context)

        group, status = "arts", "active"
        context["subjects_all"] = Subjects.objects.filter(sub_status=status, sub_select__contains='all').order_by("sub_name")
        context["subjects_optional"] = Subjects.objects.filter(
            group=group, sub_status=status
        ).filter(
            sub_select__contains='optional'
        ).exclude(
            sub_select__contains='optional2'
        ).order_by('sub_name')
        context["subjects_optional2"] = Subjects.objects.filter(group=group, sub_status=status, sub_select__contains='optional2').order_by("sub_name")
        context["subjects_main"] = Subjects.objects.filter(group=group, sub_status=status, sub_select__contains='main').order_by("sub_name")
        context["subjects_fourth"] = Subjects.objects.filter(group=group, sub_status=status, sub_select__contains='fourth').order_by("sub_name")
        context["admission_group"] = group

        # Usage meta (optional)
        qs = HscAdmissions.objects.filter(add_admission_group='arts')
        usage_by_code = {}
        for f in ["main_subject", "fourth_subject", "optional_subject", "optional_subject_2"]:
            for row in qs.values(f"{f}__code").annotate(c=Count('id')):
                code = (row.get(f"{f}__code") or "").strip()
                if code:
                    usage_by_code[code] = usage_by_code.get(code, 0) + row['c']

        def attach_meta(subject_qs):
            for s in subject_qs:
                code = (s.code or "").strip()
                used = getattr(s, "used_count", None) or usage_by_code.get(code, 0)
                s.used = used or 0
                s.left = None if s.limit is None else max(s.limit - s.used, 0)
                s.full = (s.limit is not None) and (s.used >= s.limit)
            return subject_qs

        context["subjects_all"] = attach_meta(context["subjects_all"])
        context["subjects_optional"] = attach_meta(context["subjects_optional"])
        context["subjects_optional2"] = attach_meta(context["subjects_optional2"])
        context["subjects_main"] = attach_meta(context["subjects_main"])
        context["subjects_fourth"] = attach_meta(context["subjects_fourth"])
        return context

    def form_valid(self, form):
        # Prepare instance first (avoid premature save)
        obj = form.save(commit=False)

        # Program & group
        try:
            hsc_program = Programs.objects.get(pro_name__iexact="hsc")
            obj.add_program = hsc_program
            obj.add_admission_group = "arts"
        except Programs.DoesNotExist:
            form.add_error(None, "HSC program not found. Please add it from admin.")
            return self.form_invalid(form)

        # Robust session_id resolve
        session_obj = form.cleaned_data.get("add_session")
        session_id = getattr(session_obj, "id", None) if session_obj else None
        if not session_id:
            session_id = (
                self.request.POST.get("add_session") or
                self.request.POST.get("add_session_hidden") or
                getattr(form.instance, "add_session_id", None)
            )
        if not session_id:
            form.add_error("add_session", "Session missing. Please refresh and try again.")
            return self.form_invalid(form)

        # Server-side fee resolution
        amount = Fee.objects.filter(
            fee_session_id=session_id,
            fee_program=hsc_program,
            fee_group__group_name__iexact="arts",
        ).values_list("amount", flat=True).first()

        if amount is None:
            form.add_error("add_session", "Configured fee not found for this session.")
            return self.form_invalid(form)

        obj.add_amount = amount

        # Audit trail
        u = self.request.user
        if getattr(u, "is_authenticated", False):
            obj.created_by = u
            obj.submitted_via = 'student_self' if getattr(u, 'role', None) == 'student' else 'staff'
            if getattr(u, 'role', None) == 'student':
                obj.add_mobile = _normalize_bd_mobile(getattr(u, 'phone_number', '') or '')
        else:
            obj.created_by = None
            obj.submitted_via = 'api'

        # Subjects (IDs from POST)
        obj.main_subject_id = self.request.POST.get("main_subject") or None
        obj.fourth_subject_id = self.request.POST.get("fourth_subject") or None
        obj.optional_subject_id = self.request.POST.get("optional_subject") or None
        obj.optional_subject_2_id = self.request.POST.get("optional_subject_2") or None

        # Validate unique roll per group
        try:
            with transaction.atomic():
                obj.save()
                self.object = obj
        except IntegrityError:
            form.add_error('add_class_roll', "এই গ্রুপে এই রোল নম্বর ইতিমধ্যেই আছে।")
            return self.form_invalid(form)

        # Attach common subjects (M2M)
        selected_subjects = Subjects.objects.filter(sub_status="active", sub_select__contains='all')
        self.object.subjects.set(selected_subjects)

        messages.success(self.request, "Arts admission submitted successfully.")
        return redirect("hsc_admission_view", pk=self.object.pk)

    def form_invalid(self, form):
        print("⛔ Form INVALID", form.errors)
        return super().form_invalid(form)


# Honours Admission Section

from django.views.generic.edit import FormView
from django.urls import reverse_lazy

from apps.admissions.forms import DegreeAdmissionForm
from apps.admissions.models import DegreePrograms, DegreeSubjects

# BA
@method_decorator(role_required(['master_admin', 'admin', 'sub_admin', 'teacher', 'student']), name='dispatch')
class AdmissionBaCreateView(FormView):
    template_name = "admissions_others/admission_form_honours.html"
    form_class = DegreeAdmissionForm
    success_url = reverse_lazy("ba_admission_create")

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["request"] = self.request
        return kw

    def get_initial(self):
        return {"add_admission_group": "Ba"}

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx = TemplateLayout.init(self, ctx)
        ctx["layout"] = "vertical"
        ctx["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", ctx)
        ctx["subjects_all"] = DegreeSubjects.objects.filter(group="Ba", sub_status="active")
        return ctx

    def form_valid(self, form):
        # program & group
        try:
            prog = DegreePrograms.objects.get(deg_name__iexact="Ba")
            form.instance.add_program = prog
            form.instance.add_admission_group = "Ba"
        except DegreePrograms.DoesNotExist:
            form.add_error(None, "BA program not found.")
            return self.form_invalid(form)

        # fee (optional; falls back to 0)
        session_id = self.request.POST.get("add_session")
        try:
            degree_program = Programs.objects.get(pro_name__iexact="degree")
            fee = Fee.objects.get(fee_session_id=session_id, fee_program=degree_program, fee_group__group_name__iexact="Ba")
            form.instance.add_amount = fee.amount
        except Exception:
            form.instance.add_amount = 0

        # audit
        u = self.request.user
        form.instance.created_by = u if getattr(u, "is_authenticated", False) else None
        form.instance.submitted_via = 'student_self' if getattr(u, 'role', None) == 'student' else 'staff'

        # main subject (FK)
        form.instance.main_subject_id = self.request.POST.get("main_subject") or None

        self.object = form.save()

        # M2M subjects
        selected_subjects = self.request.POST.getlist("subjects")
        if selected_subjects:
            self.object.subjects.set(selected_subjects)

        messages.success(self.request, "✅ BA admission submitted successfully.")
        return redirect(self.success_url)

    def form_invalid(self, form):
        print("Form invalid:", form.errors)
        return super().form_invalid(form)


# BSS
@method_decorator(role_required(['master_admin', 'admin', 'sub_admin', 'teacher', 'student']), name='dispatch')
class AdmissionBssCreateView(FormView):
    template_name = "admissions_others/admission_form_honours.html"
    form_class = DegreeAdmissionForm
    success_url = reverse_lazy("bss_admission_create")

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["request"] = self.request
        return kw

    def get_initial(self):
        return {"add_admission_group": "Bss"}

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx = TemplateLayout.init(self, ctx)
        ctx["layout"] = "vertical"
        ctx["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", ctx)
        ctx["subjects_all"] = DegreeSubjects.objects.filter(group="Bss", sub_status="active")
        return ctx

    def form_valid(self, form):
        try:
            prog = DegreePrograms.objects.get(deg_name__iexact="Bss")
            form.instance.add_program = prog
            form.instance.add_admission_group = "Bss"
        except DegreePrograms.DoesNotExist:
            form.add_error(None, "BSS program not found.")
            return self.form_invalid(form)

        session_id = self.request.POST.get("add_session")
        try:
            degree_program = Programs.objects.get(pro_name__iexact="degree")
            fee = Fee.objects.get(fee_session_id=session_id, fee_program=degree_program, fee_group__group_name__iexact="Bss")
            form.instance.add_amount = fee.amount
        except Exception:
            form.instance.add_amount = 0

        u = self.request.user
        form.instance.created_by = u if getattr(u, "is_authenticated", False) else None
        form.instance.submitted_via = 'student_self' if getattr(u, 'role', None) == 'student' else 'staff'

        form.instance.main_subject_id = self.request.POST.get("main_subject") or None

        self.object = form.save()

        selected_subjects = self.request.POST.getlist("subjects")
        if selected_subjects:
            self.object.subjects.set(selected_subjects)

        messages.success(self.request, "✅ BSS admission submitted successfully.")
        return redirect(self.success_url)

    def form_invalid(self, form):
        print("Form invalid:", form.errors)
        return super().form_invalid(form)


# BSC
@method_decorator(role_required(['master_admin', 'admin', 'sub_admin', 'teacher', 'student']), name='dispatch')
class AdmissionBscCreateView(FormView):
    template_name = "admissions_others/admission_form_honours.html"
    form_class = DegreeAdmissionForm
    success_url = reverse_lazy("bsc_admission_create")

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["request"] = self.request
        return kw

    def get_initial(self):
        return {"add_admission_group": "Bsc"}

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx = TemplateLayout.init(self, ctx)
        ctx["layout"] = "vertical"
        ctx["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", ctx)
        ctx["subjects_all"] = DegreeSubjects.objects.filter(group="Bsc", sub_status="active")
        return ctx

    def form_valid(self, form):
        try:
            prog = DegreePrograms.objects.get(deg_name__iexact="Bsc")
            form.instance.add_program = prog
            form.instance.add_admission_group = "Bsc"
        except DegreePrograms.DoesNotExist:
            form.add_error(None, "BSc program not found.")
            return self.form_invalid(form)

        session_id = self.request.POST.get("add_session")
        try:
            degree_program = Programs.objects.get(pro_name__iexact="degree")
            fee = Fee.objects.get(fee_session_id=session_id, fee_program=degree_program, fee_group__group_name__iexact="Bsc")
            form.instance.add_amount = fee.amount
        except Exception:
            form.instance.add_amount = 0

        u = self.request.user
        form.instance.created_by = u if getattr(u, "is_authenticated", False) else None
        form.instance.submitted_via = 'student_self' if getattr(u, 'role', None) == 'student' else 'staff'

        form.instance.main_subject_id = self.request.POST.get("main_subject") or None

        self.object = form.save()

        selected_subjects = self.request.POST.getlist("subjects")
        if selected_subjects:
            self.object.subjects.set(selected_subjects)

        messages.success(self.request, "✅ BSc admission submitted successfully.")
        return redirect(self.success_url)

    def form_invalid(self, form):
        print("⛔ Form INVALID", form.errors)
        return super().form_invalid(form)


# BBS
@method_decorator(role_required(['master_admin', 'admin', 'sub_admin', 'teacher', 'student']), name='dispatch')
class AdmissionBbsCreateView(FormView):
    template_name = "admissions_others/admission_form_honours.html"
    form_class = DegreeAdmissionForm
    success_url = reverse_lazy("bbs_admission_create")

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["request"] = self.request
        return kw

    def get_initial(self):
        return {"add_admission_group": "Bbs"}

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx = TemplateLayout.init(self, ctx)
        ctx["layout"] = "vertical"
        ctx["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", ctx)
        ctx["subjects_all"] = DegreeSubjects.objects.filter(group="Bbs", sub_status="active")
        return ctx

    def form_valid(self, form):
        try:
            prog = DegreePrograms.objects.get(deg_name__iexact="Bbs")
            form.instance.add_program = prog
            form.instance.add_admission_group = "Bbs"
        except DegreePrograms.DoesNotExist:
            form.add_error(None, "BBS program not found.")
            return self.form_invalid(form)

        session_id = self.request.POST.get("add_session")
        try:
            degree_program = Programs.objects.get(pro_name__iexact="degree")
            fee = Fee.objects.get(fee_session_id=session_id, fee_program=degree_program, fee_group__group_name__iexact="Bbs")
            form.instance.add_amount = fee.amount
        except Exception:
            form.instance.add_amount = 0

        u = self.request.user
        form.instance.created_by = u if getattr(u, "is_authenticated", False) else None
        form.instance.submitted_via = 'student_self' if getattr(u, 'role', None) == 'student' else 'staff'

        form.instance.main_subject_id = self.request.POST.get("main_subject") or None

        self.object = form.save()

        selected_subjects = self.request.POST.getlist("subjects")
        if selected_subjects:
            self.object.subjects.set(selected_subjects)

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

@method_decorator(role_required(['master_admin', 'admin', 'sub_admin', 'teacher']), name='dispatch')
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

        return queryset.order_by('-id')

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

@method_decorator(role_required(['master_admin', 'admin', 'sub_admin']), name='dispatch')
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

@method_decorator(role_required(['master_admin', 'admin']), name='dispatch')
class FeeUpdateView(UpdateView):
    model = Fee
    form_class = FeeForm
    success_url = reverse_lazy('fee_list')

    def form_valid(self, form):
        messages.success(self.request, "Fee updated successfully.")
        return super().form_valid(form)
    
from django.shortcuts import redirect, get_object_or_404
from django.views.decorators.http import require_POST


@require_POST
def fee_update(request, pk):
    fee = get_object_or_404(Fee, pk=pk)
    form = FeeForm(request.POST, instance=fee)
    if form.is_valid():
        form.save()
        messages.success(request, "Fee updated successfully.")
    else:
        print("⛔ Fee update form errors:", form.errors)  # ← log errors
        messages.error(request, "Failed to update fee.")
    return redirect('fee_list')


@method_decorator(role_required(['master_admin', 'admin']), name='dispatch')
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
