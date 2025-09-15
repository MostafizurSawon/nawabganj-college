from django.views.generic import TemplateView
from django.views.generic import ListView

from django.contrib import messages

from functools import wraps
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from apps.admissions.models import Programs

from apps.accounts.utils import role_required
from django.utils.decorators import method_decorator
from web_project import TemplateLayout, TemplateHelper

# @method_decorator(role_required(['master_admin', 'admin', 'sub_admin', 'teacher']), name='dispatch')
 
# Create your views here.
@method_decorator(role_required(['master_admin', 'admin', 'sub_admin', 'teacher']), name='dispatch')
class TableView(TemplateView):
    # Predefined function
    def get_context_data(self, **kwargs):
        # A function to init the global layout. It is defined in web_project/__init__.py file
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))

        return context


from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, View
from .models import Subject
from .forms import SubjectForm

@method_decorator(role_required(['master_admin', 'admin', 'sub_admin']), name='dispatch')
class SubjectDashboardView(TemplateView):
    template_name = "exam/subject_list.html"

    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))

        # Edit mode
        edit_id = self.request.GET.get("edit")
        if edit_id:
            subject = get_object_or_404(Subject, id=edit_id)
            form = SubjectForm(instance=subject)
            context["edit_id"] = edit_id
        else:
            form = SubjectForm()

        context["form"] = form
        context["subjects"] = Subject.objects.all()
        context["msg"] = self.request.session.pop("msg", None)
        return context

    def post(self, request, *args, **kwargs):
        edit_id = request.POST.get("edit_id")
        if edit_id:
            subject = get_object_or_404(Subject, id=edit_id)
            form = SubjectForm(request.POST, instance=subject)
        else:
            form = SubjectForm(request.POST)

        if form.is_valid():
            subject = form.save(commit=False)
            subject.save()
            form.save_m2m()  

            request.session["msg"] = "Subject updated successfully!" if edit_id else "Subject added successfully!"
            return redirect("subject_list")



        # Form invalid, return with errors
        context = self.get_context_data()
        context["form"] = form
        if edit_id:
            context["edit_id"] = edit_id
        return render(request, self.template_name, context)


# @method_decorator(role_required(['master_admin', 'admin', 'sub_admin']), name='dispatch')
# class DeleteSubjectView(View):
#     def get(self, request, pk):
#         subject = get_object_or_404(Subject, pk=pk)
#         subject.delete()
#         request.session["msg"] = "Subject deleted successfully!"
#         return redirect("subject_list")




from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q

from .models import Exam, Subject        
from apps.admissions.models import Session
from .forms import ExamForm



from .utils import get_hsc_admissions_for_exam


