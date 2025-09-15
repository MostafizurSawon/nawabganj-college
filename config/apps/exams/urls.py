from django.urls import path
from django.contrib.auth.decorators import login_required
from .views import TableView
from . import views

urlpatterns = [
    path(
        "exam/",
        login_required(TableView.as_view(template_name="ex1.html")),
        name="exam1",
    ),
    path(
        "exam/",
        login_required(TableView.as_view(template_name="ex1.html")),
        name="exam2",
    ),
    path(
        "exam/",
        login_required(TableView.as_view(template_name="ex1.html")),
        name="exam3",
    ),
    path(
        "exam/",
        login_required(TableView.as_view(template_name="ex1.html")),
        name="exam4",
    ),
    path(
        "exam/",
        login_required(TableView.as_view(template_name="ex1.html")),
        name="exam5",
    ),
    path(
        "exam/",
        login_required(TableView.as_view(template_name="ex1.html")),
        name="exam6",
    ),
    path(
        "exam/",
        login_required(TableView.as_view(template_name="ex1.html")),
        name="exam7",
    ),
    path(
        "exam/",
        login_required(TableView.as_view(template_name="ex1.html")),
        name="exam8",
    ),

    path('subjects/', views.SubjectDashboardView.as_view(), name='subject_list'),
    # path('subjects/delete/<int:pk>/', views.DeleteSubjectView.as_view(), name='subject_delete'),

    path('exam/create/', views.ExamCreateView.as_view(), name='exam_create'),
    path('exams/exam/edit/<int:pk>/', views.ExamEditView.as_view(), name='exam_edit'), 
    path('exam/delete/<int:pk>/', views.ExamDeleteView.as_view(), name='exam_delete'),

    path('get-subjects-by-class/<int:class_id>/', views.get_subjects_by_class, name='get_subjects_by_class'),


    # # cbv
    # path('exam/<int:exam_id>/students_marks/', views.ExamStudentsMarksView.as_view(), name='exam_students_marks'),

    path('marks-entry/<int:exam_id>/<int:subject_id>/', views.MarkEntryView.as_view(), name='marks_entry'),



    # # sob mark dea 
    path('exams/', views.ExamListView.as_view(), name='exam_list'),
    path('exam-list/marks/', views.ExamListView.as_view(extra_context={'mode': 'marks'}), name='exam_list_marks'),
    # path('exam-list/tabulation/', views.ExamListView.as_view(extra_context={'mode': 'tabulation'}), name='tabulation_list'),
    # path('exam-list/admit-front/', views.ExamListView.as_view(extra_context={'mode': 'sadmit_front'}), name='admit_front'),
    # path('exam-list/admit-back/', views.ExamListView.as_view(extra_context={'mode': 'sadmit_back'}), name='admit_back'),
    # # seatplan
    # path('exam-list/seatplan/', views.ExamListView.as_view(extra_context={'mode': 'seatplan'}), name='seatplan'),

    # path("exam/<int:exam_id>/seatplan/", views.ExamSeatPlanView.as_view(), name="exam_seat_plan"),

    # # Admit card
    # path('exam/<int:exam_id>/admit-front/', views.AdmitCardFrontView.as_view(), name='admit_card_front'),
    # path('exam/<int:exam_id>/admit-back/', views.AdmitCardBackView.as_view(), name='admit_card_back'),

    # # Admit card backside description input
    # path('admit-back/', views.AdmitBackView.as_view(), name='admit_back_page'),

    path('exam/<int:exam_id>/full-marks/', views.ExamSubjectFullMarksView.as_view(), name='exam_subject_full_marks'),

    # # Markshit -> Class 6 - 8
    # path("exam-records/", views.ExamRecordListView.as_view(), name="exam_record_list"),
    # # Marksheet Edit for each student
    # path('exam-record/<int:pk>/edit/', views.EditMarksView.as_view(), name='edit_marks'),
    # path("marksheet/<int:pk>/", views.MarksheetDetailView.as_view(), name="marksheet"),
    # path("exams/marks-entry/<int:exam_id>/", views.save_exam_marks, name="exam_students_marks"),

    # # Tabulation
    # path('exam/<int:exam_id>/tabulation/', views.ExamTabulationView.as_view(), name='exam_tabulation'),


    # # app print marksheet
    # # দুইটা রুটই রাখো: কুইরি-প্যারাম সহ পুরোনোটা + exam-wise নতুনটা
    # path('exam/all-marksheets/', views.all_marksheets_view, name='all_marksheets'),
    # path('exam/<int:exam_id>/all-marksheets/', views.all_marksheets_view, name='all_marksheets_exam'),


]
