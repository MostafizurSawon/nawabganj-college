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
