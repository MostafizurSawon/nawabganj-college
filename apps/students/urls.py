from django.urls import path
from . import views

urlpatterns = [
    path('admitted-students/hsc', views.AdmittedStudentListView.as_view(), name='admitted_students_list'),
    path('admitted-students/<int:pk>/view/', views.HscAdmissionDetailView2.as_view(), name='hsc_admission_view'),
    # path('admitted-students/<int:pk>/view/', views.HscAdmissionDetailView.as_view(), name='hsc_admission_view'),

    # payment confirmation
    # path(
    #     "admitted-students-hsc/<int:pk>/payment/",
    #     views.HscPaymentReviewUpdateView.as_view(),
    #     name="hsc_payment_review",
    # ),

    # update mosal
    path(
        "admitted-students/<int:pk>/payment/update/",
        views.update_admission_payment,
        name="hsc_payment_update",
    ),

    # degree payment modal
    path(
        "admitted-students/degree/<int:pk>/payment/update/",
        views.update_degree_admission_payment,
        name="degree_payment_update",
    ),

    # 👇 Update and delete
    path('admitted-students/<int:pk>/edit/', views.HscAdmissionUpdateView.as_view(), name='hsc_admission_update'),
    path('admitted-students-business/<int:pk>/edit/', views.HscAdmissionUpdateCommerceView.as_view(), name='hsc_admission_update_business'),
    path('admitted-students/<int:pk>/delete/', views.HscAdmissionDeleteView.as_view(), name='hsc_admission_delete'),

    # Arts Update and delete
    path('admitted-students/<int:pk>/edit/arts/', views.HscAdmissionUpdateArtsView.as_view(), name='hsc_admission_update_arts'),

    # hsc invoice
    path("student/<int:pk>/invoice/", views.admission_invoice_view, name="hsc_admission_invoice"),

    # স্টুডেন্ট (নিজের ইনভয়েস)
    path("student/<int:pk>/my-invoice/", views.student_admission_invoice_view, name="student_invoice"),

    # ---------- Degree Invoice URLs ----------

    # Staff/Admin: যেকোনো Degree ছাত্রের ইনভয়েস দেখতে পারবে (paid হলে)
    path("degree/<int:pk>/invoice/", views.degree_admission_invoice_view, name="degree_admission_invoice"),

    # Student: শুধু নিজের Degree ইনভয়েস দেখতে পারবে (paid হলে)
    path("degree/<int:pk>/my-invoice/", views.student_degree_admission_invoice_view, name="degree_student_invoice"),


    # Degree Admitted Students
    path('admitted-students/degree/', views.DegreeAdmittedStudentListView.as_view(), name='degree_admitted_students_list'),
    path('admitted-students/degree/<int:pk>/view/', views.DegreeAdmissionDetailView.as_view(), name='degree_admission_view'),

    # Edit (group-wise রাখুন আগের মতো)
    path('admitted-students/degree/<int:pk>/edit/ba/',  views.BaAdmissionUpdateView.as_view(),  name='ba_admission_edit'),
    path('admitted-students/degree/<int:pk>/edit/bss/', views.BssAdmissionUpdateView.as_view(), name='bss_admission_edit'),
    path('admitted-students/degree/<int:pk>/edit/bsc/', views.BscAdmissionUpdateView.as_view(), name='bsc_admission_edit'),
    path('admitted-students/degree/<int:pk>/edit/bbs/', views.BbsAdmissionUpdateView.as_view(), name='bbs_admission_edit'),

    # ✅ Delete (একটাই রুট, গ্রুপ প্যারাম সহ)
    path(
        'degree-admission/<str:group>/delete/<int:pk>/',
        views.DegreeAdmissionDeleteView.as_view(),
        name='degree_admission_delete'
    ),




    # bulk pdf admission form
    path("admissions/export/pdf/", views.admission_pdf_preview, name="generate_admission_pdfs"),


]
