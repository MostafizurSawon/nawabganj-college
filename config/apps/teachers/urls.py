from django.urls import path
from django.contrib.auth.decorators import login_required
from .views import TableView

urlpatterns = [
    path(
        "teachers/",
        login_required(TableView.as_view(template_name="t1.html")),
        name="te1",
    ),
    path(
        "d1/",
        login_required(TableView.as_view(template_name="t1.html")),
        name="p1",
    ),
    path(
        "d2/",
        login_required(TableView.as_view(template_name="t1.html")),
        name="p2",
    ),
    path(
        "d3/",
        login_required(TableView.as_view(template_name="t1.html")),
        name="p3",
    ),
    path(
        "d4/",
        login_required(TableView.as_view(template_name="t1.html")),
        name="p4",
    ),

]