@method_decorator(role_required(['master_admin', 'admin', 'sub_admin']), name='dispatch')
class ExamCreateView(View):
    template_name = 'exam/exam_form.html'

    def _get_active_session_id(self, request):
        """session থেকে active_session_id পড়বে; না থাকলে None."""
        return request.session.get('active_session_id')

    def get_filtered_paginated_exams(self, request):
        search_query = request.GET.get('search', '').strip()
        class_filter = request.GET.get('class_filter', '').strip()   # exam_class (Programs.id)
        session_filter = request.GET.get('session_filter', '').strip()
        group_filter = request.GET.get('group_filter', '').strip()

        exams = (
            Exam.objects
            .select_related('exam_session', 'exam_class')
            .prefetch_related('subjects')
            .order_by('-id')
        )

        # Session filter: explicit > active_session
        if session_filter:
            exams = exams.filter(exam_session_id=session_filter)
        else:
            active_sid = self._get_active_session_id(request)
            if active_sid:
                exams = exams.filter(exam_session_id=active_sid)

        if class_filter:
            exams = exams.filter(exam_class_id=class_filter)

        if group_filter:
            exams = exams.filter(group_name=group_filter)

        if search_query:
            exams = exams.filter(
                Q(exam_name__icontains=search_query) |
                Q(subjects__name__icontains=search_query) |
                Q(exam_session__ses_name__icontains=search_query) |
                Q(exam_class__pro_name__icontains=search_query)
            ).distinct()

        paginator = Paginator(exams, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        return page_obj, search_query, class_filter, session_filter, group_filter

    def get(self, request):
        context = TemplateLayout.init(self, {})

        # Form initial: active session -> exam_session
        active_sid = self._get_active_session_id(request)
        context['form'] = ExamForm(initial={'exam_session': active_sid}) if active_sid else ExamForm()

        page_obj, search_query, class_filter, session_filter, group_filter = self.get_filtered_paginated_exams(request)

        context.update({
            'page_obj': page_obj,
            'search_query': search_query,
            'class_filter': class_filter,
            'session_filter': session_filter,
            'group_filter': group_filter,
            'classes': Programs.objects.filter(pro_status='active').order_by('pro_name'),  
            'sessions': Session.objects.all().order_by('-id'),                              
        })
        return render(request, self.template_name, context)

    def post(self, request):
        form = ExamForm(request.POST)
        page_obj, search_query, class_filter, session_filter, group_filter = self.get_filtered_paginated_exams(request)

        if form.is_valid():
            exam = form.save()              
            matched = get_hsc_admissions_for_exam(exam).count()
            messages.success(request, f"✅ Exam created. Matched HSC students: {matched}")
            return redirect('exam_create')
        else:
            messages.error(request, "❌ Failed to create Exam. Please check the form.")

        context = TemplateLayout.init(self, {})
        context.update({
            'form': form,
            'page_obj': page_obj,
            'search_query': search_query,
            'class_filter': class_filter,
            'session_filter': session_filter,
            'group_filter': group_filter,
            'classes': Programs.objects.filter(pro_status='active').order_by('pro_name'),
            'sessions': Session.objects.all().order_by('-id'),
        })
        return render(request, self.template_name, context)




# Exam Edit view

from django.views.generic.edit import UpdateView
from django.urls import reverse_lazy
# from apps.admissions.models import Admissions

@method_decorator(role_required(['master_admin', 'admin', 'sub_admin']), name='dispatch')
class ExamEditView(UpdateView):
    model = Exam
    form_class = ExamForm
    template_name = 'exam/exam_form.html'
    success_url = reverse_lazy('exam_create')

    def form_valid(self, form):
        resp = super().form_valid(form)
        from .utils import get_hsc_admissions_for_exam
        matched = get_hsc_admissions_for_exam(self.object).count()
        messages.success(self.request, f"Exam updated. Matched HSC students: {matched}")
        return resp


    def form_invalid(self, form):
        messages.error(self.request, "Please correct the errors in the form.")
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(TemplateLayout.init(self, context))

        # তালিকা টেবিল (simple paginate)
        context['page_obj'] = Paginator(
            Exam.objects.select_related('exam_session', 'exam_class').order_by('-id'),
            10
        ).get_page(self.request.GET.get('page'))

        # dropdown data (template expects these keys)
        context['classes']  = Programs.objects.filter(pro_status='active').order_by('pro_name')
        context['sessions'] = Session.objects.all().order_by('-id')

        # edit মোডে already-selected subjects (JS pre-check এর জন্য)
        exam = self.object
        context['selected_subject_ids'] = list(exam.subjects.values_list('id', flat=True))
        return context


@method_decorator(role_required(['master_admin', 'admin', 'sub_admin']), name='dispatch')
class ExamDeleteView(View):
    def post(self, request, pk):
        exam = get_object_or_404(Exam, pk=pk)
        exam.delete()
        messages.success(request, "🗑️ Exam deleted successfully.")
        return redirect('exam_create')


from django.views.decorators.http import require_POST

# @require_POST
# @admin_role_required

# @method_decorator(role_required(['master_admin', 'admin', 'sub_admin']), name='dispatch')
# def delete_exam(request, pk):
#     if request.method == 'POST':
#         exam = get_object_or_404(Exam, pk=pk)
#         exam.delete()
#         messages.success(request, "🗑️ Exam deleted successfully.")
#     return redirect('exam_create')  




from django.http import JsonResponse
from .models import Subject

def get_subjects_by_class(request, class_id):
    subjects = Subject.objects.filter(program__id=class_id).values('id', 'name')
    return JsonResponse({'subjects': list(subjects)})




# from .models import Exam, ExamRecord, SubjectMark

# @method_decorator(role_required(['master_admin', 'admin', 'sub_admin']), name='dispatch')
# class ExamStudentsMarksView(TemplateView):
#     template_name = 'exam/exam_students_marks.html'

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context = TemplateLayout.init(self, context)  # Vuexy layout context

#         exam_id = self.kwargs.get('exam_id')
#         exam = get_object_or_404(Exam, id=exam_id)
#         exam_records = ExamRecord.objects.filter(exam=exam).select_related('student')
#         subjects = exam.subjects.all()

#         subject_marks = SubjectMark.objects.filter(exam_record__in=exam_records)
#         marks_dict = {}
#         for sm in subject_marks:
#             marks_dict.setdefault(sm.exam_record_id, {})[sm.subject_id] = sm.mark

#         context.update({
#             'exam': exam,
#             'exam_records': exam_records,
#             'subjects': subjects,
#             'marks_dict': marks_dict,
#         })

#         return context

#     def post(self, request, *args, **kwargs):
#         exam_id = self.kwargs.get('exam_id')
#         exam = get_object_or_404(Exam, id=exam_id)
#         exam_records = ExamRecord.objects.filter(exam=exam).select_related('student')
#         subjects = exam.subjects.all()

#         for exam_record in exam_records:
#             for subject in subjects:
#                 key = f"mark_{exam_record.id}_{subject.id}"
#                 mark_val = request.POST.get(key)
#                 if mark_val is not None and mark_val != '':
#                     try:
#                         mark_val = float(mark_val)
#                     except ValueError:
#                         continue  # skip invalid values

#                     subject_mark, created = SubjectMark.objects.get_or_create(
#                         exam_record=exam_record,
#                         subject=subject,
#                         defaults={'mark': mark_val}
#                     )
#                     if not created:
#                         subject_mark.mark = mark_val
#                         subject_mark.save()
#                 else:
#                     # Optional: delete if empty
#                     SubjectMark.objects.filter(exam_record=exam_record, subject=subject).delete()

#         messages.success(request, "Marks saved successfully!")
#         return redirect('exam_students_marks', exam_id=exam.id)




from django.forms import modelformset_factory

from apps.admissions.models import Session
from .models import Exam, ExamSubject
from django import forms

# ----- ExamSubject formset (teacher marks setup) -----
ExamSubjectFormSet = modelformset_factory(
    ExamSubject,
    fields=[
        'full_marks', 'pass_marks',
        'cq_pass_marks', 'mcq_pass_marks',
        'practical_pass_marks', 'ct_pass_marks'
    ],
    extra=0,
    widgets={
        'full_marks':          forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        'pass_marks':          forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        'cq_pass_marks':       forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        'mcq_pass_marks':      forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        'practical_pass_marks':forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        'ct_pass_marks':       forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
    }
)

@method_decorator(role_required(['master_admin', 'admin', 'sub_admin']), name='dispatch')
class ExamListView(ListView):
    model = Exam
    template_name = "exam/exam_list.html"
    paginate_by = 10
    context_object_name = 'exams'

    def get_queryset(self):
        qs = (super()
              .get_queryset()
              .select_related('exam_session', 'exam_class')
              .prefetch_related('subjects')
              .order_by('-id'))

        search = self.request.GET.get('search', '').strip()
        class_filter = self.request.GET.get('class_filter', '').strip()
        exam_filter = self.request.GET.get('exam_filter', '').strip()
        start_date = self.request.GET.get('start_date', '').strip()
        end_date = self.request.GET.get('end_date', '').strip()
        session_filter = self.request.GET.get('session_filter', '').strip()

        if session_filter:
            qs = qs.filter(exam_session_id=session_filter)
        else:
            active_sid = self.request.session.get('active_session_id')
            if active_sid:
                qs = qs.filter(exam_session_id=active_sid)

        if class_filter:
            qs = qs.filter(exam_class_id=class_filter)
        if exam_filter:
            qs = qs.filter(id=exam_filter)
        if search:
            qs = qs.filter(
                Q(exam_name__icontains=search) |
                Q(exam_session__ses_name__icontains=search) |
                Q(exam_class__pro_name__icontains=search) |
                Q(subjects__name__icontains=search)
            ).distinct()
        if start_date:
            qs = qs.filter(exam_start_date__gte=start_date)
        if end_date:
            qs = qs.filter(exam_end_date__lte=end_date)
        return qs

    def get_context_data(self, **kwargs):
        # ListView-এর default pagination/context ব্যবহার করি
        context = super().get_context_data(**kwargs)
        context = TemplateLayout.init(self, context)

        # extra_context এ mode দিলে add হবে
        if self.extra_context:
            context.update(self.extra_context)

        context['classes'] = Programs.objects.filter(pro_status='active').order_by('pro_name')
        context['sessions'] = Session.objects.all().order_by('-id')
        context['all_exams'] = Exam.objects.all().order_by('-id')

        # ফিল্টার ভ্যালু preserve (template এ ব্যবহার করছ)
        req = self.request.GET
        context['search'] = req.get('search', '')
        context['class_filter'] = req.get('class_filter', '')
        context['session_filter'] = req.get('session_filter', '')
        context['start_date'] = req.get('start_date', '')
        context['end_date'] = req.get('end_date', '')

        # ✅ exam_id থাকলে formset attach
        exam_id = req.get('exam_id')
        if exam_id:
            exam = get_object_or_404(Exam, pk=exam_id)
            qs = ExamSubject.objects.filter(exam=exam).select_related('subject')
            context['active_exam'] = exam
            context['formset'] = ExamSubjectFormSet(queryset=qs)

        return context

    # ❌ কাস্টম get() দরকার নেই — ListView নিজেই handle করবে
    # def get(...):  <-- এটা সরিয়ে দিন

    def post(self, request, *args, **kwargs):
        exam_id = request.POST.get('exam_id')
        if not exam_id:
            messages.error(request, "No exam selected.")
            # mode অনুযায়ী redirect name ঠিক করি
            urlname = 'exam_list_marks' if (self.extra_context or {}).get('mode') == 'marks' else 'exam_list'
            return redirect(urlname)

        exam = get_object_or_404(Exam, pk=exam_id)
        qs = ExamSubject.objects.filter(exam=exam).select_related('subject')
        formset = ExamSubjectFormSet(request.POST, queryset=qs)

        if formset.is_valid():
            formset.save()
            messages.success(request, f"✅ Marks setup saved for: {exam.exam_name}")
        else:
            messages.error(request, "❌ Please fix the errors below.")

        # mode preserve করে redirect
        urlname = 'exam_list_marks' if (self.extra_context or {}).get('mode') == 'marks' else 'exam_list'
        # exam_id রেখে দিচ্ছি যাতে save এর পরেও formset ওপেন থাকে
        return redirect(f"{reverse_lazy(urlname)}?exam_id={exam.id}")


# # Then for setting full marks per subject per exam:
# from .models import Exam, ExamSubject

def _to_int_or_none(v):
    if v is None or v == "":
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None

def _set_if_exists(obj, field, value):
    if hasattr(obj, field):
        setattr(obj, field, value)

@method_decorator(role_required(['master_admin', 'admin', 'sub_admin']), name='dispatch')
class ExamSubjectFullMarksView(TemplateView):
    template_name = 'exam/exam_subject_full_marks.html'

    def get_context_data(self, **kwargs):
        exam_id = self.kwargs.get('exam_id')
        exam = get_object_or_404(Exam, id=exam_id)
        exam_subjects = (
            ExamSubject.objects
            .filter(exam=exam)
            .select_related('subject')
            # .order_by('subject__name')
        )
        ctx = super().get_context_data(**kwargs)
        ctx.update({
            'exam': exam,
            'exam_subjects': exam_subjects,
        })
        return TemplateLayout.init(self, ctx)

    def post(self, request, *args, **kwargs):
        exam_id = self.kwargs.get('exam_id')
        exam = get_object_or_404(Exam, id=exam_id)
        exam_subjects = (
            ExamSubject.objects
            .filter(exam=exam)
            .select_related('subject')
        )

        for es in exam_subjects:
            prefix = f"subject_{es.subject.id}"

            # core full/pass
            _set_if_exists(es, 'full_marks', _to_int_or_none(request.POST.get(f'{prefix}_full_marks')) or 0)
            _set_if_exists(es, 'pass_marks', _to_int_or_none(request.POST.get(f'{prefix}_pass_marks')) or 0)

            # component totals (যদি মডেলে থাকে)
            _set_if_exists(es, 'cq_marks',        _to_int_or_none(request.POST.get(f'{prefix}_cq_marks')))
            _set_if_exists(es, 'mcq_marks',       _to_int_or_none(request.POST.get(f'{prefix}_mcq_marks')))
            _set_if_exists(es, 'practical_marks', _to_int_or_none(request.POST.get(f'{prefix}_practical_marks')))
            _set_if_exists(es, 'ct_marks',        _to_int_or_none(request.POST.get(f'{prefix}_ct_marks')))

            # component pass (মডেলে থাকলে)
            _set_if_exists(es, 'cq_pass_marks',        _to_int_or_none(request.POST.get(f'{prefix}_cq_pass_marks')))
            _set_if_exists(es, 'mcq_pass_marks',       _to_int_or_none(request.POST.get(f'{prefix}_mcq_pass_marks')))
            _set_if_exists(es, 'practical_pass_marks', _to_int_or_none(request.POST.get(f'{prefix}_practical_pass_marks')))
            _set_if_exists(es, 'ct_pass_marks',        _to_int_or_none(request.POST.get(f'{prefix}_ct_pass_marks')))

            es.save()

        messages.success(request, "✅ Full marks updated successfully!")
        return redirect('exam_subject_full_marks', exam_id=exam.id)




# from django.views.generic import TemplateView
# from django.shortcuts import get_object_or_404

# from apps.exams.models import Exam, ExamRecord

# def chunked_list(items, size):
#     return [items[i:i + size] for i in range(0, len(items), size)]

# @method_decorator(role_required(['master_admin', 'admin', 'sub_admin']), name='dispatch')
# class ExamSeatPlanView(TemplateView):
#     template_name = "exam/seat_plan.html"

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         exam_id = self.kwargs.get("exam_id")
#         exam = get_object_or_404(Exam, id=exam_id)

#         # GFK বলে select_related("student") করা যাবে না
#         # exam (FK) + student_content_type (FK) নিলে GFK resolve দ্রুত হয়
#         records_qs = (
#             ExamRecord.objects
#             .filter(exam=exam)
#             .select_related("exam", "student_content_type")
#         )

#         # Python-side এ sort (DB join সম্ভব নয় GFK হওয়ার কারণে)
#         records = list(records_qs)

#         def sort_key(rec):
#             stu = rec.student  # GFK resolve
#             # রোল না থাকলে অনেক বড় ভ্যালু দিয়ে পেছনে পাঠাই; int না হলে fallback
#             roll = getattr(stu, "add_class_roll", None)
#             try:
#                 roll_int = int(roll) if roll is not None else 10**9
#             except (TypeError, ValueError):
#                 roll_int = 10**9
#             # দ্বিতীয় কী হিসেবে নাম, যেন রোল same হলে স্টেবল অর্ডার থাকে
#             name = getattr(stu, "add_name", "") or ""
#             return (roll_int, name.lower())

#         records.sort(key=sort_key)

#         context.update({
#             "exam": exam,
#             "pages": chunked_list(records, 12),  # ১২ জন করে একেক পেজ
#         })
#         return context





# student der mark xm er
from django.forms import modelformset_factory

from .models import Exam, Subject, SubjectMark
from .forms import SubjectMarkForm


@method_decorator(role_required(['master_admin', 'admin', 'sub_admin']), name='dispatch')
class MarkEntryView(TemplateView):
    template_name = "exam/marks_entry.html"

    # def _marks_queryset(self, exam, subject):
    #     """
    #     শুধুই সেই SubjectMark যেগুলো signal দিয়ে তৈরী হয়েছে
    #     (মানে: যাদের উপর এই subject প্রযোজ্য).
    #     """
    #     return (
    #         SubjectMark.objects
    #         .filter(subject=subject, exam_record__exam=exam)
    #         .select_related('exam_record__hsc_student')   # HscAdmissions FK ধরে
    #         .order_by('exam_record__hsc_student__add_name')
    #     )
    
    def _marks_queryset(self, exam, subject):
        """
        শুধুই সেই SubjectMark যেগুলো signal দিয়ে তৈরী হয়েছে
        (মানে: যাদের উপর এই subject প্রযোজ্য).
        """
        return (
            SubjectMark.objects
            .filter(subject=subject, exam_record__exam=exam)
            .select_related('exam_record__hsc_student')   
            .order_by('exam_record__hsc_student__add_class_roll', 'exam_record__hsc_student__add_name')
        )


    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))

        exam = get_object_or_404(Exam, id=self.kwargs.get('exam_id'))
        subject = get_object_or_404(Subject, id=self.kwargs.get('subject_id'))

        marks_qs = self._marks_queryset(exam, subject)
        MarkFormSet = modelformset_factory(SubjectMark, form=SubjectMarkForm, extra=0)

        context.update({
            'exam': exam,
            'subject': subject,
            'formset': MarkFormSet(queryset=marks_qs),
        })
        return context

    def post(self, request, *args, **kwargs):
        exam = get_object_or_404(Exam, id=self.kwargs.get('exam_id'))
        subject = get_object_or_404(Subject, id=self.kwargs.get('subject_id'))

        marks_qs = self._marks_queryset(exam, subject)
        MarkFormSet = modelformset_factory(SubjectMark, form=SubjectMarkForm, extra=0)
        formset = MarkFormSet(request.POST, queryset=marks_qs)

        if not formset.is_valid():
            messages.error(request, "There was an error in the submitted marks. Please check again.")
            context = TemplateLayout.init(self, super().get_context_data())
            context.update({
                'exam': exam,
                'subject': subject,
                'formset': formset,
            })
            return self.render_to_response(context)

        # Save with total_mark recompute
        for form in formset.forms:
            instance = form.save(commit=False)
            # যেসব ফিল্ড তোমার SubjectMark‑এ আছে সেগুলোর যোগফল—নেই এমন হলে 0 ধরা
            total = 0
            for part in ('cq_mark', 'mcq_mark', 'practical_mark', 'ct_mark'):
                total += getattr(instance, part, 0) or 0
            instance.total_mark = total
            instance.save()

        messages.success(request, "Marks submitted successfully!")
        return redirect('marks_entry', exam_id=exam.id, subject_id=subject.id)





