from web_project.views import SystemView
from django.urls import path
from .views import HscAdmissionCreateView, get_admission_fee, FeeListView, FeeUpdateView, FeeDeleteView, HscAdmissionCreateCommerceView,HscAdmissionCreateArtsView, FeeCreateView
from . import views

urlpatterns = [
    #Admission Fee Api
    path('api/fee/admission/', get_admission_fee, name='get_admission_fee'),

    # Degree Api
    path('api/fee/degree/', views.get_degree_admission_fee, name='get_degree_admission_fee'),


    path('fees/', FeeListView.as_view(), name='fee_list'),
    path('fees/create/', FeeCreateView.as_view(), name='fee_create'),
    # path('fees/<int:pk>/update/', FeeUpdateView.as_view(), name='fee_update'),
    path('fees/<int:pk>/update/', views.fee_update, name='fee_update'),
    path('fees/<int:pk>/delete/', FeeDeleteView.as_view(), name='fee_delete'),

    # Hsc Apply
    path('apply/science/', HscAdmissionCreateView.as_view(), name='hsc_admission_create'),
    path('apply/commerce/', HscAdmissionCreateCommerceView.as_view(), name='hsc_admission_create_commerce'),
    path('apply/arts/', HscAdmissionCreateArtsView.as_view(), name='hsc_admission_create_arts'),

    # Degree Apply
    path('apply/ba/', views.AdmissionBaCreateView.as_view(), name='ba_admission_create'),
    path('apply/bss/', views.AdmissionBssCreateView.as_view(), name='bss_admission_create'),
    path('apply/bsc/', views.AdmissionBscCreateView.as_view(), name='bsc_admission_create'),
    path('apply/bbs/', views.AdmissionBbsCreateView.as_view(), name='bbs_admission_create'),


    # Global filter by session
    path('set-session/', views.set_session_view, name='set_session'),


    # subject wise student data
    path("subjects/students/", views.SubjectWiseStudentsView.as_view(), name="subject_wise_students"),

    path("subjects/pdf/", views.SubjectStudentsPDFView.as_view(), name="subject_students_pdf"),

    # Tabulation (static PDF design)
    path("tabulation", views.TabulationSheetPDFView.as_view(), name="tabulation_pdf"),

]

handler404 = SystemView.as_view(template_name="pages_misc_error.html", status=404)
handler403 = SystemView.as_view(template_name="pages_misc_not_authorized.html", status=403)
handler400 = SystemView.as_view(template_name="pages_misc_error.html", status=400)
handler500 = SystemView.as_view(template_name="pages_misc_error.html", status=500)
