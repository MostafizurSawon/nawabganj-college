from django.urls import path
from . import views

urlpatterns = [
    path('admitted-students/', views.AdmittedStudentListView.as_view(), name='admitted_students_list'),
    path('admitted-students/<int:pk>/view/', views.HscAdmissionDetailView.as_view(), name='hsc_admission_view'),

    # 👇 Update and delete
    path('admitted-students/<int:pk>/edit/', views.HscAdmissionUpdateView.as_view(), name='hsc_admission_update'),
    path('admitted-students/<int:pk>/delete/', views.HscAdmissionDeleteView.as_view(), name='hsc_admission_delete'),
]