# # Markshit / Tabulation
# from django.views.generic import ListView, DetailView
# from .models import ExamRecord, SchoolClass, SubjectMark, Exam, Subject

# from django.db.models import Q, OuterRef, Subquery, IntegerField, F


# @method_decorator(role_required(['master_admin', 'admin', 'sub_admin']), name='dispatch')
# class ExamRecordListView(ListView):
#     model = ExamRecord
#     template_name = "exam/exam_record_list.html"
#     context_object_name = "exam_records"
#     paginate_by = 25

#     def get_queryset(self):
#         qs = (
#             super()
#             .get_queryset()
#             .select_related("exam", "exam__exam_class", "student_content_type")  # student নয়, কারণ এটা GFK
#             .order_by('-id')  # initial order; পরে আমরা roll অনুযায়ী ওভাররাইড করবো
#         )

#         search = self.request.GET.get('search')
#         class_filter = self.request.GET.get('class_filter')
#         exam_filter = self.request.GET.get('exam_filter')
#         start_date = self.request.GET.get('start_date')
#         end_date = self.request.GET.get('end_date')

#         if search:
#             qs = qs.filter(
#                 Q(exam__exam_name__icontains=search) |
#                 # নিচের লাইনটা কাজ করবে না যদি GFK—কিন্তু আমরা পরে roll/name annotate করলে চাইলে তা দিয়ে সার্চ করতে পারি
#                 Q(student_name__icontains=search)  # থাকলে; না থাকলে এই লাইনটি বাদ দিন
#             )

