from django.urls import path
from django.contrib.auth.decorators import login_required
from .views import TableView

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

]
