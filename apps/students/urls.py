from django.urls import path
from . import views

urlpatterns = [
    path('admitted-students/hsc', views.AdmittedStudentListView.as_view(), name='admitted_students_list'),
    path('admitted-students/<int:pk>/view/', views.HscAdmissionDetailView2.as_view(), name='hsc_admission_view'),
    # path('admitted-students/<int:pk>/view/', views.HscAdmissionDetailView.as_view(), name='hsc_admission_view'),

    # 👇 Update and delete
    path('admitted-students/<int:pk>/edit/', views.HscAdmissionUpdateView.as_view(), name='hsc_admission_update'),
    path('admitted-students/<int:pk>/delete/', views.HscAdmissionDeleteView.as_view(), name='hsc_admission_delete'),

    # Arts Update and delete
    path('admitted-students/<int:pk>/edit/arts/', views.HscAdmissionUpdateArtsView.as_view(), name='hsc_admission_update_arts'),

    # Degree Admitted Students
    path('admitted-students/degree/', views.DegreeAdmittedStudentListView.as_view(), name='degree_admitted_students_list'),
    path('admitted-students/degree/<int:pk>/view/', views.DegreeAdmissionDetailView.as_view(), name='degree_admission_view'),

    # Ba update and delete
    path('admitted-students/degree/<int:pk>/edit/ba/', views.BaAdmissionUpdateView.as_view(), name='ba_admission_edit'),
    path('degree-admission/delete/<int:pk>/', views.BaAdmissionDeleteView.as_view(), name='degree_admission_delete'),




    # bulk pdf admission form
    path("admissions/export/pdf/", views.admission_pdf_preview, name="generate_admission_pdfs"),


]
