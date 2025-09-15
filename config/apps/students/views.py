from django.views.generic import ListView
from apps.admissions.models import HscAdmissions
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
from apps.accounts.utils import role_required
from apps.admissions.models import HscAdmissions, Programs, Session

@method_decorator(role_required(['master_admin', 'admin', 'sub_admin', 'teacher']), name='dispatch')
class AdmittedStudentListView(ListView):
    model = HscAdmissions
    template_name = 'students/admitted_students_list.html'
    context_object_name = 'students'
    paginate_by = 25

    def get_queryset(self):
        queryset = super().get_queryset().select_related('add_session', 'add_program')

        session = self.request.GET.get('session') or self.request.session.get('active_session_id')
        program = self.request.GET.get('program')
        group   = self.request.GET.get('group')

        if session:
            queryset = queryset.filter(add_session_id=session)
        if program:
            queryset = queryset.filter(add_program_id=program)
        if group:
            queryset = queryset.filter(add_admission_group=group)

        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(add_name__icontains=search) |
                Q(add_father__icontains=search) |
                Q(add_mobile__icontains=search) |
                Q(add_class_roll__icontains=search)
            )

        # নতুন অংশ: order প্যারামিটার দেখুন
        order = self.request.GET.get('order')
        if order == 'desc':
            queryset = queryset.order_by('-add_class_roll')
        else:
            queryset = queryset.order_by('add_class_roll')  # ডিফল্ট ascending

        return queryset

    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     context = TemplateLayout.init(self, context)
    #     context["layout"] = "vertical"
    #     context["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", context)
    #     context['sessions'] = Session.objects.all()
    #     context['programs'] = Programs.objects.all()
    #     context['groups'] = GROUP_CHOICES_MAP.items()
    #     return context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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

# @require_POST
# @role_required(['master_admin', 'admin', 'sub_admin', 'teacher'])
# def update_admission_payment(request, pk):
#     obj = get_object_or_404(HscAdmissions, pk=pk)
#     form = HscPaymentReviewForm(request.POST, instance=obj)
#     next_url = request.POST.get("next") or request.META.get("HTTP_REFERER")

#     if form.is_valid():
#         form.save()
#         messages.success(request, f"✅ Payment updated for {obj.add_name}.")
#         return redirect(next_url or "admitted_students_list")

#     # invalid হলে error মেসেজ দেখিয়ে লিস্টেই ফেরত
#     messages.error(request, "❌ Payment update failed. Please check the form.")
#     return redirect(next_url or "admitted_students_list")






@require_POST
@role_required(['master_admin', 'admin', 'sub_admin', 'teacher'])
def update_admission_payment(request, pk):
    obj = get_object_or_404(HscAdmissions, pk=pk)
    form = HscPaymentReviewForm(request.POST, instance=obj)
    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER") or "/"

    if not form.is_valid():
        messages.error(request, "❌ Payment update failed. Please check the form.")
        return redirect(next_url)

    # শুধুমাত্র payment ফিল্ডগুলো আপডেট করুন
    partial = form.save(commit=False)
    try:
        # normalize trxid
        if not partial.add_trxid:
            partial.add_trxid = None

        # ইন-মেমরি অবজেক্টে সেট করে তারপর update_fields দিয়ে সেভ
        obj.add_payment_method = partial.add_payment_method
        obj.add_amount = partial.add_amount
        obj.add_trxid = partial.add_trxid
        obj.add_slip = partial.add_slip
        obj.add_payment_status = partial.add_payment_status
        obj.add_payment_note = partial.add_payment_note

        obj.save(update_fields=[
            "add_payment_method",
            "add_amount",
            "add_trxid",
            "add_slip",
            "add_payment_status",
            "add_payment_note",
            "updated_at",
        ])

        messages.success(request, f"✅ Payment updated for {obj.add_name or obj.id}.")
    except IntegrityError:
        messages.error(request, "❌ Transaction ID must be unique.")
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

    # def form_valid(self, form):
    #     # স্বাভাবিক UpdateView সেভ করুন
    #     response = super().form_valid(form)

    #     group = self.object.add_admission_group or "science"

    #     # বিজ্ঞান গ্রুপে all + বিজ্ঞান optional সাবজেক্টগুলো যোগ করুন
    #     subjects_all = Subjects.objects.filter(sub_status='active').filter(
    #         Q(sub_select__contains='all') |
    #         (Q(group='science') & Q(sub_select__contains='optional'))
    #     )
    #     self.object.subjects.set(subjects_all)

    #     messages.success(self.request, f"✅ {self.object.add_name}'s data updated successfully.")
    #     return response

    def form_valid(self, form):
        try:
            with transaction.atomic():
                response = super().form_valid(form)
        except IntegrityError:
            # একই রোল থাকলে এই অংশে আসবে
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