#         if class_filter:
#             qs = qs.filter(exam__exam_class_id=class_filter)

#         if exam_filter:
#             qs = qs.filter(exam__id=exam_filter)

#         if start_date:
#             qs = qs.filter(exam__exam_start_date__gte=start_date)

#         if end_date:
#             qs = qs.filter(exam__exam_end_date__lte=end_date)

#         # ---- Core: roll annotate + order ----
#         # কেবল তখনই কাজ করবে যখন student_content_type = Admissions
#         admissions_ct = ContentType.objects.get_for_model(Admissions)

#         # add_class_roll যদি IntegerField হয়:
#         roll_subq = Subquery(
#             Admissions.objects
#             .filter(pk=OuterRef('student_object_id'))
#             .values('add_class_roll')[:1],
#             output_field=IntegerField()  # যদি DB-তে integer হয়
#         )
#         qs = (
#             qs
#             .filter(student_content_type=admissions_ct)
#             .annotate(roll=roll_subq)
#             .order_by(F('roll').asc(nulls_last=True), 'id')
#         )

#         return qs

#     def get_context_data(self, **kwargs):
#         context = TemplateLayout.init(self, super().get_context_data(**kwargs))
#         context['classes'] = SchoolClass.objects.all()
#         context['exams'] = Exam.objects.all()
#         return context




# # New method grade and gpa calculate from model 
# from decimal import Decimal, ROUND_HALF_UP
# from collections import defaultdict

# from django.views.generic import DetailView
# from .models import ExamRecord, GradingScheme
# from decimal import Decimal, ROUND_HALF_UP


# @method_decorator(role_required(['master_admin', 'admin', 'sub_admin']), name='dispatch')
# class MarksheetDetailView(DetailView):
#     model = ExamRecord
#     template_name = "exam/marksheet_detail.html"
#     context_object_name = "record"

#     def get_template_names(self):
#         record = self.get_object()
#         scheme = getattr(record.exam, "grading_scheme", None)
#         nine_ten_schemes = {
#             GradingScheme.NINE_SCIENCE,
#             GradingScheme.NINE_BUSINESS,
#             GradingScheme.NINE_HUMANITIES,
#             GradingScheme.TEN_SCIENCE,
#             GradingScheme.TEN_BUSINESS,
#             GradingScheme.TEN_HUMANITIES,
#         }
#         if scheme in nine_ten_schemes:
#             return ["exam/marksheet_detail_ninescience.html"]
#         return [self.template_name]

#     def get_context_data(self, **kwargs):
#         from collections import defaultdict

#         print(f"[DEBUG] ENTER {self.__class__.__name__}.get_context_data pk={self.kwargs.get('pk')}", flush=True)
#         context = TemplateLayout.init(self, super().get_context_data(**kwargs))

#         record: ExamRecord = self.object
#         student = record.student

#         # ---------- Model-side final calc ----------
#         print("[DEBUG] About to call calculate_total_and_grade()", flush=True)
#         record.calculate_total_and_grade()
#         print("[DEBUG] Returned from calculate_total_and_grade()", flush=True)

#         # ---------- Pull all marks & maps ----------
#         subject_marks = record.subjectmark_set.select_related("subject").all()
#         full_marks_map = record.get_full_marks_map()

#         # ---------- Combine Bangla/English ----------
#         combined_subjects = {
#             "Bangla": ["Bangla 1st Paper", "Bangla 2nd Paper"],
#             "English": ["English 1st Paper", "English 2nd Paper"],
#         }
#         grouped_marks = defaultdict(list)
#         regular_subject_marks = []

#         for mark in subject_marks:
#             mark.full_marks = full_marks_map.get(mark.subject_id, 100)
#             name = (getattr(mark.subject, "name", "") or "").strip()
#             found = False
#             for c_name, paper_names in combined_subjects.items():
#                 if name in paper_names:
#                     grouped_marks[c_name].append(mark)
#                     found = True
#                     break
#             if not found:
#                 regular_subject_marks.append(mark)

#         # ---------- Helpers (display only) ----------
#         def grade_by_percent(p):
#             if p >= 80: return "A+"
#             if p >= 70: return "A"
#             if p >= 60: return "A-"
#             if p >= 50: return "B"
#             if p >= 40: return "C"
#             if p >= 33: return "D"
#             return "F"

#         def gpa_by_grade(g):
#             return {"A+":5.0,"A":4.0,"A-":3.5,"B":3.0,"C":2.0,"D":1.0,"F":0.0}.get(g,0.0)

#         def norm(s):
#             return (s or "").strip().lower()

#         # ---------- Combined totals (Bangla/English) ----------
#         combined_results = []
#         for name, papers in grouped_marks.items():
#             total_ex = sum((p.total_mark or 0) for p in papers)  # EX only
#             full = sum(full_marks_map.get(p.subject.id, 100) for p in papers)
#             pct = (total_ex / full) * 100 if full else 0.0
#             grade = grade_by_percent(pct)
#             gpa = gpa_by_grade(grade)
#             combined_results.append({
#                 "name": name,
#                 "full_marks": full,
#                 "cq": sum(p.cq_mark or 0 for p in papers),
#                 "mcq": sum(p.mcq_mark or 0 for p in papers),
#                 "practical": sum(p.practical_mark or 0 for p in papers),
#                 "total": total_ex,
#                 "gpa": gpa,
#                 "grade": grade,
#             })

#         # ---------- Enrich regular marks (display GP/Grade) ----------
#         for mark in regular_subject_marks:
#             full = full_marks_map.get(mark.subject.id, 100)
#             ex_total = mark.total_mark or 0
#             pct = (ex_total / full) * 100 if full else 0.0
#             mark.grade = grade_by_percent(pct)
#             mark.gpa = gpa_by_grade(mark.grade)
#             mark.full_marks = full

#         # ---------- Optional row (SET FIRST!) ----------
#         detected_optional_name = "-"
#         full_for_optional = "-"
#         cq_optional = "-"
#         mcq_optional = "-"
#         practical_optional = "-"
#         total_optional = "-"
#         opt_grade = "-"
#         opt_gp_calc = "-"

#         opt_label = getattr(record, "optional_subject_label", None)
#         opt_mark = None
#         if opt_label and str(opt_label).startswith("subject_id:"):
#             try:
#                 sid = int(str(opt_label).split(":", 1)[1])
#                 opt_mark = next((m for m in subject_marks if m.subject_id == sid), None)
#             except Exception:
#                 opt_mark = None

#         if not opt_mark and getattr(student, "fourth_subject", None):
#             target = norm(getattr(student.fourth_subject, "sub_name", ""))
#             opt_mark = next((m for m in subject_marks if norm(getattr(m.subject, "name", "")) == target), None)

#         if opt_mark:
#             detected_optional_name = getattr(opt_mark.subject, "name", "-")
#             full_for_optional = full_marks_map.get(opt_mark.subject_id, 100)
#             cq_optional = opt_mark.cq_mark or 0
#             mcq_optional = opt_mark.mcq_mark or 0
#             practical_optional = opt_mark.practical_mark or 0
#             total_optional = opt_mark.total_mark or 0

#             # ---- grade + gp (raw %) ----
#             pct_opt = (float(total_optional) / float(full_for_optional)) * 100 if full_for_optional else 0.0
#             opt_grade = grade_by_percent(pct_opt)
#             opt_gp_calc = gpa_by_grade(opt_grade)

