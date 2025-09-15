from django.urls import path
from .views import SampleView
from django.contrib.auth.views import LogoutView
from django.contrib.auth.decorators import login_required
from . import views

urlpatterns = [
    # path("dashboard/", login_required(views.dashboard, name="index"),
    # path("dashboard/", views.dashboard, name="index"),
    path("dashboard/", login_required(SampleView.as_view()), name="index"),
    # path("dashboard/", login_required(SampleView.as_view(template_name="index.html")), name="index"),

    path("page_2/", SampleView.as_view(template_name="page_2.html"), name="page-2"),
    path(
        "dashboard/my-admission-form/",
        login_required(SampleView.as_view(extra_context={"mode": "list"})),
        name="my_form",
    ),
    path(
        "dashboard/my-payment/",
        login_required(SampleView.as_view(extra_context={"mode": "sp"})),
        name="student_admission_pdf",
    ),

]