# @method_decorator(
#     role_required(['master_admin', 'admin', 'sub_admin', 'teacher']),
#     name='dispatch'
# )
# class HscAdmissionUpdateCommerceView(UpdateView):
#     model = HscAdmissions
#     template_name = "admissions/admission_form.html"
#     form_class = HscAdmissionForm
#     context_object_name = "student"

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)

#         # layout ও user
#         context["user"] = self.request.user
#         context = TemplateLayout.init(self, context)
#         context["layout"] = "vertical"
#         context["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", context)

#         student = self.object
#         group = student.add_admission_group or "commerce"

#         context["subjects_all"]      = Subjects.objects.filter(sub_status="active", sub_select__contains="all")
#         context["subjects_optional"] = Subjects.objects.filter(group=group, sub_status="active", sub_select__contains="optional")
#         context["subjects_main"]     = Subjects.objects.filter(group=group, sub_status="active", sub_select__contains="main")
#         context["subjects_fourth"]   = Subjects.objects.filter(group=group, sub_status="active", sub_select__contains="fourth")
#         return context

#     def form_valid(self, form):
#         # স্বাভাবিক UpdateView সেভ করুন
#         response = super().form_valid(form)

#         # যদি fourth_subject POST থেকে না আসে (কমার্স ফর্মে disabled ছিল), ডিফল্ট সাবজেক্ট সেট করুন
#         if not form.instance.fourth_subject_id:
#             default_fourth = Subjects.objects.filter(
#                 group='commerce', sub_status='active', sub_select__contains='fourth'
#             ).first()
#             if default_fourth:
#                 self.object.fourth_subject = default_fourth
#                 self.object.save(update_fields=['fourth_subject'])

#         # কমার্স গ্রুপে all + কমার্স optional সাবজেক্টগুলো যোগ করুন
#         subjects_all = Subjects.objects.filter(sub_status='active').filter(
#             Q(sub_select__contains='all') |
#             (Q(group='commerce') & Q(sub_select__contains='optional'))
#         )
#         self.object.subjects.set(subjects_all)

#         messages.success(self.request, f"✅ {self.object.add_name}'s data updated successfully.")
#         return response

#     def get_success_url(self):
#         return reverse_lazy("admitted_students_list")




@method_decorator(
    role_required(['master_admin', 'admin', 'sub_admin', 'teacher']),
    name='dispatch'
)
class HscAdmissionUpdateCommerceView(UpdateView):
    model = HscAdmissions
    template_name = "admissions/admission_form_commerce.html"
    form_class = HscAdmissionForm
    context_object_name = "student" 

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user"] = self.request.user
        context = TemplateLayout.init(self, context)
        context["layout"] = "vertical"
        context["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", context)

        student = self.object
        group = student.add_admission_group or "commerce"

        context["subjects_all"]      = Subjects.objects.filter(sub_status="active", sub_select__contains="all")
        context["subjects_optional"] = Subjects.objects.filter(group=group, sub_status="active", sub_select__contains="optional")
        context["subjects_main"]     = Subjects.objects.filter(group=group, sub_status="active", sub_select__contains="main")
        context["subjects_fourth"]   = Subjects.objects.filter(group=group, sub_status="active", sub_select__contains="fourth")
        return context

    def form_valid(self, form):
        # ফর্ম সেভ করার সময় ইউনিক কনস্ট্রেইন্ট ভঙ্গ হলে ক্যাচ করুন
        try:
            with transaction.atomic():
                response = super().form_valid(form)
        except IntegrityError:
            # একই গ্রুপে একই রোল নম্বরের জন্য ব্যবহারকারীকে বার্তা দিন
            form.add_error('add_class_roll', "এই গ্রুপে এই রোল নম্বর ইতিমধ্যেই আছে।")
            return self.form_invalid(form)

        # কমার্স গ্রুপে fourth_subject ইনপুট পাঠানো না হলে একটি ডিফল্ট নির্বাচন করুন
        if not form.instance.fourth_subject_id:
            default_fourth = Subjects.objects.filter(
                group='commerce', sub_status='active', sub_select__contains='fourth'
            ).first()
            if default_fourth:
                self.object.fourth_subject = default_fourth
                self.object.save(update_fields=['fourth_subject'])

        # “all” + commerce-এর “optional” সাবজেক্টগুলো ManyToMany ফিল্ডে সেট করুন
        subjects_all = Subjects.objects.filter(sub_status='active').filter(
            Q(sub_select__contains='all') |
            (Q(group='commerce') & Q(sub_select__contains='optional'))
        )
        self.object.subjects.set(subjects_all)

        messages.success(
            self.request,
            f"✅ {self.object.add_name}'s data updated successfully."
        )
        return response

    def get_success_url(self):
        return reverse_lazy("admitted_students_list")