#         # model-এর optional_gp_raw থাকলে সেটাকে দেখাবে; না থাকলে আমরা ক্যাল্ক করা gp দেখাবো
#         opt_gp_final = record.optional_gp_raw if getattr(record, "optional_gp_raw", None) is not None else opt_gp_calc

#         context["optional_row"] = {
#             "name": detected_optional_name,
#             "full_marks": full_for_optional or "-",
#             "cq": cq_optional or "-",
#             "mcq": mcq_optional or "-",
#             "practical": practical_optional or "-",
#             "total": total_optional or "-",
#             "grade": opt_grade or "-",
#             "gp": opt_gp_final if opt_gp_final != "-" else "-",   # eg. 0.0 valid
#         }


#         # ---------- Main row (AFTER optional set) ----------
#         main_detected_name = "-"
#         main_full = "-"
#         main_cq = "-"
#         main_mcq = "-"
#         main_practical = "-"
#         main_total = "-"
#         main_grade = "-"
#         main_gp = "-"

#         main_mark = None
#         try:
#             main_name_target = norm(getattr(getattr(student, "main_subject", None), "sub_name", ""))
#         except Exception:
#             main_name_target = ""

#         if main_name_target:
#             main_mark = next((m for m in subject_marks if norm(getattr(m.subject, "name", "")) == main_name_target), None)

#         if main_mark:
#             main_detected_name = getattr(main_mark.subject, "name", "-")
#             main_full = full_marks_map.get(main_mark.subject_id, 100)
#             main_cq = main_mark.cq_mark or 0
#             main_mcq = main_mark.mcq_mark or 0
#             main_practical = main_mark.practical_mark or 0
#             main_total = main_mark.total_mark or 0

#             pct_main = (float(main_total) / float(main_full)) * 100 if main_full else 0.0
#             main_grade = grade_by_percent(pct_main)
#             main_gp = gpa_by_grade(main_grade)

#         context["main_row"] = {
#             "name": main_detected_name,
#             "full_marks": main_full or "-",
#             "cq": main_cq or "-",
#             "mcq": main_mcq or "-",
#             "practical": main_practical or "-",
#             "total": main_total or "-",
#             "grade": main_grade or "-",
#             "gp": main_gp if main_gp != "-" else "-",   # eg. 0.0 valid
#         }


#         # ---------- Filter regular list for Science (9/10) ----------
#         scheme = getattr(record.exam, "grading_scheme", None)
#         is_science_9_10 = scheme in {GradingScheme.NINE_SCIENCE, GradingScheme.TEN_SCIENCE}

#         if is_science_9_10:
#             FIXED_NAMES = {
#                 # Core & science
#                 "mathematics", "physics", "chemistry",
#                 # BGS variations
#                 "bangladesh and global studies", "bangladesh & global studies", "bgs",
#                 # ICT variations
#                 "ict", "information and communication technology",
#                 # Religion variations (keep broad)
#                 "religion", "islam", "islamic studies", "hinduism", "buddhism", "christian studies",
#             }

#             main_name_norm = norm(context["main_row"]["name"])
#             opt_name_norm = norm(context["optional_row"]["name"])

#             filtered_regular = []
#             for m in regular_subject_marks:
#                 nm = norm(getattr(m.subject, "name", ""))
#                 # skip main & optional (they are separate sections)
#                 if nm and nm in {main_name_norm, opt_name_norm}:
#                     continue
#                 # include only fixed/common
#                 if nm in FIXED_NAMES:
#                     filtered_regular.append(m)

#             regular_subject_marks = filtered_regular

#         # ---------- Final context ----------
#         context.update({
#             "combined_results": combined_results,
#             "bangla_papers": grouped_marks.get("Bangla", []),
#             "english_papers": grouped_marks.get("English", []),
#             "regular_subject_marks": regular_subject_marks,

#             # Final from model
#             "gpa": record.gpa,
#             "grade": record.grade,
#             "remarks": record.remarks,
#             "record": record,
#         })
#         return context

# @method_decorator(role_required(['master_admin', 'admin', 'sub_admin']), name='dispatch')
# class EditMarksView(View):
#     template_name = "marks/edit_marks.html"

#     def get(self, request, pk):
#         record = get_object_or_404(ExamRecord, pk=pk)
#         subject_marks = record.subjectmark_set.select_related("subject").all()
#         full_marks_map = record.get_full_marks_map()
#         exam_subjects = {
#             es.subject_id: es for es in ExamSubject.objects.filter(exam=record.exam)
#         }

#         grand_total = sum(m.total_mark or 0 for m in subject_marks)

#         for mark in subject_marks:
#             es = exam_subjects.get(mark.subject_id)
#             fail_fields = []

#             if es:
#                 if es.cq_pass_marks and (mark.cq_mark or 0) < es.cq_pass_marks:
#                     fail_fields.append("cq")
#                 if es.mcq_pass_marks and (mark.mcq_mark or 0) < es.mcq_pass_marks:
#                     fail_fields.append("mcq")
#                 if es.practical_pass_marks and (mark.practical_mark or 0) < es.practical_pass_marks:
#                     fail_fields.append("practical")
#                 if es.ct_pass_marks and (mark.ct_mark or 0) < es.ct_pass_marks:
#                     fail_fields.append("ct")
#                 if es.pass_marks and (mark.total_mark or 0) < es.pass_marks:
#                     fail_fields.append("total")

#             # Attach directly to mark object for easy use in template
#             mark.fail_fields = fail_fields

#         context = TemplateLayout.init(self, {
#             "record": record,
#             "subject_marks": subject_marks,
#             "grand_total": grand_total,
#         })
#         return render(request, self.template_name, context)

#     def post(self, request, pk):
#         record = get_object_or_404(ExamRecord, pk=pk)
#         subject_marks = record.subjectmark_set.all()

#         for mark in subject_marks:
#             try:
#                 mark.cq_mark = float(request.POST.get(f"cq_{mark.id}", 0) or 0)
#                 mark.mcq_mark = float(request.POST.get(f"mcq_{mark.id}", 0) or 0)
#                 mark.practical_mark = float(request.POST.get(f"practical_{mark.id}", 0) or 0)
#                 mark.ct_mark = float(request.POST.get(f"ct_{mark.id}", 0) or 0)
#             except ValueError:
#                 messages.error(request, "Invalid mark entered.")
#                 continue

#             mark.save()

#         record.calculate_total_and_grade()
#         record.save()

#         messages.success(request, "Marks updated successfully.")
#         return redirect("edit_marks", pk=record.pk)  # Reload same page






# # @method_decorator(role_required(['master_admin', 'admin', 'sub_admin']), name='dispatch')
# def get_grade(total, subject_count):
#     gpa = total / subject_count if subject_count else 0
#     if gpa >= 80:
#         return "A+"
#     elif gpa >= 70:
#         return "A"
#     elif gpa >= 60:
#         return "A-"
#     elif gpa >= 50:
#         return "B"
#     elif gpa >= 40:
#         return "C"
#     elif gpa >= 33:
#         return "D"
#     return "F"

# def save_exam_marks(request, exam_id):
#     exam = get_object_or_404(Exam, pk=exam_id)
#     subjects = exam.subjects.all()
#     exam_records = ExamRecord.objects.filter(exam=exam)

#     if request.method == 'POST':
#         for record in exam_records:
#             for subject in subjects:
#                 sub_mark, created = SubjectMark.objects.get_or_create(
#                     exam_record=record, subject=subject
#                 )

#                 prefix = f"{record.id}_{subject.id}_"
#                 cq = request.POST.get(f'cq_{prefix}')
#                 mcq = request.POST.get(f'mcq_{prefix}')
#                 practical = request.POST.get(f'practical_{prefix}')
#                 ct = request.POST.get(f'ct_{prefix}')

#                 sub_mark.cq_mark = int(cq) if cq else 0
#                 sub_mark.mcq_mark = int(mcq) if mcq else 0
#                 sub_mark.practical_mark = int(practical) if practical else 0
#                 sub_mark.ct_mark = int(ct) if ct else 0
#                 sub_mark.save()

