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
from .models import HscAdmissions, Subjects, Programs, Fee, DegreeAdmission

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


class DegreeSingleApplicationGuardMixin:
    """
    student হলে phone_number দিয়ে আগের আবেদন আছে কিনা চেক।
    থাকলে warning সহ details পেজে পাঠায়।
    """
    def dispatch(self, request, *args, **kwargs):
        u = getattr(request, 'user', None)
        if getattr(u, 'is_authenticated', False) and getattr(u, 'role', None) == 'student':
            phone = _normalize_bd_mobile(getattr(u, 'phone_number', '') or '')
            if phone:
                existing = DegreeAdmission.objects.filter(add_mobile=phone).order_by('id').first()
                if existing:
                    messages.warning(request, "আপনি ইতিমধ্যে একটি Degree আবেদন করেছেন—নতুন করে আবেদন করা যাবে না। কোন ভুল থাকলে কলেজ থেকে ঠিক করে নিতে হবে ")
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
from django.views.generic.edit import UpdateView

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

        # Session → Fee (use cleaned data instead of POST directly)
        session = form.cleaned_data['add_session']
        if not session:
            form.add_error('add_session', "Session is required.")
            return self.form_invalid(form)
        form.instance.add_session = session  # Explicitly set session
        print("Saving session ID:", session.pk)  # Debug to check session ID

        try:
            fee = Fee.objects.get(
                fee_session=session,  # Use session object directly
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

        messages.success(self.request, "Business Studies admission submitted successfully.")
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

        messages.success(self.request, "Humanities admission submitted successfully.")
        return redirect("hsc_admission_view", pk=self.object.pk)

    def form_invalid(self, form):
        print("⛔ Form INVALID", form.errors)
        return super().form_invalid(form)

# Degree Admission Section

from django.views.generic.edit import FormView
from django.urls import reverse_lazy

from apps.admissions.forms import DegreeAdmissionForm
from apps.admissions.models import DegreePrograms, DegreeSubjects


@method_decorator(
    role_required(['master_admin', 'admin', 'sub_admin', 'teacher', 'student']),
    name='dispatch'
)
class AdmissionBaCreateView(DegreeSingleApplicationGuardMixin, FormView):
    template_name = "admissions_others/admission_form_honours.html"
    form_class = DegreeAdmissionForm
    success_url = reverse_lazy("ba_admission_create")

    # ---- constants ----
    GROUP = "Ba"          # DegreeSubjects.group MultiSelect-এ "Ba" ট্যাগ
    DEG_NAME = "Ba"       # DegreePrograms.deg_name
    MAX_SELECTABLE = 3    # compulsory বাদে মোট ৩টি

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["request"] = self.request
        kw["user"] = getattr(self.request, "user", None)
        return kw

    def get_initial(self):
        ini = super().get_initial()
        ini["add_admission_group"] = self.GROUP
        return ini

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx = TemplateLayout.init(self, ctx)
        ctx["layout"] = "vertical"
        ctx["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", ctx)

        # Compulsory: All/All
        compulsory_qs = DegreeSubjects.objects.filter(
            sub_status="active",
            group__contains="All",
            sub_select__contains="all",
        ).order_by("sub_name")

        # Selectable: (Ba OR All) AND NOT (All/All)
        selectable_qs = DegreeSubjects.objects.filter(
            sub_status="active"
        ).filter(
            Q(group__contains=self.GROUP) | Q(group__contains="All")
        ).exclude(
            Q(group__contains="All") & Q(sub_select__contains="all")
        )

        def slot_qs(tag: str):
            return selectable_qs.filter(sub_select__contains=tag).order_by("sub_name")

        ctx["subjects_compulsory"] = compulsory_qs
        ctx["subjects_by_slot"] = {
            "main": slot_qs("main"),
            "op1":  slot_qs("op1"),
            "op2":  slot_qs("op2"),
            "op3":  slot_qs("op3"),
            "op4":  slot_qs("op4"),
        }
        ctx["group_name"] = self.GROUP
        ctx["max_selectable"] = self.MAX_SELECTABLE
        return ctx

    def form_valid(self, form):
        # ---- Program & group ----
        try:
            prog = DegreePrograms.objects.get(deg_name__iexact=self.DEG_NAME)
        except DegreePrograms.DoesNotExist:
            form.add_error(None, f"{self.DEG_NAME} program not found.")
            return self.form_invalid(form)

        form.instance.add_program = prog
        form.instance.add_admission_group = self.GROUP

        # ---- Session (ফর্মের clean থেকে locked session আসবে) ----
        session = form.cleaned_data.get("add_session")
        if not session:
            form.add_error("add_session", "Session is required.")
            return self.form_invalid(form)
        form.instance.add_session = session

        # ---- Fee resolve (server-side authoritative) ----
        try:
            degree_program = Programs.objects.get(pro_name__iexact="degree")
            fee = Fee.objects.get(
                fee_session=session,
                fee_program=degree_program,
                fee_group__group_name__iexact=self.GROUP
            )
            form.instance.add_amount = fee.amount
        except (Programs.DoesNotExist, Fee.DoesNotExist):
            form.instance.add_amount = 0

        # ---- Audit trail ----
        u = self.request.user
        if getattr(u, "is_authenticated", False):
            form.instance.created_by = u
            form.instance.submitted_via = "student_self" if getattr(u, "role", None) == "student" else "staff"
        else:
            form.instance.created_by = None
            form.instance.submitted_via = "api"

        # ---- Save + Subject handling ----
        posted_ids = [int(x) for x in self.request.POST.getlist("subjects") if str(x).isdigit()]

        # Compulsory IDs (All/All) — সবসময় যোগ হবে
        compulsory_ids = list(
            DegreeSubjects.objects.filter(
                sub_status="active",
                group__contains="All",
                sub_select__contains="all",
            ).values_list("id", flat=True)
        )

        # Posted selectable (Ba|All) থেকে, কিন্তু All/All বাদ
        posted_qs = DegreeSubjects.objects.filter(
            id__in=posted_ids,
            sub_status="active",
        ).filter(
            Q(group__contains=self.GROUP) | Q(group__contains="All")
        ).exclude(
            Q(group__contains="All") & Q(sub_select__contains="all")
        )

        # ---- Server-side validation: প্রতি slot ≤ 1 এবং মোট ঠিক ৩টি ----
        slot_tags = ("main", "op1", "op2", "op3", "op4")
        # প্রতি স্লটে কয়টা করে আছে
        slot_counts = {t: 0 for t in slot_tags}
        for s in posted_qs:
            tags = set(s.sub_select or [])
            for t in slot_tags:
                if t in tags:
                    slot_counts[t] += 1

        errs = []
        for t, c in slot_counts.items():
            if c > 1:
                errs.append(f"‘{t.upper()}’ থেকে একটির বেশি নির্বাচন করা যাবে না।")

        total_selected = posted_qs.count()  # compulsory বাদে ক’টি নেয়া হয়েছে
        if total_selected != self.MAX_SELECTABLE:
            errs.append(f"compulsory বাদে ঠিক {self.MAX_SELECTABLE}টি বিষয় নির্বাচন করতে হবে।")

        if errs:
            for e in errs:
                form.add_error(None, e)
            return self.form_invalid(form)

        # ---- সব ঠিক থাকলে সেভ ----
        try:
            with transaction.atomic():
                obj = form.save()

                # M2M set: compulsory + posted
                final_ids = compulsory_ids + list(posted_qs.values_list("id", flat=True))
                obj.subjects.set(final_ids)

                # FK auto-assign: posted থেকে স্লট অনুযায়ী প্রথমটিকে বসানো
                slot_first = {}
                for s in posted_qs:
                    tags = set(s.sub_select or [])
                    for t in slot_tags:
                        if t in tags and t not in slot_first:
                            slot_first[t] = s

                obj.main_subject = slot_first.get("main")
                obj.op1 = slot_first.get("op1")
                obj.op2 = slot_first.get("op2")
                obj.op3 = slot_first.get("op3")
                obj.op4 = slot_first.get("op4")
                obj.save()

        except IntegrityError:
            form.add_error("add_class_roll", "এই গ্রুপে এই রোল নম্বর ইতিমধ্যেই আছে।")
            return self.form_invalid(form)

        messages.success(self.request, "✅ BA admission submitted successfully.")
        return redirect(self.success_url)

    def form_invalid(self, form):
        # ডিবাগ সহায়তা
        print("Form invalid:", form.errors)
        return super().form_invalid(form)


# BSS
@method_decorator(
    role_required(['master_admin', 'admin', 'sub_admin', 'teacher', 'student']),
    name='dispatch'
)
class AdmissionBssCreateView(DegreeSingleApplicationGuardMixin, FormView):
    template_name = "admissions_others/admission_form_honours.html"
    form_class = DegreeAdmissionForm
    success_url = reverse_lazy("bss_admission_create")

    # ---- constants ----
    GROUP = "Bss"
    DEG_NAME = "Bss"
    MAX_SELECTABLE = 3  # compulsory বাদে মোট ৩টি

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["request"] = self.request
        kw["user"] = getattr(self.request, "user", None)
        return kw

    def get_initial(self):
        ini = super().get_initial()
        ini["add_admission_group"] = self.GROUP
        return ini

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx = TemplateLayout.init(self, ctx)
        ctx["layout"] = "vertical"
        ctx["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", ctx)

        compulsory_qs = DegreeSubjects.objects.filter(
            sub_status="active",
            group__contains="All",
            sub_select__contains="all",
        ).order_by("sub_name")

        selectable_qs = DegreeSubjects.objects.filter(
            sub_status="active"
        ).filter(
            Q(group__contains=self.GROUP) | Q(group__contains="All")
        ).exclude(
            Q(group__contains="All") & Q(sub_select__contains="all")
        )

        def slot_qs(tag: str):
            return selectable_qs.filter(sub_select__contains=tag).order_by("sub_name")

        ctx["subjects_compulsory"] = compulsory_qs
        ctx["subjects_by_slot"] = {
            "main": slot_qs("main"),
            "op1":  slot_qs("op1"),
            "op2":  slot_qs("op2"),
            "op3":  slot_qs("op3"),
            "op4":  slot_qs("op4"),
        }
        ctx["group_name"] = self.GROUP
        ctx["max_selectable"] = self.MAX_SELECTABLE
        return ctx

    def form_valid(self, form):
        # ---- Program & group ----
        try:
            prog = DegreePrograms.objects.get(deg_name__iexact=self.DEG_NAME)
        except DegreePrograms.DoesNotExist:
            form.add_error(None, f"{self.DEG_NAME} program not found.")
            return self.form_invalid(form)

        form.instance.add_program = prog
        form.instance.add_admission_group = self.GROUP

        # ---- Session (locked in form.clean) ----
        session = form.cleaned_data.get("add_session")
        if not session:
            form.add_error("add_session", "Session is required.")
            return self.form_invalid(form)
        form.instance.add_session = session

        # ---- Fee resolve ----
        try:
            degree_program = Programs.objects.get(pro_name__iexact="degree")
            fee = Fee.objects.get(
                fee_session=session,
                fee_program=degree_program,
                fee_group__group_name__iexact=self.GROUP
            )
            form.instance.add_amount = fee.amount
        except (Programs.DoesNotExist, Fee.DoesNotExist):
            form.instance.add_amount = 0

        # ---- Audit ----
        u = self.request.user
        if getattr(u, "is_authenticated", False):
            form.instance.created_by = u
            form.instance.submitted_via = "student_self" if getattr(u, "role", None) == "student" else "staff"
        else:
            form.instance.created_by = None
            form.instance.submitted_via = "api"

        # ---- Subjects (posted) ----
        posted_ids = [int(x) for x in self.request.POST.getlist("subjects") if str(x).isdigit()]

        compulsory_ids = list(
            DegreeSubjects.objects.filter(
                sub_status="active",
                group__contains="All",
                sub_select__contains="all",
            ).values_list("id", flat=True)
        )

        posted_qs = DegreeSubjects.objects.filter(
            id__in=posted_ids, sub_status="active"
        ).filter(
            Q(group__contains=self.GROUP) | Q(group__contains="All")
        ).exclude(
            Q(group__contains="All") & Q(sub_select__contains="all")
        )

        # ---- Server-side validation ----
        slot_tags = ("main", "op1", "op2", "op3", "op4")
        MULTI_SLOTS = {"op1", "op3"}        # A, C multi
        SINGLE_SLOTS = set(slot_tags) - MULTI_SLOTS  # main, op2, op4

        slot_counts = {t: 0 for t in slot_tags}
        for s in posted_qs:
            tags = set(s.sub_select or [])
            for t in slot_tags:
                if t in tags:
                    slot_counts[t] += 1

        errs = []
        for t in SINGLE_SLOTS:
            if slot_counts[t] > 1:
                errs.append(f"‘{t.upper()}’ থেকে একটির বেশি নির্বাচন করা যাবে না।")

        total_selected = posted_qs.count()
        if total_selected != self.MAX_SELECTABLE:
            errs.append(f"compulsory বাদে ঠিক {self.MAX_SELECTABLE}টি বিষয় নির্বাচন করতে হবে।")

        if errs:
            for e in errs:
                form.add_error(None, e)
            return self.form_invalid(form)

        # ---- Save ----
        try:
            with transaction.atomic():
                obj = form.save()

                final_ids = compulsory_ids + list(posted_qs.values_list("id", flat=True))
                obj.subjects.set(final_ids)

                slot_first = {}
                for s in posted_qs:
                    tags = set(s.sub_select or [])
                    for t in slot_tags:
                        if t in tags and t not in slot_first:
                            slot_first[t] = s

                obj.main_subject = slot_first.get("main")
                obj.op1 = slot_first.get("op1")
                obj.op2 = slot_first.get("op2")
                obj.op3 = slot_first.get("op3")
                obj.op4 = slot_first.get("op4")
                obj.save()

        except IntegrityError:
            form.add_error("add_class_roll", "এই গ্রুপে এই রোল নম্বর ইতিমধ্যেই আছে।")
            return self.form_invalid(form)

        messages.success(self.request, "✅ BSS admission submitted successfully.")
        return redirect(self.success_url)

    def form_invalid(self, form):
        print("Form invalid:", form.errors)
        return super().form_invalid(form)


# BSC
@method_decorator(
    role_required(['master_admin', 'admin', 'sub_admin', 'teacher', 'student']),
    name='dispatch'
)
class AdmissionBscCreateView(DegreeSingleApplicationGuardMixin, FormView):
    template_name = "admissions_others/admission_form_honours.html"
    form_class = DegreeAdmissionForm
    success_url = reverse_lazy("bsc_admission_create")

    GROUP = "Bsc"
    DEG_NAME = "Bsc"
    MAX_SELECTABLE = 3

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["request"] = self.request
        kw["user"] = getattr(self.request, "user", None)
        return kw

    def get_initial(self):
        ini = super().get_initial()
        ini["add_admission_group"] = self.GROUP
        return ini

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx = TemplateLayout.init(self, ctx)
        ctx["layout"] = "vertical"
        ctx["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", ctx)

        compulsory_qs = DegreeSubjects.objects.filter(
            sub_status="active", group__contains="All", sub_select__contains="all"
        ).order_by("sub_name")

        selectable_qs = DegreeSubjects.objects.filter(
            sub_status="active"
        ).filter(
            Q(group__contains=self.GROUP) | Q(group__contains="All")
        ).exclude(
            Q(group__contains="All") & Q(sub_select__contains="all")
        )

        def slot_qs(tag: str):
            return selectable_qs.filter(sub_select__contains=tag).order_by("sub_name")

        ctx["subjects_compulsory"] = compulsory_qs
        ctx["subjects_by_slot"] = {
            "main": slot_qs("main"),
            "op1":  slot_qs("op1"),
            "op2":  slot_qs("op2"),
            "op3":  slot_qs("op3"),
            "op4":  slot_qs("op4"),
        }
        ctx["group_name"] = self.GROUP
        ctx["max_selectable"] = self.MAX_SELECTABLE
        return ctx

    def form_valid(self, form):
        try:
            prog = DegreePrograms.objects.get(deg_name__iexact=self.DEG_NAME)
        except DegreePrograms.DoesNotExist:
            form.add_error(None, f"{self.DEG_NAME} program not found.")
            return self.form_invalid(form)

        form.instance.add_program = prog
        form.instance.add_admission_group = self.GROUP

        session = form.cleaned_data.get("add_session")
        if not session:
            form.add_error("add_session", "Session is required.")
            return self.form_invalid(form)
        form.instance.add_session = session

        try:
            degree_program = Programs.objects.get(pro_name__iexact="degree")
            fee = Fee.objects.get(
                fee_session=session,
                fee_program=degree_program,
                fee_group__group_name__iexact=self.GROUP
            )
            form.instance.add_amount = fee.amount
        except (Programs.DoesNotExist, Fee.DoesNotExist):
            form.instance.add_amount = 0

        u = self.request.user
        if getattr(u, "is_authenticated", False):
            form.instance.created_by = u
            form.instance.submitted_via = "student_self" if getattr(u, "role", None) == "student" else "staff"
        else:
            form.instance.created_by = None
            form.instance.submitted_via = "api"

        posted_ids = [int(x) for x in self.request.POST.getlist("subjects") if str(x).isdigit()]

        compulsory_ids = list(
            DegreeSubjects.objects.filter(
                sub_status="active", group__contains="All", sub_select__contains="all"
            ).values_list("id", flat=True)
        )

        posted_qs = DegreeSubjects.objects.filter(
            id__in=posted_ids, sub_status="active"
        ).filter(
            Q(group__contains=self.GROUP) | Q(group__contains="All")
        ).exclude(
            Q(group__contains="All") & Q(sub_select__contains="all")
        )

        slot_tags = ("main", "op1", "op2", "op3", "op4")
        MULTI_SLOTS = {"op1", "op3"}
        SINGLE_SLOTS = set(slot_tags) - MULTI_SLOTS

        slot_counts = {t: 0 for t in slot_tags}
        for s in posted_qs:
            tags = set(s.sub_select or [])
            for t in slot_tags:
                if t in tags:
                    slot_counts[t] += 1

        errs = []
        for t in SINGLE_SLOTS:
            if slot_counts[t] > 1:
                errs.append(f"‘{t.upper()}’ থেকে একটির বেশি নির্বাচন করা যাবে না।")

        total_selected = posted_qs.count()
        if total_selected != self.MAX_SELECTABLE:
            errs.append(f"compulsory বাদে ঠিক {self.MAX_SELECTABLE}টি বিষয় নির্বাচন করতে হবে।")

        if errs:
            for e in errs:
                form.add_error(None, e)
            return self.form_invalid(form)

        try:
            with transaction.atomic():
                obj = form.save()
                final_ids = compulsory_ids + list(posted_qs.values_list("id", flat=True))
                obj.subjects.set(final_ids)

                slot_first = {}
                for s in posted_qs:
                    tags = set(s.sub_select or [])
                    for t in slot_tags:
                        if t in tags and t not in slot_first:
                            slot_first[t] = s

                obj.main_subject = slot_first.get("main")
                obj.op1 = slot_first.get("op1")
                obj.op2 = slot_first.get("op2")
                obj.op3 = slot_first.get("op3")
                obj.op4 = slot_first.get("op4")
                obj.save()

        except IntegrityError:
            form.add_error("add_class_roll", "এই গ্রুপে এই রোল নম্বর ইতিমধ্যেই আছে।")
            return self.form_invalid(form)

        messages.success(self.request, "✅ BSc admission submitted successfully.")
        return redirect(self.success_url)

    def form_invalid(self, form):
        print("Form invalid:", form.errors)
        return super().form_invalid(form)


# BBS
@method_decorator(
    role_required(['master_admin', 'admin', 'sub_admin', 'teacher', 'student']),
    name='dispatch'
)
class AdmissionBbsCreateView(DegreeSingleApplicationGuardMixin, FormView):
    template_name = "admissions_others/admission_form_honours.html"
    form_class = DegreeAdmissionForm
    success_url = reverse_lazy("bbs_admission_create")

    GROUP = "Bbs"
    DEG_NAME = "Bbs"
    MAX_SELECTABLE = 3

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["request"] = self.request
        kw["user"] = getattr(self.request, "user", None)
        return kw

    def get_initial(self):
        ini = super().get_initial()
        ini["add_admission_group"] = self.GROUP
        return ini

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx = TemplateLayout.init(self, ctx)
        ctx["layout"] = "vertical"
        ctx["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", ctx)

        compulsory_qs = DegreeSubjects.objects.filter(
            sub_status="active", group__contains="All", sub_select__contains="all"
        ).order_by("sub_name")

        selectable_qs = DegreeSubjects.objects.filter(
            sub_status="active"
        ).filter(
            Q(group__contains=self.GROUP) | Q(group__contains="All")
        ).exclude(
            Q(group__contains="All") & Q(sub_select__contains="all")
        )

        def slot_qs(tag: str):
            return selectable_qs.filter(sub_select__contains=tag).order_by("sub_name")

        ctx["subjects_compulsory"] = compulsory_qs
        ctx["subjects_by_slot"] = {
            "main": slot_qs("main"),
            "op1":  slot_qs("op1"),
            "op2":  slot_qs("op2"),
            "op3":  slot_qs("op3"),
            "op4":  slot_qs("op4"),
        }
        ctx["group_name"] = self.GROUP
        ctx["max_selectable"] = self.MAX_SELECTABLE
        return ctx

    def form_valid(self, form):
        try:
            prog = DegreePrograms.objects.get(deg_name__iexact=self.DEG_NAME)
        except DegreePrograms.DoesNotExist:
            form.add_error(None, f"{self.DEG_NAME} program not found.")
            return self.form_invalid(form)

        form.instance.add_program = prog
        form.instance.add_admission_group = self.GROUP

        session = form.cleaned_data.get("add_session")
        if not session:
            form.add_error("add_session", "Session is required.")
            return self.form_invalid(form)
        form.instance.add_session = session

        try:
            degree_program = Programs.objects.get(pro_name__iexact="degree")
            fee = Fee.objects.get(
                fee_session=session,
                fee_program=degree_program,
                fee_group__group_name__iexact=self.GROUP
            )
            form.instance.add_amount = fee.amount
        except (Programs.DoesNotExist, Fee.DoesNotExist):
            form.instance.add_amount = 0

        u = self.request.user
        if getattr(u, "is_authenticated", False):
            form.instance.created_by = u
            form.instance.submitted_via = "student_self" if getattr(u, "role", None) == "student" else "staff"
        else:
            form.instance.created_by = None
            form.instance.submitted_via = "api"

        posted_ids = [int(x) for x in self.request.POST.getlist("subjects") if str(x).isdigit()]

        compulsory_ids = list(
            DegreeSubjects.objects.filter(
                sub_status="active", group__contains="All", sub_select__contains="all"
            ).values_list("id", flat=True)
        )

        posted_qs = DegreeSubjects.objects.filter(
            id__in=posted_ids, sub_status="active"
        ).filter(
            Q(group__contains=self.GROUP) | Q(group__contains="All")
        ).exclude(
            Q(group__contains="All") & Q(sub_select__contains="all")
        )

        slot_tags = ("main", "op1", "op2", "op3", "op4")
        MULTI_SLOTS = {"op1", "op3"}
        SINGLE_SLOTS = set(slot_tags) - MULTI_SLOTS

        slot_counts = {t: 0 for t in slot_tags}
        for s in posted_qs:
            tags = set(s.sub_select or [])
            for t in slot_tags:
                if t in tags:
                    slot_counts[t] += 1

        errs = []
        for t in SINGLE_SLOTS:
            if slot_counts[t] > 1:
                errs.append(f"‘{t.upper()}’ থেকে একটির বেশি নির্বাচন করা যাবে না।")

        total_selected = posted_qs.count()
        if total_selected != self.MAX_SELECTABLE:
            errs.append(f"compulsory বাদে ঠিক {self.MAX_SELECTABLE}টি বিষয় নির্বাচন করতে হবে।")

        if errs:
            for e in errs:
                form.add_error(None, e)
            return self.form_invalid(form)

        try:
            with transaction.atomic():
                obj = form.save()
                final_ids = compulsory_ids + list(posted_qs.values_list("id", flat=True))
                obj.subjects.set(final_ids)

                slot_first = {}
                for s in posted_qs:
                    tags = set(s.sub_select or [])
                    for t in slot_tags:
                        if t in tags and t not in slot_first:
                            slot_first[t] = s

                obj.main_subject = slot_first.get("main")
                obj.op1 = slot_first.get("op1")
                obj.op2 = slot_first.get("op2")
                obj.op3 = slot_first.get("op3")
                obj.op4 = slot_first.get("op4")
                obj.save()

        except IntegrityError:
            form.add_error("add_class_roll", "এই গ্রুপে এই রোল নম্বর ইতিমধ্যেই আছে।")
            return self.form_invalid(form)

        messages.success(self.request, "✅ BBS admission submitted successfully.")
        return redirect(self.success_url)

    def form_invalid(self, form):
        print("Form invalid:", form.errors)
        return super().form_invalid(form)


# BSS
# @method_decorator(role_required(['master_admin', 'admin', 'sub_admin', 'teacher', 'student']), name='dispatch')
# class AdmissionBssCreateView(FormView):
#     template_name = "admissions_others/admission_form_honours.html"
#     form_class = DegreeAdmissionForm
#     success_url = reverse_lazy("bss_admission_create")

#     def get_form_kwargs(self):
#         kw = super().get_form_kwargs()
#         kw["request"] = self.request
#         return kw

#     def get_initial(self):
#         return {"add_admission_group": "Bss"}

#     def get_context_data(self, **kwargs):
#         ctx = super().get_context_data(**kwargs)
#         ctx = TemplateLayout.init(self, ctx)
#         ctx["layout"] = "vertical"
#         ctx["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", ctx)
#         ctx["subjects_all"] = DegreeSubjects.objects.filter(group="Bss", sub_status="active")
#         return ctx

#     def form_valid(self, form):
#         try:
#             prog = DegreePrograms.objects.get(deg_name__iexact="Bss")
#             form.instance.add_program = prog
#             form.instance.add_admission_group = "Bss"
#         except DegreePrograms.DoesNotExist:
#             form.add_error(None, "BSS program not found.")
#             return self.form_invalid(form)

#         session_id = self.request.POST.get("add_session")
#         try:
#             degree_program = Programs.objects.get(pro_name__iexact="degree")
#             fee = Fee.objects.get(fee_session_id=session_id, fee_program=degree_program, fee_group__group_name__iexact="Bss")
#             form.instance.add_amount = fee.amount
#         except Exception:
#             form.instance.add_amount = 0

#         u = self.request.user
#         form.instance.created_by = u if getattr(u, "is_authenticated", False) else None
#         form.instance.submitted_via = 'student_self' if getattr(u, 'role', None) == 'student' else 'staff'

#         form.instance.main_subject_id = self.request.POST.get("main_subject") or None

#         self.object = form.save()

#         selected_subjects = self.request.POST.getlist("subjects")
#         if selected_subjects:
#             self.object.subjects.set(selected_subjects)

#         messages.success(self.request, "✅ BSS admission submitted successfully.")
#         return redirect(self.success_url)

#     def form_invalid(self, form):
#         print("Form invalid:", form.errors)
#         return super().form_invalid(form)


# # BSC
# @method_decorator(role_required(['master_admin', 'admin', 'sub_admin', 'teacher', 'student']), name='dispatch')
# class AdmissionBscCreateView(FormView):
#     template_name = "admissions_others/admission_form_honours.html"
#     form_class = DegreeAdmissionForm
#     success_url = reverse_lazy("bsc_admission_create")

#     def get_form_kwargs(self):
#         kw = super().get_form_kwargs()
#         kw["request"] = self.request
#         return kw

#     def get_initial(self):
#         return {"add_admission_group": "Bsc"}

#     def get_context_data(self, **kwargs):
#         ctx = super().get_context_data(**kwargs)
#         ctx = TemplateLayout.init(self, ctx)
#         ctx["layout"] = "vertical"
#         ctx["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", ctx)
#         ctx["subjects_all"] = DegreeSubjects.objects.filter(group="Bsc", sub_status="active")
#         return ctx

#     def form_valid(self, form):
#         try:
#             prog = DegreePrograms.objects.get(deg_name__iexact="Bsc")
#             form.instance.add_program = prog
#             form.instance.add_admission_group = "Bsc"
#         except DegreePrograms.DoesNotExist:
#             form.add_error(None, "BSc program not found.")
#             return self.form_invalid(form)

#         session_id = self.request.POST.get("add_session")
#         try:
#             degree_program = Programs.objects.get(pro_name__iexact="degree")
#             fee = Fee.objects.get(fee_session_id=session_id, fee_program=degree_program, fee_group__group_name__iexact="Bsc")
#             form.instance.add_amount = fee.amount
#         except Exception:
#             form.instance.add_amount = 0

#         u = self.request.user
#         form.instance.created_by = u if getattr(u, "is_authenticated", False) else None
#         form.instance.submitted_via = 'student_self' if getattr(u, 'role', None) == 'student' else 'staff'

#         form.instance.main_subject_id = self.request.POST.get("main_subject") or None

#         self.object = form.save()

#         selected_subjects = self.request.POST.getlist("subjects")
#         if selected_subjects:
#             self.object.subjects.set(selected_subjects)

#         messages.success(self.request, "✅ BSc admission submitted successfully.")
#         return redirect(self.success_url)

#     def form_invalid(self, form):
#         print("⛔ Form INVALID", form.errors)
#         return super().form_invalid(form)


# # BBS
# @method_decorator(role_required(['master_admin', 'admin', 'sub_admin', 'teacher', 'student']), name='dispatch')
# class AdmissionBbsCreateView(FormView):
#     template_name = "admissions_others/admission_form_honours.html"
#     form_class = DegreeAdmissionForm
#     success_url = reverse_lazy("bbs_admission_create")

#     def get_form_kwargs(self):
#         kw = super().get_form_kwargs()
#         kw["request"] = self.request
#         return kw

#     def get_initial(self):
#         return {"add_admission_group": "Bbs"}

#     def get_context_data(self, **kwargs):
#         ctx = super().get_context_data(**kwargs)
#         ctx = TemplateLayout.init(self, ctx)
#         ctx["layout"] = "vertical"
#         ctx["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", ctx)
#         ctx["subjects_all"] = DegreeSubjects.objects.filter(group="Bbs", sub_status="active")
#         return ctx

#     def form_valid(self, form):
#         try:
#             prog = DegreePrograms.objects.get(deg_name__iexact="Bbs")
#             form.instance.add_program = prog
#             form.instance.add_admission_group = "Bbs"
#         except DegreePrograms.DoesNotExist:
#             form.add_error(None, "BBS program not found.")
#             return self.form_invalid(form)

#         session_id = self.request.POST.get("add_session")
#         try:
#             degree_program = Programs.objects.get(pro_name__iexact="degree")
#             fee = Fee.objects.get(fee_session_id=session_id, fee_program=degree_program, fee_group__group_name__iexact="Bbs")
#             form.instance.add_amount = fee.amount
#         except Exception:
#             form.instance.add_amount = 0

#         u = self.request.user
#         form.instance.created_by = u if getattr(u, "is_authenticated", False) else None
#         form.instance.submitted_via = 'student_self' if getattr(u, 'role', None) == 'student' else 'staff'

#         form.instance.main_subject_id = self.request.POST.get("main_subject") or None

#         self.object = form.save()

#         selected_subjects = self.request.POST.getlist("subjects")
#         if selected_subjects:
#             self.object.subjects.set(selected_subjects)

#         messages.success(self.request, "✅ BBS admission submitted successfully.")
#         return redirect(self.success_url)

#     def form_invalid(self, form):
#         print("⛔ Form INVALID", form.errors)
#         return super().form_invalid(form)






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
@role_required(['master_admin'])
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


@method_decorator(role_required(['master_admin']), name='dispatch')
class FeeDeleteView(DeleteView):
    model = Fee
    success_url = reverse_lazy('fee_list')
    template_name = None

    def post(self, request, *args, **kwargs):
        messages.success(request, "Fee deleted successfully.")
        return super().post(request, *args, **kwargs)









# subject wise studnt data
import csv
from django.http import HttpResponse
from django.views.generic import TemplateView
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Count, Case, When, Value, IntegerField
from django.utils.decorators import method_decorator

from apps.accounts.utils import role_required

from .forms import SubjectFilterForm
from .models import HscAdmissions, Subjects, Session


def _mobile_text(m):
    """Keep leading 0 in CSV for Excel (treat as text)."""
    if not m:
        return ''
    return f'="{str(m).strip()}"'


@method_decorator(role_required(['master_admin', 'admin', 'sub_admin', 'teacher']), name='dispatch')
class SubjectWiseStudentsView(TemplateView):
    template_name = "subjects/subject_students.html"
    paginate_by = 50  # Show 50 students per page

    def _apply_session_filter(self, qs):
        """Apply active session filter if present; return (qs, active_session_name)."""
        active_session_name = None
        active_session_id = self.request.session.get('active_session_id')
        if active_session_id:
            try:
                active_session = Session.objects.get(id=active_session_id)
                qs = qs.filter(add_session=active_session)
                active_session_name = active_session.ses_name
            except Session.DoesNotExist:
                pass
        return qs, active_session_name

    def _subject_qs(self, subject):
        """
        Build the base queryset for a given subject.
        If subject.sub_select contains 'all', it applies to everyone (e.g., Bangla/English/ICT).
        Otherwise, match against all subject fields and the M2M.
        """
        if 'all' in (subject.sub_select or []):
            qs = HscAdmissions.objects.all()
        else:
            qs = HscAdmissions.objects.filter(
                Q(subjects=subject) |
                Q(main_subject=subject) |
                Q(fourth_subject=subject) |
                Q(optional_subject=subject) |
                Q(optional_subject_2=subject)
            )
        return qs

    def _order_students(self, qs):
        """
        Order by roll (NULL last), then group, then name.
        Works whether roll is nullable or not (keeps your current approach).
        """
        return qs.order_by(
            Case(
                When(add_class_roll__isnull=True, then=Value(999999)),
                default="add_class_roll",
                output_field=IntegerField()
            ),
            "add_admission_group",
            "add_name"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Vuexy layout context
        context = TemplateLayout.init(self, context)
        context["layout"] = "vertical"
        context["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", context)

        form = SubjectFilterForm(self.request.GET or None)
        students = HscAdmissions.objects.none()
        selected_subject = None
        total_count = 0
        group_counts = {}
        active_session_name = None

        if form.is_valid():
            subject = form.cleaned_data.get("subject")
            if subject:
                selected_subject = subject

                # Build base queryset (handles 'all' subjects like Bangla/English/ICT)
                qs = self._subject_qs(subject)

                # Apply session filter (if active session set)
                qs, active_session_name = self._apply_session_filter(qs)

                # Avoid duplicates and select relevant fields
                qs = qs.select_related("add_session").only(
                    "id", "add_name", "add_class_roll", "add_admission_group",
                    "add_session", "add_class_id", "add_mobile"
                ).distinct()

                # Order & paginate
                students = self._order_students(qs)
                group_counts = students.values('add_admission_group').annotate(count=Count('id')).order_by()

                total_count = students.count()
                paginator = Paginator(students, self.paginate_by)
                page_number = self.request.GET.get('page')
                try:
                    students_page = paginator.page(page_number)
                except PageNotAnInteger:
                    students_page = paginator.page(1)
                except EmptyPage:
                    students_page = paginator.page(paginator.num_pages)

                context.update({
                    "students": students_page,
                    "all_students": students,  # full qs for CSV
                    "paginator": paginator,
                    "page_obj": students_page,
                    "group_counts": group_counts,
                    "active_session_name": active_session_name,
                })

        # All active subjects + enrolled students (for the grid)
        all_subjects = Subjects.objects.filter(sub_status="active").order_by("group", "sub_name")
        subject_students = []
        for subject in all_subjects:
            qs = self._subject_qs(subject)
            qs, _ = self._apply_session_filter(qs)
            qs = qs.select_related("add_session").only(
                "add_name", "add_class_roll", "add_session", "add_mobile"
            ).distinct()
            qs = self._order_students(qs)
            subject_students.append({
                "subject": subject,
                "students": qs
            })

        context.update({
            "form": form,
            "selected_subject": selected_subject,
            "total_count": total_count,
            "all_subjects_students": subject_students,
        })
        return context

    def get(self, request, *args, **kwargs):
        # CSV export
        if request.GET.get('download_csv'):
            context = self.get_context_data(**kwargs)
            selected_subject = context.get('selected_subject')
            students = context.get('all_students')  # full ordered queryset

            response = HttpResponse(content_type='text/csv')
            filename = f"subject_{selected_subject.sub_name if selected_subject else 'students'}_students.csv"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'

            writer = csv.writer(response)
            if selected_subject:
                admitted_count = students.count() if students else 0
                seat_limit = selected_subject.limit or 0

                writer.writerow(['Subject', selected_subject.sub_name or ''])
                writer.writerow(['Code', selected_subject.code or ''])
                writer.writerow(['Group', selected_subject.get_group_display() or 'All'])
                writer.writerow(['Student Admitted', admitted_count])
                writer.writerow(['Seat Limit', seat_limit])
                writer.writerow([])

            # ==== HEADER ====
            writer.writerow(['Roll', 'Student', 'Mobile', '', '', '', ''])

            # ==== DATA ROWS ====
            if students and students.exists():
                for student in students:
                    writer.writerow([
                        student.add_class_roll or '',
                        student.add_name or '',
                        _mobile_text(student.add_mobile),  # keep leading 0
                        '', '', '', ''  # 4 blank cols
                    ])
            else:
                writer.writerow(['No students found for this subject and session.', '', '', '', '', '', ''])

            return response

        return super().get(request, *args, **kwargs)






from django.views.generic import TemplateView
from django.db.models import Q, Case, When, Value, IntegerField, Count

from apps.admissions.models import HscAdmissions, Subjects, Session

@method_decorator(role_required(['master_admin', 'admin', 'sub_admin', 'teacher']), name='dispatch')
class SubjectStudentsPDFView(TemplateView):
    """
    Client-side PDF view: renders a standalone A4 page (or multiple)
    and uses html2canvas + jsPDF to download.
    """
    template_name = "subjects/subject_students_pdf.html"

    def _apply_session_filter(self, qs):
        active_session_name = None
        active_session_id = self.request.session.get('active_session_id')
        if active_session_id:
            try:
                active_session = Session.objects.get(id=active_session_id)
                qs = qs.filter(add_session=active_session)
                active_session_name = active_session.ses_name
            except Session.DoesNotExist:
                pass
        return qs, active_session_name

    def _subject_qs(self, subject):
        # if this subject is for everyone (Bangla/English/ICT)
        if 'all' in (subject.sub_select or []):
            return HscAdmissions.objects.all()
        return HscAdmissions.objects.filter(
            Q(subjects=subject) |
            Q(main_subject=subject) |
            Q(fourth_subject=subject) |
            Q(optional_subject=subject) |
            Q(optional_subject_2=subject)
        )

    def _order_students(self, qs):
        return qs.order_by(
            Case(
                When(add_class_roll__isnull=True, then=Value(999999)),
                default="add_class_roll",
                output_field=IntegerField()
            ),
            "add_admission_group",
            "add_name"
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # This template is standalone (no Vuexy chrome), but we keep layout vars just in case
        ctx = TemplateLayout.init(self, ctx)
        ctx["layout"] = "vertical"
        ctx["layout_path"] = TemplateHelper.set_layout("layout_blank.html", ctx)

        # Resolve subject from query param
        subject_obj = None
        subject_id = self.request.GET.get("subject")
        if subject_id:
            subject_obj = Subjects.objects.filter(pk=subject_id).first()

        students = HscAdmissions.objects.none()
        active_session_name = None
        total_count = 0

        if subject_obj:
            qs = self._subject_qs(subject_obj)
            qs, active_session_name = self._apply_session_filter(qs)
            qs = qs.select_related("add_session").only(
                "add_name", "add_mobile", "add_class_roll",
                "add_admission_group", "add_class_id", "add_session"
            ).distinct()
            students = self._order_students(qs)
            total_count = students.count()

        ctx.update({
            "selected_subject": subject_obj,
            "students": students,            # full list (no pagination)
            "total_count": total_count,
            "active_session_name": active_session_name,
            # Optional header meta; override via context processor if you have
            "institute_name": "নবাবগঞ্জ সিটি কলেজ",
            "eiin": "124596",
            "phone": "01309124596",
        })
        return ctx








# demo tabulation PDF (static design)
from datetime import datetime



@method_decorator(role_required(['master_admin', 'admin', 'sub_admin', 'teacher']), name='dispatch')
class TabulationSheetPDFView(TemplateView):
    """
    Static tabulation sheet preview (A4 landscape, header repeats each page).
    Renders exams/tabulation_pdf.html; later you can replace static rows with DB data.
    """
    template_name = "exams/tabulation_pdf.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # Vuexy blank layout for clean print/PDF
        ctx = TemplateLayout.init(self, ctx)
        ctx["layout"] = "vertical"
        ctx["layout_path"] = TemplateHelper.set_layout("layout_blank.html", ctx)

        subjects = [
            "Bangla", "English", "ICT", "Physics", "Chemistry",
            "Biology / Higher Math", "Biology/H.Math/Agri/Stats/Psychology",
        ]

        # --- Static 100 students ---
        rows = []
        start_roll = 401
        for i in range(100):
            rows.append({
                "roll": str(start_roll + i),
                "name": f"Student {i+1:03d}",
                "marks": [0 for _ in subjects],  # one mark per subject
                "gpa_wo4": "0.00",
                "gpa": "0.00",
                "grade": "F",
            })

        ctx.update({
            "institute_name": "নবাবগঞ্জ সিটি কলেজ",
            "eiin": "124596",
            "exam_name": "Science Tabulation – HTML (Static)",
            "class_name": "HSC – First Year",
            "group_name": "Science",
            "session_name": "2024–2025",
            "subjects": subjects,
            "rows": rows,
            "ROWS_PER_PAGE": 24,
        })
        ctx["current_year"] = datetime.now().year
        return ctx



# Global session filter
from .forms import SessionSelectForm

def set_session_view(request):
    if request.method == 'POST':
        form = SessionSelectForm(request.POST)
        if form.is_valid():
            request.session['active_session_id'] = form.cleaned_data['session'].id
    return redirect(request.META.get('HTTP_REFERER', '/'))
