from django.views.generic import ListView
from apps.admissions.models import HscAdmissions, Fee
from django.db.models import Q
from django.contrib import messages
from apps.admissions.models import Session, Programs

from apps.accounts.utils import role_required
from django.utils.decorators import method_decorator
from django.db import IntegrityError, transaction

# @method_decorator(role_required(['master_admin', 'admin', 'sub_admin', 'teacher']), name='dispatch')

from web_project import TemplateLayout, TemplateHelper

GROUP_CHOICES_MAP = {
    'science': 'Science',
    'arts': 'Humanities',
    'commerce': 'Business Studies',
    # 'Ba': 'BA',
    # 'Bss': 'BSS',
    # 'Bbs': 'BBS',
    # 'Bsc': 'BSC',
}


from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from django.http import HttpResponse
from apps.accounts.utils import role_required
from apps.admissions.models import HscAdmissions, Programs, Session

import csv
import re

# @method_decorator(role_required(['master_admin', 'admin', 'sub_admin', 'teacher']), name='dispatch')
# class AdmittedStudentListView(ListView):
#     model = HscAdmissions
#     template_name = 'students/admitted_students_list.html'
#     context_object_name = 'students'
#     paginate_by = 25

#     # ---------- CSV trigger ----------
#     def render_to_response(self, context, **response_kwargs):
#         if self.request.GET.get('export') == 'csv':
#             qs = self._get_base_queryset(exporting=True)
#             return self._export_csv_full(qs)
#         return super().render_to_response(context, **response_kwargs)

#     # ---------- Helpers ----------
#     def _normalize_mobile_digits(self, val: str) -> str:
#         if not val:
#             return ''
#         digits = re.sub(r'\D+', '', val)
#         if digits.startswith('880'):
#             digits = '0' + digits[3:]
#         return digits

#     def _fmt_excel_mobile(self, val: str) -> str:
#         """Excel-safe: keep leading zero & show as text."""
#         d = self._normalize_mobile_digits(val)
#         return f'="{d}"' if d else ''

#     def _get_compulsory_subjects(self):
#         """
#         Compulsory list: Bangla, English, ICT always first (hard-coded, guaranteed).
#         Then any extra subjects that have sub_select containing 'all' (if present in DB).
#         """
#         priority = ['Bangla', 'English', 'ICT']  # hard requirement
#         # try to fetch additional 'all' subjects (if any), but not required
#         extra = list(
#             Subjects.objects
#             .filter(sub_select__contains='all')
#             .values_list('sub_name', flat=True)
#         )
#         seen = {p.lower() for p in priority}
#         extras_ordered = []
#         for name in sorted({(n or '').strip() for n in extra if n}):
#             if name.lower() not in seen:
#                 extras_ordered.append(name)
#                 seen.add(name.lower())
#         return priority + extras_ordered

#     # ---------- CSV (full requirement + fixes) ----------
#     def _export_csv_full(self, queryset):
#         """
#         Columns:
#         Roll, Name, SSC Result, Mobile,
#         Father Name, Father Mobile, Mother Name, Mother Mobile,
#         Address, Subjects

#         Subjects rule:
#         - Always start with: Bangla; English; ICT
#         - Then the rest (main/fourth/optional/optional2 + M2M), deduped & A..Z
#         """
#         resp = HttpResponse(content_type='text/csv; charset=utf-8')
#         resp['Content-Disposition'] = 'attachment; filename="admitted_students_full.csv"'
#         writer = csv.writer(resp)

#         writer.writerow([
#             'Roll', 'Name', 'SSC Result', 'Mobile',
#             'Father Name', 'Father Mobile',
#             'Mother Name', 'Mother Mobile',
#             'Address', 'Subjects'
#         ])

#         compulsory = self._get_compulsory_subjects()
#         compulsory_lower = [c.lower() for c in compulsory]

#         for s in queryset:
#             # SSC: "GPA (Year)"
#             ssc_result = f"{s.add_ssc_gpa or ''} ({s.add_ssc_passyear or ''})".strip()

#             # Address
#             parts = [s.add_village or '', s.add_post or '', s.add_police or '', s.add_distric or '']
#             address = ', '.join([p for p in parts if p]).strip(', ')

#             # Gather subjects from all sources
#             pool = set()

#             if s.main_subject and getattr(s.main_subject, 'sub_name', None):
#                 pool.add(s.main_subject.sub_name.strip())
#             if s.fourth_subject and getattr(s.fourth_subject, 'sub_name', None):
#                 pool.add(s.fourth_subject.sub_name.strip())
#             if s.optional_subject and getattr(s.optional_subject, 'sub_name', None):
#                 pool.add(s.optional_subject.sub_name.strip())
#             if s.optional_subject_2 and getattr(s.optional_subject_2, 'sub_name', None):
#                 pool.add(s.optional_subject_2.sub_name.strip())

#             m2m = getattr(s, '_prefetched_subjects', None) or s.subjects.all()
#             for sub in m2m:
#                 if getattr(sub, 'sub_name', None):
#                     pool.add(sub.sub_name.strip())

#             # Order: compulsory first (always included), then the rest A..Z
#             pool_lower_map = {name.lower(): name for name in pool if name}
#             first = []
#             for c in compulsory_lower:
#                 # if DB has a differently-cased version of the same name, use that
#                 first.append(pool_lower_map.get(c, c.title()))  # keep nice casing

#             rest = sorted([v for k, v in pool_lower_map.items() if k not in compulsory_lower])
#             subjects_str = '; '.join(first + rest)

#             writer.writerow([
#                 s.add_class_roll or '',
#                 s.add_name or '',
#                 ssc_result,
#                 self._fmt_excel_mobile(s.add_mobile),
#                 s.add_father or '',
#                 self._fmt_excel_mobile(s.add_father_mobile),
#                 s.add_mother or '',
#                 self._fmt_excel_mobile(s.add_mother_mobile),
#                 address,
#                 subjects_str,
#             ])

#         return resp

#     # ---------- Queryset ----------
#     def _get_base_queryset(self, exporting=False):
#         qs = HscAdmissions.objects.select_related('add_session', 'add_program', 'created_by')

#         # Filters
#         session = self.request.GET.get('session') or self.request.session.get('active_session_id')
#         program = self.request.GET.get('program')
#         group = self.request.GET.get('group')

#         if session:
#             qs = qs.filter(add_session_id=session)
#         if program:
#             qs = qs.filter(add_program_id=program)
#         if group:
#             qs = qs.filter(add_admission_group=group)

#         # Search (normalize +880/880 -> 0)
#         search = self.request.GET.get('search')
#         if search:
#             norm = self._normalize_mobile_digits(search)
#             try:
#                 search_id = int(search)
#                 qs = qs.filter(
#                     Q(created_by_id=search_id) |
#                     Q(add_name__icontains=search) |
#                     Q(add_father__icontains=search) |
#                     Q(add_mobile__icontains=norm) |
#                     Q(add_class_roll__icontains=search)
#                 )
#             except ValueError:
#                 qs = qs.filter(
#                     Q(add_name__icontains=search) |
#                     Q(add_father__icontains=search) |
#                     Q(add_mobile__icontains=norm) |
#                     Q(add_class_roll__icontains=search)
#                 )

#         # Order
#         order = self.request.GET.get('order')
#         qs = qs.order_by('-add_class_roll' if order == 'desc' else 'add_class_roll')