#             # Automatically calculate totals and grade after marks input
#             record.calculate_total_and_grade()

#         messages.success(request, "Marks saved and calculated successfully.")
#         return redirect('exam_record_list')

#     marks_dict = {
#         record.id: {
#             sm.subject_id: sm for sm in SubjectMark.objects.filter(exam_record=record)
#         } for record in exam_records
#     }

#     context = {
#         'exam': exam,
#         'subjects': subjects,
#         'exam_records': exam_records,
#         'marks_dict': marks_dict,
#     }
#     return render(request, 'exam/exam_students_marks.html', context)





# # Tabulation details
# from django.views.generic import TemplateView
# from django.contrib.contenttypes.models import ContentType

# from apps.admissions.models import Admissions, NineAdmissions
# from .models import Exam, ExamRecord, SubjectMark, ExamSubject, GradingScheme  

# @method_decorator(role_required(['master_admin', 'admin', 'sub_admin']), name='dispatch')
# class ExamTabulationView(TemplateView):
#     template_name = "exam/tabulation_sheet.html"  # fallback (optional)

#     def get_template_names(self):
#         exam = get_object_or_404(Exam, pk=self.kwargs.get('exam_id'))
#         scheme = getattr(exam, "grading_scheme", None)

#         nine_ten_schemes = {
#             GradingScheme.NINE_SCIENCE,
#             GradingScheme.NINE_BUSINESS,
#             GradingScheme.NINE_HUMANITIES,
#             GradingScheme.TEN_SCIENCE,
#             GradingScheme.TEN_BUSINESS,
#             GradingScheme.TEN_HUMANITIES,
#         }

#         if scheme == GradingScheme.JUNIOR:
#             return ["exam/tabulation_sheet.html"]      # ✅ 6–8
#         if scheme in nine_ten_schemes:
#             return ["exam/tabulation_sheet_nine_ten.html"]    # ✅ 9/10

#         return [self.template_name]

#     def get_context_data(self, **kwargs):
#         context = TemplateLayout.init(self, super().get_context_data(**kwargs))
#         exam_id = self.kwargs.get('exam_id')
#         exam = get_object_or_404(Exam, pk=exam_id)

#         # GFK কারণে select_related('student') নয়
#         records = ExamRecord.objects.filter(exam=exam).select_related('student_content_type')

#         subjects = exam.subjects.all()
#         exam_subjects = ExamSubject.objects.filter(exam=exam).select_related("subject")
#         full_marks_map = {es.subject_id: es.full_marks for es in exam_subjects}

#         marks = SubjectMark.objects.filter(exam_record__in=records).select_related('subject', 'exam_record')
#         marks_dict = {}
#         for mark in marks:
#             marks_dict.setdefault(mark.exam_record_id, {})[mark.subject_id] = mark.total_mark

#         context.update({
#             'exam': exam,
#             'records': records,
#             'subjects': subjects,
#             'marks_dict': marks_dict,
#             'full_marks_map': full_marks_map,
#         })
#         return context





# # Admit card
# from django.views.generic import TemplateView
# from .models import Exam, ExamRecord

# @method_decorator(role_required(['master_admin', 'admin', 'sub_admin']), name='dispatch')
# class AdmitCardFrontView(TemplateView):
#     template_name = "exam/admit_card_front.html"  # default: class 6–8

#     def get_template_names(self):
#         exam = get_object_or_404(Exam, id=self.kwargs.get("exam_id"))
#         cls = (exam.exam_class.name or "").strip().lower()
#         is_68 = any(k in cls for k in ["6","six","7","seven","8","eight"])
#         return ["exam/admit_card_front.html"] if is_68 else ["exam/admit_card_front_nine.html"]

#     def get_context_data(self, **kwargs):
#         from types import SimpleNamespace

#         context = super().get_context_data(**kwargs)
#         exam_id = self.kwargs.get("exam_id")
#         exam = get_object_or_404(Exam, id=exam_id)

#         # সব রেকর্ড
#         students = (
#             ExamRecord.objects
#             .filter(exam=exam)
#             .select_related("exam", "student_content_type")
#             .order_by("id")
#         )

#         # সব সাবজেক্ট (অর্ডার গুরুত্বপূর্ণ)
#         exam_subjects = (
#             ExamSubject.objects
#             .filter(exam=exam)
#             .select_related("subject")
#             .order_by("id")
#         )
#         subjects = [es.subject for es in exam_subjects]

#         # এই পেজটা 6–8 নাকি 9/10?
#         cls = (exam.exam_class.name or "").strip().lower()
#         is_68 = any(k in cls for k in ["6","six","7","seven","8","eight"])

#         # ————— Helpers —————
#         def norm(s):
#             return (s or "").strip().lower()

#         # ৯/১০ সায়েন্স/কমন ফিক্সড নামগুলো (লোয়ারকেস ভ্যারিয়েন্টসহ)
#         FIXED_NAMES = {
#             # Bangla & English (1st/2nd as separate rows in admit card)
#             "bangla 1st paper", "bangla 2nd paper",
#             "english 1st paper", "english 2nd paper",
#             # Core/common
#             "mathematics",
#             "bangladesh and global studies", "bangladesh & global studies", "bgs",
#             "ict", "information and communication technology",
#             "religion", "islam", "islamic studies", "hinduism", "buddhism", "christian studies",
#             # Science cores
#             "physics", "chemistry",
#         }

#         # padding এর জন্য হালকা dict
#         def blank_row():
#             return {"code": "", "name": ""}

#         # ————— Build per-student subject table —————
#         for rec in students:
#             if is_68:
#                 # আগের মতো dynamic split (per-record attach)
#                 half = (len(subjects) + 1) // 2
#                 left_subjects = subjects[:half]
#                 right_subjects = subjects[half:]
#             else:
#                 # 9/10: Fixed + Main + Fourth (unique, in exam order)
#                 sel = []

#                 # map: normalized name -> subject object(s) keeping order
#                 # (একই নামে ডুপ্লিকেট সাবজেক্ট সাধারণত নেই; থাকলে প্রথমটাই নেবে)
#                 for s in subjects:
#                     nm = norm(getattr(s, "name", ""))
#                     if nm in FIXED_NAMES:
#                         sel.append(s)

#                 # main / fourth detect from admission
#                 try:
#                     main_name = norm(getattr(getattr(rec.student, "main_subject", None), "sub_name", ""))
#                 except Exception:
#                     main_name = ""
#                 try:
#                     fourth_name = norm(getattr(getattr(rec.student, "fourth_subject", None), "sub_name", ""))
#                 except Exception:
#                     fourth_name = ""

#                 def find_by_name(name_norm):
#                     if not name_norm:
#                         return None
#                     for s in subjects:
#                         if norm(getattr(s, "name", "")) == name_norm:
#                             return s
#                     return None

#                 main_subj = find_by_name(main_name)
#                 fourth_subj = find_by_name(fourth_name)

#                 # de-duplicate while preserving order
#                 def add_unique(item_list, s):
#                     if not s:
#                         return
#                     for x in item_list:
#                         if getattr(x, "id", None) == getattr(s, "id", None):
#                             return
#                     item_list.append(s)

#                 add_unique(sel, main_subj)
#                 add_unique(sel, fourth_subj)

#                 # normalize to exactly 12 rows
#                 sel = sel[:12]
#                 if len(sel) < 12:
#                     sel = sel + [blank_row() for _ in range(12 - len(sel))]

#                 left_subjects = sel[:6]
#                 right_subjects = sel[6:12]

#             # টেমপ্লেটে সরাসরি rec.left_subjects/right_subjects ব্যবহার করবো
#             rec.left_subjects = left_subjects
#             rec.right_subjects = right_subjects

#         context.update({
#             "exam": exam,
#             "students": students,
#         })
#         return TemplateLayout.init(self, context)





# @method_decorator(role_required(['master_admin', 'admin', 'sub_admin']), name='dispatch')
# class AdmitCardBackView(TemplateView):
#     template_name = "exam/admit_card_back.html"