# Arts Update View
from apps.admissions.forms import ArtsAdmissionForm



# @method_decorator(role_required(['master_admin', 'admin', 'sub_admin', 'teacher']), name='dispatch')
# class HscAdmissionUpdateArtsView(UpdateView):
#     model = HscAdmissions
#     form_class = ArtsAdmissionForm
#     template_name = "admissions/admission_form_arts.html"
#     context_object_name = "student"
#     success_url = reverse_lazy("admitted_students_list")

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)

#         # Layout সেট করা
#         context = TemplateLayout.init(self, context)
#         context["layout"] = "vertical"
#         context["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", context)

#         group, status = "arts", "active"
#         student = self.object

#         def with_meta(qs):
#             """
#             ব্যবহৃত ও বাকি আসনের তথ্য যুক্ত করে সাবজেক্ট কুয়েরি রিটার্ন।
#             ছাত্রের বর্তমানে নির্বাচিত সাবজেক্টগুলিকে full না দেখানোর জন্য ব্যবহার।
#             """
#             for s in qs:
#                 s.used = getattr(s, "used_count", 0) or 0
#                 s.left = None if s.limit is None else max(s.limit - s.used, 0)
#                 s.full = (s.limit is not None) and (s.used >= s.limit)
#                 # edit mode: student's own selections should never be disabled
#                 if student:
#                     if (student.main_subject_id and s.id == student.main_subject_id) \
#                        or (student.fourth_subject_id and s.id == student.fourth_subject_id) \
#                        or (student.optional_subject_id and s.id == student.optional_subject_id) \
#                        or (student.optional_subject_2_id and s.id == student.optional_subject_2_id):
#                         s.full = False
#             return qs

#         # Common subjects (sub_select contains 'all')
#         context["subjects_all"] = with_meta(
#             Subjects.objects.filter(sub_status=status, sub_select__contains='all').order_by("sub_name")
#         )
#         # Optional Group A: contains 'optional' but not 'optional2'
#         context["subjects_optional"] = with_meta(
#             Subjects.objects.filter(
#                 group=group, sub_status=status, sub_select__contains='optional'
#             ).exclude(
#                 sub_select__contains='optional2'
#             ).order_by('sub_name')
#         )
#         # Optional Group B: contains 'optional2'
#         context["subjects_optional2"] = with_meta(
#             Subjects.objects.filter(group=group, sub_status=status, sub_select__contains='optional2').order_by("sub_name")
#         )
#         # Main subjects
#         context["subjects_main"] = with_meta(
#             Subjects.objects.filter(group=group, sub_status=status, sub_select__contains='main').order_by("sub_name")
#         )
#         # Fourth subjects
#         context["subjects_fourth"] = with_meta(
#             Subjects.objects.filter(group=group, sub_status=status, sub_select__contains='fourth').order_by("sub_name")
#         )

#         context["student"] = student
#         return context

#     def form_valid(self, form):
#         # Program ও group সেট করা
#         try:
#             hsc_program = Programs.objects.get(pro_name__iexact="hsc")
#             form.instance.add_program = hsc_program
#             form.instance.add_admission_group = "arts"
#         except Programs.DoesNotExist:
#             form.add_error(None, "HSC program not found.")
#             return self.form_invalid(form)