#         # Optimize for export
#         if exporting:
#             qs = qs.select_related(
#                 'main_subject', 'fourth_subject', 'optional_subject', 'optional_subject_2'
#             ).prefetch_related('subjects')
#             # micro-cache M2M
#             for obj in qs:
#                 obj._prefetched_subjects = list(obj.subjects.all())

#         return qs

#     # ---------- ListView hooks ----------
#     def get_queryset(self):
#         return self._get_base_queryset(exporting=False)

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)

#         # Vuexy layout
#         context = TemplateLayout.init(self, context)
#         context["layout"] = "vertical"
#         context["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", context)

#         context['sessions'] = Session.objects.all()
#         context['programs'] = Programs.objects.all()
#         context['groups'] = GROUP_CHOICES_MAP.items()

#         for s in context['students']:
#             s.payment_form = HscPaymentReviewForm(instance=s)

#         return context






from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from django.http import HttpResponse
from apps.accounts.utils import role_required
from apps.admissions.models import HscAdmissions, Programs, Session, Subjects

import csv
import re
from datetime import date, datetime


@method_decorator(role_required(['master_admin', 'admin', 'sub_admin', 'teacher']), name='dispatch')
class AdmittedStudentListView(ListView):
    model = HscAdmissions
    template_name = 'students/admitted_students_list.html'
    context_object_name = 'students'
    paginate_by = 25

    # ========================
    # Trigger: ?export=csv
    # ========================
    def render_to_response(self, context, **response_kwargs):
        if self.request.GET.get('export') == 'csv':
            qs = self._get_base_queryset(exporting=True)
            return self._export_csv_full(qs)
        return super().render_to_response(context, **response_kwargs)

    # ========================
    # Helpers
    # ========================
    def _normalize_mobile_digits(self, val: str) -> str:
        if not val:
            return ''
        digits = re.sub(r'\D+', '', val)
        if digits.startswith('880'):
            digits = '0' + digits[3:]
        return digits

    def _fmt_excel_mobile(self, val: str) -> str:
        d = self._normalize_mobile_digits(val)
        return f'="{d}"' if d else ''

    def _fmt_date(self, d):
        if isinstance(d, (date, datetime)):
            return d.strftime('%Y-%m-%d')
        return d or ''

    def _get_compulsory_subjects(self):
        """
        Always return compulsory list with this order:
        1) Bangla, English, ICT  (fixed priority)
        2) Then any other Subjects where sub_select contains 'all' (case-insensitive),
        deduped (case-insensitive), trimmed, and sorted A→Z.
        """
        priority = ["Bangla", "English", "ICT"]

        # pull names where 'all' is present in sub_select
        extra_qs = Subjects.objects.filter(sub_select__icontains="all").values_list("sub_name", flat=True)

        # normalize, dedupe (case-insensitive), and skip priority ones
        seen_lower = {p.lower() for p in priority}
        extras_set = set()

        for n in extra_qs:
            if not n:
                continue
            clean = n.strip()
            if not clean:
                continue
            low = clean.lower()
            if low in seen_lower:
                # skip Bangla/English/ICT even if they exist in DB with 'all'
                continue
            extras_set.add(clean)

        # stable A→Z sort for the rest
        extras_sorted = sorted(extras_set, key=lambda s: s.lower())

        return priority + extras_sorted

    # ========================
    # CSV (full + new fields)
    # ========================
    def _export_csv_full(self, queryset):
        """
        CSV export:
        - All Subjects (M2M) is ALWAYS 'Bangla; English; ICT'
        - Group-A static by stream (science/commerce), arts keeps optional_subject
        - Flat header order kept
        """
        from django.http import HttpResponse
        import csv

        resp = HttpResponse(content_type='text/csv')
        resp['Content-Disposition'] = 'attachment; filename="admitted_students_full.csv"'
        writer = csv.writer(resp)

        writer.writerow([
            # Applicant
            "Student Name", "Class Roll", "Mobile", "Class ID",
            "Birth Certificate/NID", "Date of Birth",
            "Marital Status", "Age", "Gender", "Religion",
            "Blood Group", "Nationality",

            # Parent/Guardian
            "Father Name", "Father Mobile", "Father NID", "Father DOB",
            "Mother Name", "Mother Mobile", "Mother NID", "Mother DOB",
            "Guardian Name", "Guardian Mobile", "Guardian Occupation", "Guardian Monthly Income",

            # Present Address
            "Present Village", "Present Post", "Present Police", "Present District", "Present Postal",

            # Permanent Address
            "Permanent Village", "Permanent Post", "Permanent Police", "Permanent District", "Permanent Postal",

            # Quota/Community
            "Special Quota", "Quota Name", "Community", "Community Name",

            # Academic (SSC)
            "SSC Board", "SSC Year", "SSC Roll", "SSC Registration",
            "SSC Session", "SSC Group", "SSC Institute", "SSC GPA",

            # Subjects (fixed order)
            "Common Subjects",
            "Elective/Optional Subjects (Group: A)",
            "Elective/Optional Subjects (Group: B)",
            "Elective/Optional Subjects (Group: C)/ Main Subject",
            "Additional/4th Subjects",

            # Payment
            "Payment Method", "Payment From", "TrxID", "Amount", "Payment Status", "Payment Note"
        ])

        def fmt_date(d):
            return d.strftime("%d-%m-%Y") if d else ''

        for s in queryset:
            # ----- All Subjects (M2M): fixed for everyone -----
            all_subjects_m2m = "Bangla; English; ICT"

            # ----- Group A by stream -----
            if s.add_admission_group == 'science':
                group_a = "Physics; Chemistry"
            elif s.add_admission_group == 'commerce':
                group_a = "Accounting; Business Organization and Management; Production Management and Marketing"
            else:  # arts
                group_a = s.optional_subject.sub_name if s.optional_subject else ''

            # Other subject slots
            group_b     = s.optional_subject_2.sub_name if s.optional_subject_2 else ''
            group_c_main= s.main_subject.sub_name       if s.main_subject       else ''
            fourth_sub  = s.fourth_subject.sub_name     if s.fourth_subject     else ''

            writer.writerow([
                # Applicant
                s.add_name or '',
                s.add_class_roll or '',
                self._fmt_excel_mobile(s.add_mobile),
                s.add_class_id or '',
                s.add_birth_certificate_no or '',
                fmt_date(s.add_birthdate),
                s.add_marital_status or '',
                s.add_age or '',
                s.add_gender or '',
                s.add_religion or '',
                s.add_blood_group or '',
                s.add_nationality or '',

                # Parent/Guardian
                s.add_father or '',
                self._fmt_excel_mobile(s.add_father_mobile),
                s.add_father_nid or '',
                fmt_date(s.add_father_birthdate),
                s.add_mother or '',
                self._fmt_excel_mobile(s.add_mother_mobile),
                s.add_mother_nid or '',
                fmt_date(s.add_mother_birthdate),
                s.add_parent or '',
                self._fmt_excel_mobile(s.add_parent_mobile),
                s.add_parent_service or '',
                s.add_parent_income or '',

                # Present Address
                s.add_village or '',
                s.add_post or '',
                s.add_police or '',
                s.add_distric or '',
                s.add_postal or '',

                # Permanent Address
                s.add_village_per or '',
                s.add_post_per or '',
                s.add_police_per or '',
                s.add_distric_per or '',
                s.add_postal_per or '',

                # Quota/Community
                "Yes" if s.qouta else "No",
                s.qouta_name or '',
                "Yes" if s.community else "No",
                s.community_name or '',

                # SSC
                s.add_ssc_board or '',
                s.add_ssc_passyear or '',
                s.add_ssc_roll or '',
                s.add_ssc_reg or '',
                s.add_ssc_session or '',
                s.get_add_ssc_group_display() or '',
                s.add_ssc_institute or '',
                s.add_ssc_gpa or '',

                # Subjects
                all_subjects_m2m,
                group_a,
                group_b,
                group_c_main,
                fourth_sub,

                # Payment
                s.get_add_payment_method_display() or '',
                s.add_slip or '',
                s.add_trxid or '',
                s.add_amount or '',
                s.add_payment_status or '',
                s.add_payment_note or '',
            ])

        return resp
    # ========================
    # Queryset (list & export)
    # ========================
    def _get_base_queryset(self, exporting=False):
        qs = HscAdmissions.objects.select_related('add_session', 'add_program', 'created_by')

        # Filters
        session = self.request.GET.get('session') or self.request.session.get('active_session_id')
        program = self.request.GET.get('program')
        group = self.request.GET.get('group')
        if session: qs = qs.filter(add_session_id=session)
        if program: qs = qs.filter(add_program_id=program)
        if group:   qs = qs.filter(add_admission_group=group)

        # Search
        search = self.request.GET.get('search')
        if search:
            norm = self._normalize_mobile_digits(search)
            try:
                search_id = int(search)
                qs = qs.filter(
                    Q(created_by_id=search_id) |
                    Q(add_name__icontains=search) |
                    Q(add_father__icontains=search) |
                    Q(add_mobile__icontains=norm) |
                    Q(add_class_roll__icontains=search)
                )
            except ValueError:
                qs = qs.filter(
                    Q(add_name__icontains=search) |
                    Q(add_father__icontains=search) |
                    Q(add_mobile__icontains=norm) |
                    Q(add_class_roll__icontains=search)
                )

        # Order
        order = self.request.GET.get('order')
        qs = qs.order_by('-add_class_roll' if order == 'desc' else 'add_class_roll')

        # Optimize when exporting
        if exporting:
            qs = qs.select_related(
                'main_subject', 'fourth_subject', 'optional_subject', 'optional_subject_2'
            ).prefetch_related('subjects')
            for obj in qs:
                obj._prefetched_subjects = list(obj.subjects.all())

        return qs

    # ========================
    # List hooks
    # ========================
    def get_queryset(self):
        return self._get_base_queryset(exporting=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Vuexy layout context (unchanged)
        context = TemplateLayout.init(self, context)
        context["layout"] = "vertical"
        context["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", context)

        context['sessions'] = Session.objects.all()
        context['programs'] = Programs.objects.all()
        context['groups'] = GROUP_CHOICES_MAP.items()

        for s in context['students']:
            s.payment_form = HscPaymentReviewForm(instance=s)

        return context





# Update Modal
from apps.admissions.forms import HscPaymentReviewForm
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, redirect

@require_POST
@role_required(['master_admin', 'admin', 'sub_admin', 'teacher'])
def update_admission_payment(request, pk):
    obj = get_object_or_404(HscAdmissions, pk=pk)
    form = HscPaymentReviewForm(request.POST, instance=obj)
    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER") or "/"

    if not form.is_valid():
        messages.error(request, "❌ Payment update failed. Please check the form.")
        return redirect(next_url)

    # Update only editable fields
    partial = form.save(commit=False)
    try:
        # Update only the fields that are editable in the form
        obj.add_payment_status = partial.add_payment_status
        obj.add_payment_note = partial.add_payment_note

        # Save only the editable fields
        obj.save(update_fields=[
            "add_payment_status",
            "add_payment_note",
            "updated_at",
        ])

        messages.success(request, f"✅ Payment updated for {obj.add_name or obj.id}.")
    except IntegrityError:
        messages.error(request, "❌ Payment update failed due to a database error.")
    return redirect(next_url)

from django.views.generic import UpdateView
from apps.admissions.forms import HscPaymentReviewForm


@method_decorator(role_required(['master_admin', 'admin', 'sub_admin', 'teacher']), name='dispatch')
class HscPaymentReviewUpdateView(UpdateView):
    model = HscAdmissions
    form_class = HscPaymentReviewForm
    template_name = "students/payment_review_form.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx = TemplateLayout.init(self, ctx)
        ctx["layout"] = "vertical"
        ctx["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", ctx)
        ctx["page_title"] = "Payment Review / Confirm"
        ctx["student"] = self.object
        return ctx

    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, "✅ Payment information updated.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "❌ Failed to update payment info.")
        return super().form_invalid(form)

    def get_success_url(self):
        nxt = self.request.GET.get("next")
        if nxt:
            return nxt
        return reverse("admitted_students_list")




from django.views.generic.detail import DetailView

@method_decorator(role_required(['master_admin', 'admin', 'sub_admin', 'teacher', 'student']), name='dispatch')
class HscAdmissionDetailView2(DetailView):
    model = HscAdmissions
    template_name = "students/admitted_student_details2.html"  # create this template
    context_object_name = "student"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Optional Vuexy layout integration
        context = TemplateLayout.init(self, context)
        context["layout"] = "vertical"
        context["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", context)

        return context

@method_decorator(role_required(['master_admin', 'admin', 'sub_admin', 'teacher', 'student']), name='dispatch')
class HscAdmissionDetailView(DetailView):
    model = HscAdmissions
    template_name = "students/admitted_student_details.html"  # create this template
    context_object_name = "student"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Optional Vuexy layout integration
        context = TemplateLayout.init(self, context)
        context["layout"] = "vertical"
        context["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", context)

        return context



# Edit and Delete
from django.views.generic.edit import UpdateView, DeleteView
from django.urls import reverse_lazy
from apps.admissions.forms import HscAdmissionForm
from apps.admissions.models import Subjects

# ---------------------------------------------------------------------
# HSC Science Admission: Update view
# ---------------------------------------------------------------------


@method_decorator(
    role_required(['master_admin', 'admin', 'sub_admin', 'teacher']),
    name='dispatch'
)
class HscAdmissionUpdateView(UpdateView):
    model = HscAdmissions
    template_name = "admissions/admission_form.html"
    form_class = HscAdmissionForm
    context_object_name = "student"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # layout ও user
        context["user"] = self.request.user
        context = TemplateLayout.init(self, context)
        context["layout"] = "vertical"
        context["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", context)

        student = self.object
        group = student.add_admission_group or "science"

        # বিজ্ঞান গ্রুপে সাবজেক্ট তালিকা
        context["subjects_all"]      = Subjects.objects.filter(sub_status="active", sub_select__contains="all")
        context["subjects_optional"] = Subjects.objects.filter(group=group, sub_status="active", sub_select__contains="optional")
        context["subjects_main"]     = Subjects.objects.filter(group=group, sub_status="active", sub_select__contains="main")
        context["subjects_fourth"]   = Subjects.objects.filter(group=group, sub_status="active", sub_select__contains="fourth")
        return context

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # If editing an existing instance and photo exists, make add_photo optional
        if self.object and self.object.add_photo:
            form.fields['add_photo'].required = False
        return form

    def form_valid(self, form):
        try:
            with transaction.atomic():
                # Preserve existing photo if no new file is uploaded
                if not form.cleaned_data['add_photo']:
                    form.cleaned_data['add_photo'] = self.object.add_photo
                response = super().form_valid(form)

                # Ensure unique roll per group
                group = self.object.add_admission_group or "science"
                if HscAdmissions.objects.filter(add_admission_group=group, add_class_roll=form.instance.add_class_roll).exclude(id=self.object.id).exists():
                    form.add_error('add_class_roll', "এই গ্রুপে এই রোল নম্বর ইতিমধ্যেই আছে।")
                    return self.form_invalid(form)

                # গ্রুপ অনুযায়ী all + optional সাবজেক্ট সেট করা, ইত্যাদি
                group = self.object.add_admission_group or "science"
                subjects_all = Subjects.objects.filter(
                    sub_status="active"
                ).filter(
                    Q(sub_select__contains='all') |
                    (Q(group=group) & Q(sub_select__contains='optional'))
                )
                self.object.subjects.set(subjects_all)

        except IntegrityError:
            # একই রোল থাকলে এই অংশে আসবে
            form.add_error('add_class_roll', "এই গ্রুপে এই রোল নম্বর ইতিমধ্যেই আছে।")
            return self.form_invalid(form)

        messages.success(
            self.request,
            f"✅ {self.object.add_name}'s data updated successfully."
        )
        return response

    def get_success_url(self):
        return reverse_lazy("admitted_students_list")



# ---------------------------------------------------------------------
# HSC Commerce Admission: Update view
# ---------------------------------------------------------------------


@method_decorator(
    role_required(['master_admin', 'admin', 'sub_admin', 'teacher']),
    name='dispatch'
)
class HscAdmissionUpdateCommerceView(UpdateView):
    model = HscAdmissions
    template_name = "admissions/admission_form_commerce.html"
    form_class = HscAdmissionForm
    context_object_name = "student"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Make photo optional if it already exists
        if self.object and self.object.add_photo:
            form.fields["add_photo"].required = False
        # Commerce-specific: main_subject not required, fourth_subject handled separately
        if "main_subject" in form.fields:
            form.fields["main_subject"].required = False
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user"] = self.request.user
        context = TemplateLayout.init(self, context)
        context["layout"] = "vertical"
        context["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", context)

        student = self.object
        group = student.add_admission_group if student.add_admission_group else "commerce"

        context["subjects_all"] = Subjects.objects.filter(
            sub_status="active", sub_select__contains="all"
        ).order_by("sub_name")
        context["subjects_optional"] = Subjects.objects.filter(
            group=group, sub_status="active", sub_select__contains="optional"
        ).order_by("sub_name")
        context["subjects_main"] = Subjects.objects.filter(
            group=group, sub_status="active", sub_select__contains="main"
        ).order_by("sub_name")
        context["subjects_fourth"] = Subjects.objects.filter(
            group=group, sub_status="active", sub_select__contains="fourth"
        ).order_by("sub_name")
        return context

    def form_valid(self, form):
        # Prepare instance for update
        obj = form.save(commit=False)

        # Preserve existing photo if no new file is uploaded
        if not form.cleaned_data['add_photo'] and self.object.add_photo:
            obj.add_photo = self.object.add_photo

        try:
            with transaction.atomic():
                # Save the form data
                response = super().form_valid(form)

                # Handle fourth_subject if not selected (commerce-specific)
                if not obj.fourth_subject_id:
                    default_fourth = Subjects.objects.filter(
                        group='commerce', sub_status='active', sub_select__contains='fourth'
                    ).first()
                    if default_fourth:
                        obj.fourth_subject = default_fourth
                        obj.save(update_fields=['fourth_subject'])

                # Update ManyToMany subjects
                subjects_all = Subjects.objects.filter(
                    sub_status='active'
                ).filter(
                    Q(sub_select__contains='all') |
                    (Q(group='commerce') & Q(sub_select__contains='optional'))
                )
                obj.subjects.set(subjects_all)

        except IntegrityError as e:
            form.add_error('add_class_roll', "এই গ্রুপে এই রোল নম্বর ইতিমধ্যেই আছে।")
            return self.form_invalid(form)
        except Exception as e:
            form.add_error(None, f"An error occurred while saving: {str(e)}")
            return self.form_invalid(form)

        messages.success(
            self.request,
            f"✅ {obj.add_name}'s data updated successfully."
        )
        return response

    def get_success_url(self):
        return reverse_lazy("admitted_students_list")



# Arts Update View
from apps.admissions.forms import ArtsAdmissionForm

from django.db.models import Q, Count
from django.views.generic import UpdateView
from django.db import transaction
from django.core.exceptions import ValidationError

from collections import Counter
from django.db.models import F

class HscAdmissionUpdateArtsView(UpdateView):
    model = HscAdmissions
    form_class = ArtsAdmissionForm
    template_name = "admissions/admission_form_arts.html"
    context_object_name = "student"
    success_url = reverse_lazy("admitted_students_list")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.object and self.object.add_photo:
            form.fields["add_photo"].required = False
        for field in ["main_subject", "fourth_subject", "optional_subject", "optional_subject_2"]:
            if field in form.fields:
                form.fields[field].required = False
        return form

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        kwargs["user"] = self.request.user
        return kwargs

    # Context build: direct used_count থেকে দেখানো
    def _decorate_with_meta(self, qs, current_ids=None):
        out = []
        current_ids = current_ids or set()
        for s in qs:
            used = s.used_count or 0
            limit = s.limit
            full = (limit is not None) and (used >= limit) and (s.id not in current_ids)
            out.append({
                "id": s.id,
                "sub_name": s.sub_name,
                "code": s.code,
                "limit": limit,
                "used": used,
                "full": full,
                "group": s.group,
                "select": s.sub_select,
            })
        return out

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = TemplateLayout.init(self, context)
        context["layout"] = "vertical"
        context["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", context)

        student = self.object
        group = "arts"
        base = Subjects.objects.filter(sub_status="active", group__iexact=group).order_by("sub_name")
        qs_all = Subjects.objects.filter(sub_status="active", sub_select__icontains="all").order_by("sub_name")
        qs_main = base.filter(sub_select__icontains="main")
        qs_fourth = base.filter(sub_select__icontains="fourth")
        qs_optA = base.filter(sub_select__icontains="optional").exclude(sub_select__icontains="optional2")
        qs_optB = base.filter(sub_select__icontains="optional2")

        current_ids = {
            student.main_subject_id,
            student.fourth_subject_id,
            student.optional_subject_id,
            student.optional_subject_2_id,
        }

        context["subjects_all"] = self._decorate_with_meta(qs_all, current_ids)
        context["subjects_main"] = self._decorate_with_meta(qs_main, current_ids)
        context["subjects_fourth"] = self._decorate_with_meta(qs_fourth, current_ids)
        context["subjects_optional"] = self._decorate_with_meta(qs_optA, current_ids)
        context["subjects_optional2"] = self._decorate_with_meta(qs_optB, current_ids)

        context["group"] = group
        context["status"] = "active"
        return context

    def form_valid(self, form):
        # program + group lock
        try:
            hsc_program = Programs.objects.get(pro_name__iexact="hsc")
            form.instance.add_program = hsc_program
            form.instance.add_admission_group = "arts"
        except Programs.DoesNotExist:
            form.add_error(None, "HSC program not found.")
            return self.form_invalid(form)

        old_ids = {
            self.object.main_subject_id,
            self.object.fourth_subject_id,
            self.object.optional_subject_id,
            self.object.optional_subject_2_id,
        }
        new_ids = {
            form.cleaned_data.get("main_subject").id if form.cleaned_data.get("main_subject") else None,
            form.cleaned_data.get("fourth_subject").id if form.cleaned_data.get("fourth_subject") else None,
            form.cleaned_data.get("optional_subject").id if form.cleaned_data.get("optional_subject") else None,
            form.cleaned_data.get("optional_subject_2").id if form.cleaned_data.get("optional_subject_2") else None,
        }
        remove_ids = {i for i in old_ids if i and i not in new_ids}
        add_ids = {i for i in new_ids if i and i not in old_ids}

        # preserve photo
        if not form.cleaned_data["add_photo"] and self.object.add_photo:
            form.instance.add_photo = self.object.add_photo

        try:
            with transaction.atomic():
                # update used_count safely
                if remove_ids:
                    Subjects.objects.filter(id__in=remove_ids).update(used_count=F("used_count") - 1)
                if add_ids:
                    for sid in add_ids:
                        subj = Subjects.objects.select_for_update().get(id=sid)
                        if subj.limit is not None and subj.used_count >= subj.limit:
                            form.add_error(None, f"'{subj.sub_name}' আসন পূর্ণ।")
                            raise IntegrityError("limit exceeded")
                        subj.used_count = F("used_count") + 1
                        subj.save(update_fields=["used_count"])

                self.object = form.save()

                # attach common subjects
                selected_subject_ids = list(
                    Subjects.objects.filter(sub_status="active", sub_select__icontains="all").values_list("id", flat=True)
                )
                if form.instance.optional_subject_id:
                    selected_subject_ids.append(form.instance.optional_subject_id)
                if form.instance.optional_subject_2_id:
                    selected_subject_ids.append(form.instance.optional_subject_2_id)
                self.object.subjects.set(selected_subject_ids)

                # unique roll check
                if HscAdmissions.objects.filter(
                    add_admission_group="arts",
                    add_class_roll=form.instance.add_class_roll
                ).exclude(id=self.object.id).exists():
                    form.add_error("add_class_roll", "এই গ্রুপে এই রোল নম্বর ইতিমধ্যেই আছে।")
                    raise IntegrityError("duplicate roll")

        except IntegrityError:
            return self.form_invalid(form)
        except Exception as e:
            form.add_error(None, f"An error occurred: {str(e)}")
            return self.form_invalid(form)

        messages.success(self.request, f"✅ {self.object.add_name}'s data updated successfully.")
        return super().form_valid(form)




from django.shortcuts import redirect

# 🗑️ Delete View

@method_decorator(role_required(['master_admin']), name='dispatch')
class HscAdmissionDeleteView(DeleteView):
    model = HscAdmissions
    success_url = reverse_lazy('admitted_students_list')
    context_object_name = "student"

    def dispatch(self, request, *args, **kwargs):
        if request.method == "GET":
            try:
                self.object = self.get_object()
                self.object.delete()
                messages.success(request, "✅ Admission record deleted successfully.")
            except Exception as e:
                messages.error(request, f"❌ Failed to delete admission: {str(e)}")
            return redirect(self.success_url)

        return super().dispatch(request, *args, **kwargs)







# Bulk admission form pdf

from django.shortcuts import render

# def admission_pdf_preview(request):
#     students = HscAdmissions.objects.all()
#     return render(request, "hsc/admission_pdf_bulk.html", {"students": students})

# from apps.admissions.models import HscAdmissions

def admission_pdf_preview(request):
    search = request.GET.get("search")
    session = request.GET.get("session")
    program = request.GET.get("program")
    group = request.GET.get("group")

    students = HscAdmissions.objects.all()

    if search:
        students = students.filter(
            Q(add_name__icontains=search) |
            Q(add_mobile__icontains=search) |
            Q(add_class_roll__icontains=search)
        )
    if session:
        students = students.filter(add_session_id=session)
    if program:
        students = students.filter(add_program_id=program)
    if group:
        students = students.filter(add_admission_group=group)

    return render(request, "hsc/admission_pdf_bulk.html", {"students": students})





# invoice view
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.utils.timezone import localtime
from django.conf import settings

from apps.accounts.utils import role_required
from apps.admissions.models import HscAdmissions

from apps.accounts.models import User

# এই helper টা যোগ করুন (ফোন/সম্ভাব্য FK ধরে student User খুঁজে আনে)
def _resolve_student_user_from_admission(obj: HscAdmissions):
    """
    Try common patterns first (FK), otherwise fallback to phone match.
    """
    # 1) সম্ভাব্য FK নামগুলো ট্রাই করুন (আপনার মডেল অনুযায়ী যে আছে সেটা মিলবে)
    for attr in ("user", "student", "account", "applicant"):
        u = getattr(obj, attr, None)
        if isinstance(u, User):
            return u

    # 2) ফোন থেকে রেজল্ভ (আপনার HscAdmissions-এ যে ফিল্ড আছে সেটা দিন)
    phone_fields = ("phone", "mobile", "student_phone", "guardian_phone", "applicant_phone")
    for f in phone_fields:
        if hasattr(obj, f):
            raw = getattr(obj, f)
            phone = _normalize_phone(raw)
            if phone:
                u = User.objects.filter(phone_number=phone).first()
                if u:
                    return u

    return None




def _normalize_phone(s: str) -> str:
    """Normalize +880 / 880 → 0…"""
    s = (s or "").strip()
    if s.startswith("+880"):
        s = s[4:]
    elif s.startswith("880"):
        s = s[3:]
    if s and not s.startswith("0") and s[0] == "1":
        s = "0" + s
    return s


def _make_invoice_number(obj: HscAdmissions) -> str:
    # উদাহরণ: MI-20250812-00048  (date + pk padded)
    dt = localtime(obj.created_at) if obj.created_at else None
    dpart = dt.strftime("%y%m%d") if dt else "NA"
    return f"MI-{dpart}-{obj.pk:04d}"


def _build_invoice_context(obj: HscAdmissions):
    """কমন কনটেক্সট—দুই ভিউ-ই এটা ব্যবহার করবে"""
    org_name_bn = getattr(settings, "ORG_NAME_BN", "নবাবগঞ্জ সিটি কলেজ")
    org_name_en = getattr(settings, "ORG_NAME_EN", "Nawabganj City College")
    org_address_bn = getattr(settings, "ORG_ADDRESS_BN", "চাঁপাইনবাবগঞ্জ")

    ctx = {
        "student": obj,
        "invoice_no": _make_invoice_number(obj),
        "invoice_date": localtime(obj.created_at) if obj.created_at else None,
        "payment_date": localtime(obj.updated_at) if obj.updated_at else None,
        "line_description": "HSC Admission Fee",
        "org_name_bn": org_name_bn,
        "org_name_en": org_name_en,
        "org_address_bn": org_address_bn,
    }
    return ctx


# ---------- STAFF / ADMIN ----------
# @role_required(['master_admin', 'admin', 'sub_admin', 'teacher'])
# def admission_invoice_view(request, pk):
#     obj = get_object_or_404(
#         HscAdmissions.objects.select_related("add_session", "add_program"),
#         pk=pk,
#     )

#     # পেমেন্ট না হলে দেখাবো না
#     if obj.add_payment_status != "paid":
#         messages.warning(request, "এই ছাত্রের পেমেন্ট এখনো Paid নয়—Invoice দেখা যাবে না।")
#         return redirect(request.META.get("HTTP_REFERER", "admitted_students_list"))

#     context = _build_invoice_context(obj)
#     # স্টাফদের জন্য back_url
#     context["back_url"] = request.META.get("HTTP_REFERER", None) or "/dashboard/students/admitted/"
#     return render(request, "students/invoice_preview.html", context)

@role_required(['master_admin', 'admin', 'sub_admin', 'teacher'])
def admission_invoice_view(request, pk):
    obj = get_object_or_404(
        HscAdmissions.objects.select_related("add_session", "add_program"),
        pk=pk,
    )

    if obj.add_payment_status != "paid":
        messages.warning(request, "এই ছাত্রের পেমেন্ট এখনো Paid নয়—Invoice দেখা যাবে না।")
        return redirect(request.META.get("HTTP_REFERER", "admitted_students_list"))

    context = _build_invoice_context(obj)

    # ✅ স্টুডেন্টের cus_id যোগ করা
    student_user = _resolve_student_user_from_admission(obj)
    context["student_cus_id"] = getattr(student_user, "cus_id", None)

    # (ঐচ্ছিক) যদি স্টাফের (লগইনকৃত) cus_id-ও রাখতে চান:
    # context["staff_cus_id"] = getattr(request.user, "cus_id", None)

    context["back_url"] = request.META.get("HTTP_REFERER", None) or "/dashboard/students/admitted/"
    return render(request, "students/invoice_preview.html", context)



# ---------- STUDENT ----------
@role_required(['student'])
def student_admission_invoice_view(request, pk):
    print("janina")
    obj = get_object_or_404(HscAdmissions, pk=pk)

    # নিজের রেকর্ড না হলে 403
    user_phone = _normalize_phone(getattr(request.user, "phone_number", ""))
    if user_phone != (obj.add_mobile or "").strip():
        return HttpResponseForbidden("You are not allowed to view this invoice.")

    # paid না হলে ড্যাশবোর্ডে ফেরত
    if obj.add_payment_status != "paid":
        messages.warning(request, "Invoice is available only after payment confirmation.")
        return redirect("/dashboard/")  # তোমার student dashboard URL

    context = _build_invoice_context(obj)
    # স্টুডেন্টের জন্য back_url
    context["back_url"] = "/dashboard/"
    return render(request, "students/invoice_preview.html", context)


# Degree Section
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from django.db.models import Q
import re

from apps.admissions.models import DegreeAdmission, DegreePrograms


@method_decorator(role_required(['master_admin', 'admin', 'sub_admin', 'teacher']), name='dispatch')
class DegreeAdmittedStudentListView(ListView):
    model = DegreeAdmission
    template_name = 'students/admitted_students_list_honors.html'
    context_object_name = 'students'
    paginate_by = 25

    # --- helpers (same vibe as HSC) ---
    def _normalize_mobile_digits(self, val: str) -> str:
        if not val:
            return ''
        digits = re.sub(r'\D+', '', val)
        if digits.startswith('880'):
            digits = '0' + digits[3:]
        return digits

    def get_queryset(self):
        qs = (
            DegreeAdmission.objects
            .select_related('add_session', 'add_program', 'created_by')
        )

        # filters
        session = self.request.GET.get('session') or self.request.session.get('active_session_id')
        program = self.request.GET.get('program')
        group   = self.request.GET.get('group')

        if session:
            qs = qs.filter(add_session_id=session)
        if program:
            qs = qs.filter(add_program_id=program)
        if group:
            qs = qs.filter(add_admission_group=group)

        # search (id/name/mobile/roll/class_id/admission_roll)
        search = self.request.GET.get('search')
        if search:
            norm = self._normalize_mobile_digits(search)
            try:
                sid = int(search)
                qs = qs.filter(
                    Q(created_by_id=sid) |
                    Q(add_name__icontains=search) |
                    Q(add_mobile__icontains=norm) |
                    Q(add_class_roll__icontains=search) |
                    Q(add_admission_roll__icontains=search) |
                    Q(add_class_id__icontains=search)
                )
            except ValueError:
                qs = qs.filter(
                    Q(add_name__icontains=search) |
                    Q(add_mobile__icontains=norm) |
                    Q(add_class_roll__icontains=search) |
                    Q(add_admission_roll__icontains=search) |
                    Q(add_class_id__icontains=search)
                )

        # order (default asc)
        order = (self.request.GET.get('order') or 'asc').lower()
        if order == 'desc':
            qs = qs.order_by('-add_class_roll')
        else:
            qs = qs.order_by('add_class_roll')

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # Vuexy layout
        ctx = TemplateLayout.init(self, ctx)
        ctx["layout"] = "vertical"
        ctx["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", ctx)

        # filter sources
        ctx['sessions'] = Session.objects.all()
        ctx['programs'] = DegreePrograms.objects.all()
        ctx['groups']   = ['Ba', 'Bss', 'Bbs', 'Bsc']

        return ctx


@method_decorator(role_required(['master_admin', 'admin', 'sub_admin', 'teacher']), name='dispatch')
class DegreeAdmissionDetailView(DetailView):
    model = DegreeAdmission
    template_name = "students/admitted_student_details_honours.html"
    context_object_name = "student"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Layout
        context = TemplateLayout.init(self, context)
        context["layout"] = "vertical"
        context["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", context)

        return context

from collections import OrderedDict

from django.db import transaction, IntegrityError
from django.db.models import Q
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic.edit import UpdateView

from apps.admissions.forms import DegreeAdmissionForm
from apps.admissions.models import DegreeAdmission, DegreePrograms, DegreeSubjects
# from apps.programs.models import Programs
# from apps.fee.models import Fee



@method_decorator(
    role_required(['master_admin', 'admin', 'sub_admin', 'teacher']),
    name='dispatch'
)
class BaAdmissionUpdateView(UpdateView):
    model = DegreeAdmission
    template_name = "admissions_others/admission_form_honours.html"
    form_class = DegreeAdmissionForm
    context_object_name = "student"

    # ---- Form kwargs -> pass request/user + dynamic group config ----
    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        student = self.get_object()
        group = (student.add_admission_group or "Ba").strip()  # Ba/Bss/Bbs/Bsc
        kw.update({
            "request": self.request,
            "user": getattr(self.request, "user", None),
            "group": group,
            "max_selectable": 3,   # প্রয়োজনে view প্রতি কাস্টমাইজ করুন
        })
        return kw

    # ---- Context: layout + subject buckets (grid slots) ----
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx = TemplateLayout.init(self, ctx)
        ctx["layout"] = "vertical"
        ctx["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", ctx)

        student = self.object
        group = (student.add_admission_group or "Ba").strip()

        # Compulsory: All/All
        compulsory_qs = DegreeSubjects.objects.filter(
            sub_status="active",
            group__contains="All",
            sub_select__contains="all",
        ).order_by("sub_name")

        # Selectable: group or All, but not All/All
        selectable_qs = DegreeSubjects.objects.filter(
            sub_status="active"
        ).filter(
            Q(group__contains=group) | Q(group__contains="All")
        ).exclude(
            Q(group__contains="All") & Q(sub_select__contains="all")
        )

        def slot_qs(tag):
            return selectable_qs.filter(sub_select__contains=tag).order_by("sub_name")

        # Template-এর নতুন ডিজাইনের জন্য op1..op4 আগে, main শেষে রাখছি
        ctx["subjects_compulsory"] = compulsory_qs
        ctx["subjects_by_slot"] = OrderedDict([
            ("op1",  slot_qs("op1")),
            ("op2",  slot_qs("op2")),
            ("op3",  slot_qs("op3")),
            ("op4",  slot_qs("op4")),
            ("main", slot_qs("main")),   # main last
        ])

        ctx["group_name"] = group
        ctx["max_selectable"] = 3
        return ctx

    # ---- Save: sync main + M2M + (optional) recalc fee if session/group changed ----
    def form_valid(self, form):
        # hidden field থেকে main subject (JS sync করে দেয়)
        form.instance.main_subject_id = self.request.POST.get("main_subject") or None

        # (ঐচ্ছিক কিন্তু ভালো) session বদলালে ফি resolve করে নিন — server authoritative
        try:
            session = form.cleaned_data.get("add_session") or form.instance.add_session
            degree_program = Programs.objects.get(pro_name__iexact="degree")
            group = (form.instance.add_admission_group or self.object.add_admission_group or "Ba").strip()
            fee = Fee.objects.get(
                fee_session=session,              # object বা id — model অনুযায়ী ঠিক করুন
                fee_program=degree_program,
                fee_group__group_name__iexact=group
            )
            form.instance.add_amount = fee.amount
        except Programs.DoesNotExist:
            form.instance.add_amount = form.instance.add_amount or 0
        except Fee.DoesNotExist:
            form.instance.add_amount = form.instance.add_amount or 0

        # atomic save
        try:
            with transaction.atomic():
                resp = super().form_valid(form)
                # M2M subjects sync (compulsory আলাদা করে পাঠাই না; শুধু selectable ids)
                selected_subject_ids = self.request.POST.getlist("subjects")
                self.object.subjects.set(selected_subject_ids)
        except IntegrityError:
            form.add_error(None, "⚠️ আপডেট করার সময় একটি ত্রুটি হয়েছে।")
            return super().form_invalid(form)

        messages.success(self.request, f"✅ {self.object.add_name} — তথ্য আপডেট হয়েছে।")
        return resp

    def get_success_url(self):
        return reverse_lazy("degree_admitted_students_list")


from django.views.generic.edit import DeleteView
from django.urls import reverse_lazy
from apps.admissions.models import DegreeAdmission

@method_decorator(role_required(['master_admin']), name='dispatch')
class BaAdmissionDeleteView(DeleteView):
    model = DegreeAdmission
    success_url = reverse_lazy('degree_admitted_students_list')
    context_object_name = "student"

    def dispatch(self, request, *args, **kwargs):
        if request.method == "GET":
            try:
                self.object = self.get_object()
                self.object.delete()
                messages.success(request, "✅ Degree admission record deleted successfully.")
            except Exception as e:
                messages.error(request, f"❌ Failed to delete degree admission: {str(e)}")
            return redirect(self.success_url)

        return super().dispatch(request, *args, **kwargs)


# ====== BSS ======
@method_decorator(
    role_required(['master_admin', 'admin', 'sub_admin', 'teacher']),
    name='dispatch'
)
class BssAdmissionUpdateView(UpdateView):
    model = DegreeAdmission
    template_name = "admissions_others/admission_form_honours.html"
    form_class = DegreeAdmissionForm
    context_object_name = "student"

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        student = self.get_object()
        group = (student.add_admission_group or "Bss").strip()
        kw.update({
            "request": self.request,
            "user": getattr(self.request, "user", None),
            "group": group,
            "max_selectable": 3,
        })
        return kw

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx = TemplateLayout.init(self, ctx)
        ctx["layout"] = "vertical"
        ctx["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", ctx)

        student = self.object
        group = (student.add_admission_group or "Bss").strip()

        compulsory_qs = DegreeSubjects.objects.filter(
            sub_status="active",
            group__contains="All",
            sub_select__contains="all",
        ).order_by("sub_name")

        selectable_qs = DegreeSubjects.objects.filter(
            sub_status="active"
        ).filter(
            Q(group__contains=group) | Q(group__contains="All")
        ).exclude(
            Q(group__contains="All") & Q(sub_select__contains="all")
        )

        def slot_qs(tag):
            return selectable_qs.filter(sub_select__contains=tag).order_by("sub_name")

        ctx["subjects_compulsory"] = compulsory_qs
        ctx["subjects_by_slot"] = OrderedDict([
            ("op1",  slot_qs("op1")),
            ("op2",  slot_qs("op2")),
            ("op3",  slot_qs("op3")),
            ("op4",  slot_qs("op4")),
            ("main", slot_qs("main")),
        ])
        ctx["group_name"] = group
        ctx["max_selectable"] = 3
        return ctx

    def form_valid(self, form):
        form.instance.main_subject_id = self.request.POST.get("main_subject") or None

        try:
            session = form.cleaned_data.get("add_session") or form.instance.add_session
            degree_program = Programs.objects.get(pro_name__iexact="degree")
            group = (form.instance.add_admission_group or self.object.add_admission_group or "Bss").strip()
            fee = Fee.objects.get(
                fee_session=session,
                fee_program=degree_program,
                fee_group__group_name__iexact=group
            )
            form.instance.add_amount = fee.amount
        except Programs.DoesNotExist:
            form.instance.add_amount = form.instance.add_amount or 0
        except Fee.DoesNotExist:
            form.instance.add_amount = form.instance.add_amount or 0

        try:
            with transaction.atomic():
                resp = super().form_valid(form)
                selected_subject_ids = self.request.POST.getlist("subjects")
                self.object.subjects.set(selected_subject_ids)
        except IntegrityError:
            form.add_error(None, "⚠️ আপডেট করার সময় একটি ত্রুটি হয়েছে।")
            return super().form_invalid(form)

        messages.success(self.request, f"✅ {self.object.add_name} — তথ্য আপডেট হয়েছে।")
        return resp

    def get_success_url(self):
        return reverse_lazy("degree_admitted_students_list")


@method_decorator(role_required(['master_admin']), name='dispatch')
class BssAdmissionDeleteView(DeleteView):
    model = DegreeAdmission
    success_url = reverse_lazy('degree_admitted_students_list')
    context_object_name = "student"

    def dispatch(self, request, *args, **kwargs):
        if request.method == "GET":
            try:
                self.object = self.get_object()
                self.object.delete()
                messages.success(request, "✅ Degree admission record deleted successfully.")
            except Exception as e:
                messages.error(request, f"❌ Failed to delete degree admission: {str(e)}")
            return redirect(self.success_url)
        return super().dispatch(request, *args, **kwargs)


# ====== BSC ======
@method_decorator(
    role_required(['master_admin', 'admin', 'sub_admin', 'teacher']),
    name='dispatch'
)
class BscAdmissionUpdateView(UpdateView):
    model = DegreeAdmission
    template_name = "admissions_others/admission_form_honours.html"
    form_class = DegreeAdmissionForm
    context_object_name = "student"

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        student = self.get_object()
        group = (student.add_admission_group or "Bsc").strip()
        kw.update({
            "request": self.request,
            "user": getattr(self.request, "user", None),
            "group": group,
            "max_selectable": 3,
        })
        return kw

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx = TemplateLayout.init(self, ctx)
        ctx["layout"] = "vertical"
        ctx["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", ctx)

        student = self.object
        group = (student.add_admission_group or "Bsc").strip()

        compulsory_qs = DegreeSubjects.objects.filter(
            sub_status="active",
            group__contains="All",
            sub_select__contains="all",
        ).order_by("sub_name")

        selectable_qs = DegreeSubjects.objects.filter(
            sub_status="active"
        ).filter(
            Q(group__contains=group) | Q(group__contains="All")
        ).exclude(
            Q(group__contains="All") & Q(sub_select__contains="all")
        )

        def slot_qs(tag):
            return selectable_qs.filter(sub_select__contains=tag).order_by("sub_name")

        ctx["subjects_compulsory"] = compulsory_qs
        ctx["subjects_by_slot"] = OrderedDict([
            ("op1",  slot_qs("op1")),
            ("op2",  slot_qs("op2")),
            ("op3",  slot_qs("op3")),
            ("op4",  slot_qs("op4")),
            ("main", slot_qs("main")),
        ])
        ctx["group_name"] = group
        ctx["max_selectable"] = 3
        return ctx

    def form_valid(self, form):
        form.instance.main_subject_id = self.request.POST.get("main_subject") or None

        try:
            session = form.cleaned_data.get("add_session") or form.instance.add_session
            degree_program = Programs.objects.get(pro_name__iexact="degree")
            group = (form.instance.add_admission_group or self.object.add_admission_group or "Bsc").strip()
            fee = Fee.objects.get(
                fee_session=session,
                fee_program=degree_program,
                fee_group__group_name__iexact=group
            )
            form.instance.add_amount = fee.amount
        except Programs.DoesNotExist:
            form.instance.add_amount = form.instance.add_amount or 0
        except Fee.DoesNotExist:
            form.instance.add_amount = form.instance.add_amount or 0

        try:
            with transaction.atomic():
                resp = super().form_valid(form)
                selected_subject_ids = self.request.POST.getlist("subjects")
                self.object.subjects.set(selected_subject_ids)
        except IntegrityError:
            form.add_error(None, "⚠️ আপডেট করার সময় একটি ত্রুটি হয়েছে।")
            return super().form_invalid(form)

        messages.success(self.request, f"✅ {self.object.add_name} — তথ্য আপডেট হয়েছে।")
        return resp

    def get_success_url(self):
        return reverse_lazy("degree_admitted_students_list")


@method_decorator(role_required(['master_admin']), name='dispatch')
class BscAdmissionDeleteView(DeleteView):
    model = DegreeAdmission
    success_url = reverse_lazy('degree_admitted_students_list')
    context_object_name = "student"

    def dispatch(self, request, *args, **kwargs):
        if request.method == "GET":
            try:
                self.object = self.get_object()
                self.object.delete()
                messages.success(request, "✅ Degree admission record deleted successfully.")
            except Exception as e:
                messages.error(request, f"❌ Failed to delete degree admission: {str(e)}")
            return redirect(self.success_url)
        return super().dispatch(request, *args, **kwargs)


# ====== BBS ======
@method_decorator(
    role_required(['master_admin', 'admin', 'sub_admin', 'teacher']),
    name='dispatch'
)
class BbsAdmissionUpdateView(UpdateView):
    model = DegreeAdmission
    template_name = "admissions_others/admission_form_honours.html"
    form_class = DegreeAdmissionForm
    context_object_name = "student"

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        student = self.get_object()
        group = (student.add_admission_group or "Bbs").strip()
        kw.update({
            "request": self.request,
            "user": getattr(self.request, "user", None),
            "group": group,
            "max_selectable": 3,
        })
        return kw

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx = TemplateLayout.init(self, ctx)
        ctx["layout"] = "vertical"
        ctx["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", ctx)

        student = self.object
        group = (student.add_admission_group or "Bbs").strip()

        compulsory_qs = DegreeSubjects.objects.filter(
            sub_status="active",
            group__contains="All",
            sub_select__contains="all",
        ).order_by("sub_name")

        selectable_qs = DegreeSubjects.objects.filter(
            sub_status="active"
        ).filter(
            Q(group__contains=group) | Q(group__contains="All")
        ).exclude(
            Q(group__contains="All") & Q(sub_select__contains="all")
        )

        def slot_qs(tag):
            return selectable_qs.filter(sub_select__contains=tag).order_by("sub_name")

        ctx["subjects_compulsory"] = compulsory_qs
        ctx["subjects_by_slot"] = OrderedDict([
            ("op1",  slot_qs("op1")),
            ("op2",  slot_qs("op2")),
            ("op3",  slot_qs("op3")),
            ("op4",  slot_qs("op4")),
            ("main", slot_qs("main")),
        ])
        ctx["group_name"] = group
        ctx["max_selectable"] = 3
        return ctx

    def form_valid(self, form):
        form.instance.main_subject_id = self.request.POST.get("main_subject") or None

        try:
            session = form.cleaned_data.get("add_session") or form.instance.add_session
            degree_program = Programs.objects.get(pro_name__iexact="degree")
            group = (form.instance.add_admission_group or self.object.add_admission_group or "Bbs").strip()
            fee = Fee.objects.get(
                fee_session=session,
                fee_program=degree_program,
                fee_group__group_name__iexact=group
            )
            form.instance.add_amount = fee.amount
        except Programs.DoesNotExist:
            form.instance.add_amount = form.instance.add_amount or 0
        except Fee.DoesNotExist:
            form.instance.add_amount = form.instance.add_amount or 0

        try:
            with transaction.atomic():
                resp = super().form_valid(form)
                selected_subject_ids = self.request.POST.getlist("subjects")
                self.object.subjects.set(selected_subject_ids)
        except IntegrityError:
            form.add_error(None, "⚠️ আপডেট করার সময় একটি ত্রুটি হয়েছে।")
            return super().form_invalid(form)

        messages.success(self.request, f"✅ {self.object.add_name} — তথ্য আপডেট হয়েছে।")
        return resp

    def get_success_url(self):
        return reverse_lazy("degree_admitted_students_list")


@method_decorator(role_required(['master_admin']), name='dispatch')
class BbsAdmissionDeleteView(DeleteView):
    model = DegreeAdmission
    success_url = reverse_lazy('degree_admitted_students_list')
    context_object_name = "student"

    def dispatch(self, request, *args, **kwargs):
        if request.method == "GET":
            try:
                self.object = self.get_object()
                self.object.delete()
                messages.success(request, "✅ Degree admission record deleted successfully.")
            except Exception as e:
                messages.error(request, f"❌ Failed to delete degree admission: {str(e)}")
            return redirect(self.success_url)
        return super().dispatch(request, *args, **kwargs)





# all degree delete

@method_decorator(role_required(['master_admin']), name='dispatch')
class DegreeAdmissionDeleteView(DeleteView):
    model = DegreeAdmission
    success_url = reverse_lazy('degree_admitted_students_list')
    context_object_name = "student"

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        url_group = (self.kwargs.get('group') or '').strip().lower()
        obj_group = (obj.add_admission_group or '').strip().lower()
        if url_group and obj_group and url_group != obj_group:
            # URL এ দেওয়া group আর রেকর্ডের group mismatch হলে 404
            raise Http404("Group does not match.")
        return obj

    # GET-এও ডিলিট সাপোর্ট (আগের মতো এক-ক্লিক)
    def dispatch(self, request, *args, **kwargs):
        if request.method == "GET":
            try:
                self.object = self.get_object()
                self.object.delete()
                messages.success(request, "✅ Degree admission record deleted successfully.")
            except Exception as e:
                messages.error(request, f"❌ Failed to delete degree admission: {e}")
            return redirect(self.success_url)
        return super().dispatch(request, *args, **kwargs)