#     def get_context_data(self, **kwargs):
#         ctx = TemplateLayout.init(self, super().get_context_data(**kwargs))
#         exam_id = self.kwargs.get("exam_id")
#         exam = get_object_or_404(Exam, id=exam_id)
#         ctx.update({
#             "exam": exam,
#         })
#         return ctx




# from .models import AdmitBack
# from .forms import AdmitBackForm

# class AdmitBackView(TemplateView):
#     template_name = 'exam/admit_back.html'

#     def get_context_data(self, **kwargs):
#         context = TemplateLayout.init(self, super().get_context_data(**kwargs))
#         admit_back, _ = AdmitBack.objects.get_or_create(pk=1)
#         context['form'] = AdmitBackForm(instance=admit_back)
#         return context

#     def post(self, request, *args, **kwargs):
#         admit_back, _ = AdmitBack.objects.get_or_create(pk=1)
#         form = AdmitBackForm(request.POST, request.FILES, instance=admit_back)
#         if form.is_valid():
#             form.save()
#             messages.success(request, "অ্যাডমিট ব্যাক কনটেন্ট সফলভাবে সংরক্ষণ করা হয়েছে।")
#         else:
#             messages.error(request, "ফর্মটি সঠিকভাবে পূরণ করুন।")
#         return redirect('admit_back_page')  # নিচের urls.py-তে এই নামটাই ব্যবহার করেছি



# from django.db.models import Q
# from django.contrib.contenttypes.models import ContentType

# from apps.admissions.models import Admissions, NineAdmissions
# from .models import Exam, ExamRecord, SubjectMark, ExamSubject

# from collections import defaultdict



# def _is_junior(class_name: str) -> bool:
#     cn = (class_name or "").strip().lower()
#     return any(t in cn for t in ["6", "six", "7", "seven", "8", "eight"])


# def _is_senior(class_name: str) -> bool:
#     cn = (class_name or "").strip().lower()
#     return any(t in cn for t in ["9", "nine", "10", "ten"])


# @admin_role_required
# def all_marksheets_view(request, exam_id=None):
#     # ✅ local import to avoid shadowing and UnboundLocalError
#     from collections import defaultdict as _dd

#     # GFK বলে 'student' select_related করা যাবে না
#     records_qs = ExamRecord.objects.select_related('student_content_type', 'exam', 'exam__exam_class')

#     # exam_id resolve (query param থেকেও আসতে পারে)
#     if exam_id is None:
#         exam_filter = (request.GET.get('exam_filter') or "").strip()
#         if exam_filter.isdigit():
#             exam_id = int(exam_filter)

#     if exam_id:
#         records_qs = records_qs.filter(exam_id=exam_id)

#     # Filters
#     search = (request.GET.get('search') or '').strip()
#     class_filter = (request.GET.get('class_filter') or '').strip()
#     start_date = (request.GET.get('start_date') or '').strip()
#     end_date = (request.GET.get('end_date') or '').strip()

#     if search:
#         records_qs = records_qs.filter(Q(exam__exam_name__icontains=search))
#     if class_filter:
#         records_qs = records_qs.filter(exam__exam_class_id=class_filter)
#     if start_date:
#         records_qs = records_qs.filter(exam__exam_start_date__gte=start_date)
#     if end_date:
#         records_qs = records_qs.filter(exam__exam_end_date__lte=end_date)

#     # Pull records
#     records = list(records_qs.order_by('exam_id', 'id'))

#     # খালি হলে সরাসরি টেমপ্লেট দেখাও (class অনুযায়ী best-guess)
#     if not records:
#         template_name = "marks/all_marksheet_print_junior.html"
#         exam = get_object_or_404(Exam, pk=exam_id) if exam_id else None
#         if exam and _is_senior(exam.exam_class.name):
#             template_name = "marks/all_marksheet_print_senior.html"
#         return render(request, template_name, {
#             "all_data": [],
#             "exam": exam,
#             "subjects": [],
#             "full_marks_map": {},
#             "is_exam_wise": bool(exam_id),
#         })

#     # ---- Bulk fetch students (Admissions / NineAdmissions) ----
#     ct_adm = ContentType.objects.get_for_model(Admissions)
#     ct_nine = ContentType.objects.get_for_model(NineAdmissions)
#     adm_ids  = [r.student_object_id for r in records if r.student_content_type_id == ct_adm.id]
#     nine_ids = [r.student_object_id for r in records if r.student_content_type_id == ct_nine.id]

#     adm_map  = {s.id: s for s in Admissions.objects.filter(id__in=adm_ids).only(
#         'id', 'add_name', 'add_class_roll', 'add_class_section', 'add_father', 'add_mother', 'add_religion'
#     )}
#     nine_map = {s.id: s for s in NineAdmissions.objects.filter(id__in=nine_ids).only(
#         'id', 'add_name', 'add_class_roll', 'add_class_section', 'add_father', 'add_mother', 'add_religion'
#     )}

#     for r in records:
#         if r.student_content_type_id == ct_adm.id:
#             r.student_ref = adm_map.get(r.student_object_id)
#         elif r.student_content_type_id == ct_nine.id:
#             r.student_ref = nine_map.get(r.student_object_id)
#         else:
#             r.student_ref = None

#     # ---- Subjects & full marks map ----
#     exam_ids = sorted({r.exam_id for r in records})
#     es_qs = ExamSubject.objects.filter(exam_id__in=exam_ids).select_related("subject")

#     if len(exam_ids) == 1:
#         exam = get_object_or_404(Exam, pk=exam_ids[0])
#         subjects = list(exam.subjects.all())
#         # single exam: {subject_id: full}
#         full_marks_map = {es.subject_id: es.full_marks for es in es_qs}
#     else:
#         exam = None
#         subjects = []
#         # multi-exam: {exam_id: {subject_id: full}}
#         tmp = _dd(dict)
#         for es in es_qs:
#             tmp[es.exam_id][es.subject_id] = es.full_marks
#         full_marks_map = dict(tmp)

#     # ---- All SubjectMark once, then bucket by record ----
#     marks_qs = SubjectMark.objects.filter(exam_record__in=records).select_related('subject', 'exam_record')
#     marks_by_record = _dd(list)
#     for m in marks_qs:
#         marks_by_record[m.exam_record_id].append(m)

#     # ---- Helpers for GPA/Grade (combined rows) ----
#     def grade_by_percent(p):
#         if p >= 80: return "A+"
#         if p >= 70: return "A"
#         if p >= 60: return "A-"
#         if p >= 50: return "B"
#         if p >= 40: return "C"
#         if p >= 33: return "D"
#         return "F"

#     def gpa_by_grade(g):
#         return {"A+":5.0,"A":4.0,"A-":3.5,"B":3.0,"C":2.0,"D":1.0,"F":0.0}.get(g,0.0)

#     # ---- Build all_data and attach full_marks to each mark ----
#     all_data = []
#     single_exam = (len(exam_ids) == 1)

#     for r in records:
#         r.calculate_total_and_grade()
#         subject_marks = marks_by_record.get(r.id, [])

#         # attach full marks to each SubjectMark
#         if single_exam:
#             for m in subject_marks:
#                 m.full_marks = full_marks_map.get(m.subject_id, 100)
#         else:
#             for m in subject_marks:
#                 m.full_marks = full_marks_map.get(r.exam_id, {}).get(m.subject_id, 100)

#         # ---- build combined sets for Bangla/English (batch view) ----
#         grouped = _dd(list)
#         regular_subject_marks = []
#         for m in subject_marks:
#             name = (getattr(m.subject, "name", "") or "").strip()
#             if name in ("Bangla 1st Paper", "Bangla 2nd Paper"):
#                 grouped["Bangla"].append(m)
#             elif name in ("English 1st Paper", "English 2nd Paper"):
#                 grouped["English"].append(m)
#             else:
#                 regular_subject_marks.append(m)