#         # Active session from session
#         session_id = self.request.session.get("active_session_id")
#         if session_id:
#             form.instance.add_session_id = session_id
#         else:
#             form.add_error(None, "No active session selected.")
#             print(form.errors)
#             return self.form_invalid(form)

#         # POST থেকে সাবজেক্ট আইডি সেট করা
#         form.instance.main_subject_id       = self.request.POST.get("main_subject") or None
#         form.instance.fourth_subject_id     = self.request.POST.get("fourth_subject") or None
#         form.instance.optional_subject_id   = self.request.POST.get("optional_subject") or None
#         form.instance.optional_subject_2_id = self.request.POST.get("optional_subject_2") or None

#         # প্রথমে মডেল সেভ করি
#         self.object = form.save()

#         # "all" সাবজেক্টসহ নির্বাচিত optional গুলো ManyToMany তে সেট করা
#         selected_subject_ids = list(
#             Subjects.objects.filter(sub_status="active", sub_select__contains='all').values_list('id', flat=True)
#         )
#         if form.instance.optional_subject_id:
#             selected_subject_ids.append(form.instance.optional_subject_id)
#         if form.instance.optional_subject_2_id:
#             selected_subject_ids.append(form.instance.optional_subject_2_id)

#         self.object.subjects.set(selected_subject_ids)

#         messages.success(
#             self.request,
#             f"✅ {self.object.add_name}'s data updated successfully."
#         )
#         # super().form_valid() দিচ্ছি যাতে get_success_url() ও অন্যান্য ডিফল্ট আচরণ বজায় থাকে
#         return super().form_valid(form)

#     def form_invalid(self, form):
#         print("Form invalid:", form.errors)
#         return super().form_invalid(form)




