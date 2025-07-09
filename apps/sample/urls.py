from django.urls import path
from .views import SampleView, login_view
from django.contrib.auth.views import LogoutView
from django.contrib.auth.decorators import login_required

urlpatterns = [
    path("", login_required(SampleView.as_view(template_name="index.html")), name="index"),

    path("page_2/", SampleView.as_view(template_name="page_2.html"), name="page-2"),
    path("login/", login_view, name="login"),
    path("logout/", LogoutView.as_view(next_page="login"), name="logout"),
]
