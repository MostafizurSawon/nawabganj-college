from web_project.views import SystemView
from django.urls import path
from .views import HscAdmissionCreateView, get_admission_fee, FeeListView, FeeCreateView, FeeUpdateView, FeeDeleteView, HscAdmissionCreateCommerceView,HscAdmissionCreateArtsView

urlpatterns = [
    #Admission Fee Api
    path('api/fee/admission/', get_admission_fee, name='get_admission_fee'),

    path('fees/', FeeListView.as_view(), name='fee_list'),
    path('fees/create/', FeeCreateView.as_view(), name='fee_create'),
    path('fees/<int:pk>/update/', FeeUpdateView.as_view(), name='fee_update'),
    path('fees/<int:pk>/delete/', FeeDeleteView.as_view(), name='fee_delete'),

    path('apply/science/', HscAdmissionCreateView.as_view(), name='hsc_admission_create'),
    path('apply/commerce/', HscAdmissionCreateCommerceView.as_view(), name='hsc_admission_create_commerce'),
    path('apply/arts/', HscAdmissionCreateArtsView.as_view(), name='hsc_admission_create_arts'),

]

handler404 = SystemView.as_view(template_name="pages_misc_error.html", status=404)
handler403 = SystemView.as_view(template_name="pages_misc_not_authorized.html", status=403)
handler400 = SystemView.as_view(template_name="pages_misc_error.html", status=400)
handler500 = SystemView.as_view(template_name="pages_misc_error.html", status=500)