@method_decorator(
    role_required(['master_admin', 'admin', 'sub_admin', 'teacher']),
    name='dispatch'
)
class HscAdmissionUpdateArtsView(UpdateView):
    model = HscAdmissions
    form_class = ArtsAdmissionForm
    template_name = "admissions/admission_form_arts.html"
    context_object_name = "student"
    success_url = reverse_lazy("admitted_students_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = TemplateLayout.init(self, context)
        context["layout"] = "vertical"
        context["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", context)

        group, status = "arts", "active"
        student = self.object

        # with_meta helper unchanged …
        # (আপনার আগের কোডের সাথে একই)

        # … (Subjects তালিকা with_meta সহ context এ যোগ করা)
        return context

    def form_valid(self, form):
        # Program ও group ফিক্স করুন
        try:
            hsc_program = Programs.objects.get(pro_name__iexact="hsc")
            form.instance.add_program = hsc_program
            form.instance.add_admission_group = "arts"
        except Programs.DoesNotExist:
            form.add_error(None, "HSC program not found.")
            return self.form_invalid(form)

        # Session লক logic আপনার আগের কোড অনুযায়ী …

        # POST থেকে subject IDs সেট করা
        form.instance.main_subject_id       = self.request.POST.get("main_subject") or None
        form.instance.fourth_subject_id     = self.request.POST.get("fourth_subject") or None
        form.instance.optional_subject_id   = self.request.POST.get("optional_subject") or None
        form.instance.optional_subject_2_id = self.request.POST.get("optional_subject_2") or None

        # ইউনিক কনস্ট্রেইন্ট (রোল) ভঙ্গ হলে ধরা
        try:
            with transaction.atomic():
                self.object = form.save()
        except IntegrityError:
            form.add_error('add_class_roll', "এই গ্রুপে এই রোল নম্বর ইতিমধ্যেই আছে।")
            return self.form_invalid(form)

        # “all” সাবজেক্ট এবং নির্বাচিত optional/optional2 সাবজেক্টগুলো ManyToMany তে সেট করা
        selected_subject_ids = list(
            Subjects.objects.filter(sub_status="active", sub_select__contains='all').values_list('id', flat=True)
        )
        if form.instance.optional_subject_id:
            selected_subject_ids.append(form.instance.optional_subject_id)
        if form.instance.optional_subject_2_id:
            selected_subject_ids.append(form.instance.optional_subject_2_id)

        self.object.subjects.set(selected_subject_ids)

        messages.success(
            self.request,
            f"✅ {self.object.add_name}'s data updated successfully."
        )
        return super().form_valid(form)






from django.shortcuts import redirect

# 🗑️ Delete View

@method_decorator(role_required(['master_admin', 'admin', 'sub_admin', 'teacher']), name='dispatch')
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
# views.py
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.utils.timezone import localtime
from django.conf import settings

from apps.accounts.utils import role_required
from apps.admissions.models import HscAdmissions


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
    dpart = dt.strftime("%Y%m%d") if dt else "NA"
    return f"MI-{dpart}-{obj.pk:05d}"


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
@role_required(['master_admin', 'admin', 'sub_admin', 'teacher'])
def admission_invoice_view(request, pk):
    obj = get_object_or_404(
        HscAdmissions.objects.select_related("add_session", "add_program"),
        pk=pk,
    )

    # পেমেন্ট না হলে দেখাবো না
    if obj.add_payment_status != "paid":
        messages.warning(request, "এই ছাত্রের পেমেন্ট এখনো Paid নয়—Invoice দেখা যাবে না।")
        return redirect(request.META.get("HTTP_REFERER", "admitted_students_list"))

    context = _build_invoice_context(obj)
    # স্টাফদের জন্য back_url
    context["back_url"] = request.META.get("HTTP_REFERER", None) or "/dashboard/students/admitted/"
    return render(request, "students/invoice_preview.html", context)


# ---------- STUDENT ----------
@role_required(['student'])
def student_admission_invoice_view(request, pk):
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

from django.views.generic import ListView
from apps.admissions.models import DegreeAdmission, DegreePrograms

@method_decorator(role_required(['master_admin', 'admin', 'sub_admin', 'teacher']), name='dispatch')
class DegreeAdmittedStudentListView(ListView):
    model = DegreeAdmission
    template_name = 'students/admitted_students_list_honors.html'
    context_object_name = 'students'
    paginate_by = 25

    def get_queryset(self):
        queryset = super().get_queryset().select_related('add_session', 'add_program')

        # Filter values
        session = self.request.GET.get('session') or self.request.session.get('active_session_id')
        program = self.request.GET.get('program')
        group = self.request.GET.get('group')

        if session:
            queryset = queryset.filter(add_session_id=session)
        if program:
            queryset = queryset.filter(add_program_id=program)
        if group:
            queryset = queryset.filter(add_admission_group=group)

        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(add_name__icontains=search) |
                Q(add_mobile__icontains=search) |
                Q(add_class_roll__icontains=search)
            )

        return queryset


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Layout
        context = TemplateLayout.init(self, context)
        context["layout"] = "vertical"
        context["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", context)

        context['sessions'] = Session.objects.all()
        context['programs'] = DegreePrograms.objects.all()
        context['groups'] = ['Ba', 'Bss', 'Bbs', 'Bsc']
        return context



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


from apps.admissions.forms import DegreeAdmissionForm
from apps.admissions.models import DegreeAdmission, DegreeSubjects
from django.views.generic.edit import UpdateView
from django.urls import reverse_lazy

# ✏️ BA Update View (Corrected)

@method_decorator(role_required(['master_admin', 'admin', 'sub_admin', 'teacher']), name='dispatch')
class BaAdmissionUpdateView(UpdateView):
    model = DegreeAdmission
    template_name = "admissions_others/admission_form_honours.html"
    form_class = DegreeAdmissionForm
    context_object_name = "student"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = TemplateLayout.init(self, context)
        context["layout"] = "vertical"
        context["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", context)

        student = self.object
        group = student.add_admission_group or "Ba"  # Ensure proper case

        # ✅ Correct model used here
        context["subjects_all"] = DegreeSubjects.objects.filter(group=group, sub_status="active")

        return context

    def form_valid(self, form):
        response = super().form_valid(form)

        # ✅ Sync only selected subjects from POST data
        selected_subject_ids = self.request.POST.getlist("subjects")
        self.object.subjects.set(selected_subject_ids)

        messages.success(
            self.request,
            f"✅ {self.object.add_name}'s data updated successfully."
        )
        return response

    def get_success_url(self):
        return reverse_lazy('degree_admitted_students_list')


from django.views.generic.edit import DeleteView
from django.urls import reverse_lazy
from apps.admissions.models import DegreeAdmission

@method_decorator(role_required(['master_admin', 'admin', 'sub_admin', 'teacher']), name='dispatch')
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