#         # combined rows with GPA/Grade/Total
#         combined_results = []
#         for cname, papers in grouped.items():
#             full = sum((p.full_marks or 0) for p in papers)
#             cq   = sum((p.cq_mark or 0) for p in papers)
#             mcq  = sum((p.mcq_mark or 0) for p in papers)
#             prac = sum((p.practical_mark or 0) for p in papers)
#             ct   = sum((p.ct_mark or 0) for p in papers)
#             total_ex = sum((p.total_mark or 0) for p in papers)  # CQ+MCQ+Practical

#             percent_raw = (total_ex / full) * 100 if full else 0.0
#             grade = grade_by_percent(percent_raw)
#             gp = gpa_by_grade(grade)

#             combined_results.append({
#                 "name": cname,
#                 "full_marks": full,
#                 "cq": cq,
#                 "mcq": mcq,
#                 "practical": prac,
#                 "ct": ct,
#                 "total": total_ex,
#                 "grade": grade,
#                 "gpa": gp,
#             })

#         # enrich regular subjects (optional)
#         for m in regular_subject_marks:
#             full = m.full_marks or 100
#             t    = m.total_mark or 0
#             pct  = (t / full * 100) if full else 0.0
#             m.grade = grade_by_percent(pct)
#             m.gpa   = gpa_by_grade(m.grade)

#         all_data.append({
#             "record": r,
#             "student": r.student_ref,
#             "subject_marks": subject_marks,
#             "gpa": r.gpa,
#             # 👉 template needs these to print combined totals:
#             "combined_results": combined_results,
#             "bangla_papers": grouped.get("Bangla", []),
#             "english_papers": grouped.get("English", []),
#             "regular_subject_marks": regular_subject_marks,
#         })

#     # ---- Pick template (6–8 vs 9–10) ----
#     if single_exam:
#         cls_name = (exam.exam_class.name or "")
#         if _is_junior(cls_name):
#             template_name = "marks/all_marksheet_print_junior.html"
#         elif _is_senior(cls_name):
#             template_name = "marks/all_marksheet_print_senior.html"
#         else:
#             template_name = "marks/all_marksheet_print_mixed.html"
#     else:
#         has_j = any(_is_junior(r.exam.exam_class.name) for r in records)
#         has_s = any(_is_senior(r.exam.exam_class.name) for r in records)
#         if has_j and not has_s:
#             template_name = "marks/all_marksheet_print_junior.html"
#         elif has_s and not has_j:
#             template_name = "marks/all_marksheet_print_senior.html"
#         else:
#             template_name = "marks/all_marksheet_print_mixed.html"

#     ctx = {
#         "all_data": all_data,
#         "exam": exam,
#         "subjects": subjects,
#         "full_marks_map": full_marks_map,
#         "is_exam_wise": single_exam,
#     }
#     return render(request, template_name, ctx)





# Seatplan

from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.db.models import Q
from apps.admissions.models import Subjects, HscAdmissions, Session

@method_decorator(role_required(['master_admin','admin','sub_admin','teacher']), name='dispatch')
class SeatplanSubjectListView(TemplateView):
    template_name = "seatplan/subject_list.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        ctx = TemplateLayout.init(self, ctx)
        ctx["layout"] = "vertical"
        ctx["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", ctx)

        # Active session (if you’re already storing it in session like your other view)
        active_session_id = self.request.session.get("active_session_id")
        active_session = None
        if active_session_id:
            try:
                active_session = Session.objects.get(id=active_session_id)
            except Session.DoesNotExist:
                active_session = None

        # Fetch active subjects (ordered by group then name)
        subjects = Subjects.objects.filter(sub_status="active").order_by("group", "sub_name")

        # (Optional & lightweight) Precompute a simple student presence flag per subject in current session
        # We’re NOT doing heavy counts here to keep Step 1 simple.
        # You can show counts later if you want.
        ctx.update({
            "subjects": subjects,
            "active_session": active_session,
        })
        return ctx

from django.urls import reverse

@method_decorator(role_required(['master_admin','admin','sub_admin','teacher']), name='dispatch')
class SeatplanStudentsView(TemplateView):
    template_name = "seatplan/students_select.html"

    def _subject_qs(self, subject):
        return (
            Q(subjects=subject) | Q(main_subject=subject) | Q(fourth_subject=subject)
            | Q(optional_subject=subject) | Q(optional_subject_2=subject)
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # ---- Vuexy layout ----
        ctx = TemplateLayout.init(self, ctx)
        ctx["layout"] = "vertical"
        ctx["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", ctx)

        # ---- Active session (REQUIRED) ----
        active_session_id = self.request.session.get("active_session_id")
        active_session = Session.objects.filter(id=active_session_id).first() if active_session_id else None
        if not active_session:
            messages.warning(self.request, "Please select a session from the navbar to continue.")
            ctx.update({"subject": None, "students": HscAdmissions.objects.none(), "active_session": None})
            return ctx

        # ---- Subject filter ----
        subject_id = self.request.GET.get("subject")
        subject = Subjects.objects.filter(id=subject_id, sub_status="active").first() if subject_id else None

        students = HscAdmissions.objects.none()
        if subject:
            qs = (
                HscAdmissions.objects
                .filter(self._subject_qs(subject), add_session_id=active_session.id)  # ← match selected session
                .only("id","add_name","add_class_roll","add_admission_group","add_class_id","add_session")
                .distinct()
                .order_by("add_class_roll","add_admission_group","add_name")
            )
            students = qs

        ctx.update({
            "subject": subject,
            "students": students,
            "active_session": active_session,
        })
        return ctx

    

    def post(self, request, *args, **kwargs):
        active_session_id = request.session.get("active_session_id")
        if not active_session_id:
            messages.error(request, "Please select a session before proceeding.")
            return redirect(request.META.get("HTTP_REFERER", "seatplan_subjects"))

        selected_ids = request.POST.getlist("student_ids")
        subject_id = request.POST.get("subject_id")
        mode = request.POST.get("mode") or "seatplan"   # <-- which button was clicked

        request.session["seatplan_selected_ids"] = selected_ids
        request.session["seatplan_subject_id"] = subject_id
        request.session.modified = True

        # Redirect to the appropriate preview URL (GET)
        if mode == "attendance":
            return redirect(reverse("seatplan_preview_mode", kwargs={"mode": "attendance"}))
        else:
            # either specific seatplan mode or the generic preview
            return redirect(reverse("seatplan_preview_mode", kwargs={"mode": "seatplan"}))
            # or: return redirect("seatplan_preview")



# pdf
from django.http import HttpResponse, HttpResponseBadRequest
from django.template.loader import render_to_string
from django.views import View
from django.views.generic import TemplateView
from django.db.models import Q

@method_decorator(role_required(['master_admin','admin','sub_admin','teacher']), name='dispatch')
class SeatplanPreviewView(TemplateView):
    template_name = "seatplan/preview.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # Vuexy layout
        ctx = TemplateLayout.init(self, ctx)
        ctx["layout"] = "vertical"
        ctx["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", ctx)

        # Mode ধরো (default = normal)
        mode = kwargs.get("mode", "normal")
        ctx["mode"] = mode

        ids = self.request.session.get("seatplan_selected_ids", [])
        subject_id = self.request.session.get("seatplan_subject_id")

        subject = Subjects.objects.filter(id=subject_id).first() if subject_id else None
        active_session_id = self.request.session.get("active_session_id")
        active_session = Session.objects.filter(id=active_session_id).first() if active_session_id else None

        students = (
            HscAdmissions.objects
            .filter(id__in=ids, add_session_id=active_session.id if active_session else None)
            .order_by("add_class_roll","add_admission_group","add_name")
        )

        ctx.update({
            "subject": subject,
            "active_session": active_session,
            "students": students,
        })

        # mode অনুযায়ী template আলাদা করতে চাইলে
        if mode == "attendance":
            self.template_name = "seatplan/preview.html"
        elif mode == "seatplan":
            self.template_name = "seatplan/preview_seatplan.html"

        return ctx
