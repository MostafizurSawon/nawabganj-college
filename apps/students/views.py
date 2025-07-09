from django.views.generic import ListView
from apps.admissions.models import HscAdmissions
from django.db.models import Q
from django.contrib import messages

from web_project import TemplateLayout, TemplateHelper

class AdmittedStudentListView(ListView):
    model = HscAdmissions
    template_name = 'students/admitted_students_list.html'
    context_object_name = 'students'
    paginate_by = 25
    def get_queryset(self):
        queryset = super().get_queryset().select_related('add_session', 'add_program')

        # Filters
        session = self.request.GET.get('session')
        program = self.request.GET.get('program')
        group = self.request.GET.get('group')

        if session:
            queryset = queryset.filter(add_session_id=session)
        if program:
            queryset = queryset.filter(add_program_id=program)
        if group:
            queryset = queryset.filter(add_admission_group=group)

        # Optional: implement keyword search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(add_name__icontains=search) |
                Q(add_father__icontains=search) |
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
        from apps.admissions.models import Session, Programs

        context['sessions'] = Session.objects.all()
        context['programs'] = Programs.objects.all()
        context['groups'] = ['science', 'arts', 'commerce']
        return context



from django.views.generic.detail import DetailView

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

# ✏️ Edit View
class HscAdmissionUpdateView(UpdateView):
    model = HscAdmissions
    template_name = "admissions/admission_form.html"
    form_class = HscAdmissionForm
    context_object_name = "student"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = TemplateLayout.init(self, context)
        context["layout"] = "vertical"
        context["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", context)

        student = self.object  # This is the HscAdmissions instance being edited
        group = student.add_admission_group or "science"



        context["subjects_main"] = Subjects.objects.filter(group=group, sub_status="active", sub_select="main")
        context["subjects_fourth"] = Subjects.objects.filter(group=group, sub_status="active", sub_select="fourth")
        context["subjects_optional"] = Subjects.objects.filter(group=group, sub_status="active", sub_select="optional")
        context["subjects_all"] = Subjects.objects.filter(group=group, sub_status="active", sub_select="all")

        return context


    def form_valid(self, form):
        response = super().form_valid(form)

        # Re-attach all + optional subjects after update
        group = self.object.add_admission_group or "science"

        subjects_all = Subjects.objects.filter(
            group=group,
            sub_status="active",
            sub_select__in=["all", "optional"]
        )
        self.object.subjects.set(subjects_all)

        messages.success(
            self.request,
            f"✅ {self.object.add_name}'s data updated successfully."
        )
        return response



    def get_success_url(self):
        return reverse_lazy('admitted_students_list')



# Arts Update View
from apps.admissions.forms import ArtsAdmissionForm
from apps.admissions.models import Programs

class HscAdmissionUpdateArtsView(UpdateView):
    model = HscAdmissions
    form_class = ArtsAdmissionForm
    template_name = "admissions/admission_form_arts.html"
    success_url = reverse_lazy("admitted_students_list")  # or anywhere you want

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Layout setup
        context = TemplateLayout.init(self, context)
        context["layout"] = "vertical"
        context["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", context)

        # Subjects
        group = "arts"
        status = "active"
        context["subjects_all"] = Subjects.objects.filter(group=group, sub_status=status, sub_select="all")
        context["subjects_optional"] = Subjects.objects.filter(group=group, sub_status=status, sub_select="optional")
        context["subjects_optional2"] = Subjects.objects.filter(group=group, sub_status=status, sub_select="optional2")
        context["subjects_main"] = Subjects.objects.filter(group=group, sub_status=status, sub_select="main")
        context["subjects_fourth"] = Subjects.objects.filter(group=group, sub_status=status, sub_select="fourth")

        context["student"] = self.object  # 👈 for subject pre-fill
        return context

    def form_valid(self, form):
        # Set again
        try:
            hsc_program = Programs.objects.get(pro_name__iexact="hsc")
            form.instance.add_program = hsc_program
            form.instance.add_admission_group = "arts"
        except Programs.DoesNotExist:
            form.add_error(None, "HSC program not found.")
            return self.form_invalid(form)

        # Set subjects
        form.instance.main_subject_id = self.request.POST.get("main_subject")
        form.instance.fourth_subject_id = self.request.POST.get("fourth_subject")
        form.instance.optional_subject_id = self.request.POST.get("optional_subject")
        form.instance.optional_subject_2_id = self.request.POST.get("optional_subject_2")

        self.object = form.save()

        # Set only selected subjects (same logic as create)
        selected_subject_ids = []

        # All (auto)
        all_subjects = Subjects.objects.filter(group="arts", sub_status="active", sub_select="all")
        selected_subject_ids += list(all_subjects.values_list('id', flat=True))

        # Manual selections
        if form.instance.optional_subject_id:
            selected_subject_ids.append(form.instance.optional_subject_id)

        if form.instance.optional_subject_2_id:
            selected_subject_ids.append(form.instance.optional_subject_2_id)

        self.object.subjects.set(selected_subject_ids)

        messages.success(
            self.request,
            f"✅ {self.object.add_name}'s data updated successfully."
        )
        return redirect(self.success_url)

    def form_invalid(self, form):
        print("Form invalid:", form.errors)
        return super().form_invalid(form)








from django.shortcuts import redirect

# 🗑️ Delete View
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


# views.py
# from django.template.loader import render_to_string
# from weasyprint import HTML
# from django.http import HttpResponse

# def generate_admission_pdfs(request):
#     search = request.GET.get("search", "")
#     session = request.GET.get("session")
#     program = request.GET.get("program")
#     group = request.GET.get("group")

#     students = HscAdmissions.objects.all()

#     if search:
#         students = students.filter(
#             Q(add_name__icontains=search) |
#             Q(add_class_roll__icontains=search) |
#             Q(add_mobile__icontains=search)
#         )

#     if session:
#         students = students.filter(add_session_id=session)
#     if program:
#         students = students.filter(add_program_id=program)
#     if group:
#         students = students.filter(add_admission_group=group)

#     # 🔄 HTML render
#     html_string = render_to_string("hsc/admission_pdf_bulk.html", {
#         "students": students
#     })

#     # 📄 Generate PDF
#     pdf_file = HTML(string=html_string).write_pdf()

#     response = HttpResponse(pdf_file, content_type="application/pdf")
#     response["Content-Disposition"] = "inline; filename=admissions.pdf"
#     return response
