from django.views.generic import TemplateView
from web_project import TemplateLayout, TemplateHelper


"""
This file is a view controller for multiple pages as a module.
Here you can override the page view layout.
Refer to sample/urls.py file for more pages.
"""


# class SampleView(TemplateView):
#     # Predefined function
#     def get_context_data(self, **kwargs):
#         # A function to init the global layout. It is defined in web_project/__init__.py file
#         context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        
#         return context

# @method_decorator(login_required, name='dispatch')
# class SampleView(TemplateView):
#     template_name = 'dashboard.html'  # Default template

#     def get_context_data(self, **kwargs):
#         print("SampleView get_context_data called, Role:", getattr(self.request.user, 'role', 'No role defined'))
#         context = TemplateLayout.init(self, super().get_context_data(**kwargs))
#         return context

#     def get_template_names(self):
#         if getattr(self.request.user, 'role', 'No role defined') != 'admin':
#             return ['dashboard_student.html']
#         return ['dashboard.html']



# class SampleView(TemplateView):
#     template_name = 'dashboard.html'

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['user'] = self.request.user  # Explicitly set user
#         print("SampleView get_context_data called, Role:", getattr(self.request.user, 'role', 'No role defined'))
#         context = TemplateLayout.init(self, context)  # Call TemplateLayout.init
#         return context

#     def get_template_names(self):
#         if getattr(self.request.user, 'role', 'No role defined') != 'admin':
#             return ['dashboard_student.html']
#         return ['dashboard.html']



# from apps.admissions.models import HscAdmissions

# class SampleView(TemplateView):
#     template_name = 'dashboard.html'

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['user'] = self.request.user  # Explicitly set user
#         print("SampleView get_context_data called, Role:", getattr(self.request.user, 'role', 'No role defined'))

#         # Normalize phone number and fetch admission record
#         if self.request.user.is_authenticated and hasattr(self.request.user, 'phone_number'):
#             phone_number = self.request.user.phone_number
#             if phone_number.startswith('+880'):
#                 phone_number = phone_number[2:]  # Remove '+880'
#             elif phone_number.startswith('880'):
#                 phone_number = phone_number[2:]  # Remove '880'
#             try:
#                 admission = HscAdmissions.objects.filter(add_mobile=phone_number).first()
#                 if admission:
#                     context['admission_group'] = admission.get_add_admission_group_display() or admission.add_admission_group
#                     context['admission_pk'] = admission.pk  # Add pk to context
#                 else:
#                     context['admission_group'] = None
#                     context['admission_pk'] = None
#             except HscAdmissions.DoesNotExist:
#                 context['admission_group'] = None
#                 context['admission_pk'] = None

#         context = TemplateLayout.init(self, context)  # Call TemplateLayout.init
#         return context

#     def get_template_names(self):
#         if getattr(self.request.user, 'role', 'No role defined') != 'admin':
#             return ['dashboard_student.html']
#         return ['dashboard.html']



from django.urls import reverse

from apps.admissions.models import HscAdmissions

class SampleView(TemplateView):
    """
    Student Dashboard (default) / Admin Dashboard (role=admin) switcher.
    Context adds:
      - admission_group, admission_pk
      - admission_paid (bool), admission_status ('paid'|'pending'|'unpaid'|None)
      - invoice_url (student view)
    """
    template_name = 'dashboard.html'

    @staticmethod
    def _normalize_phone(s: str) -> str:
        """+880 / 880 সরিয়ে 0 দিয়ে শুরু—DB-এর add_mobile এর সাথে মেলানোর জন্য।"""
        s = (s or '').strip()
        if s.startswith('+880'):
            s = s[4:]
        elif s.startswith('880'):
            s = s[3:]
        # ensure leading 0 (যেমন '1...' হলে '01...')
        if s and not s.startswith('0') and s[0] == '1':
            s = '0' + s
        return s

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['user'] = user

        admission = None
        if getattr(user, 'is_authenticated', False) and hasattr(user, 'phone_number'):
            phone = self._normalize_phone(user.phone_number)
            # সর্বশেষ রেকর্ড (সাম্প্রতিক আবেদন) নিন
            admission = (
                HscAdmissions.objects
                .filter(add_mobile=phone)
                .order_by('-id')
                .first()
            )

        if admission:
            admission_paid = (admission.add_payment_status == 'paid')
            context.update({
                'admission': admission,
                'admission_group': admission.get_add_admission_group_display() or admission.add_admission_group,
                'admission_pk': admission.pk,
                'admission_paid': admission_paid,
                'admission_status': admission.add_payment_status,  # 'paid' | 'pending' | 'unpaid'
                # ইনভয়েস ইউআরএল—স্টুডেন্টের ভিউ; টেমপ্লেটে বাটন disabled/hidden হ্যান্ডেল করুন
                'invoice_url': reverse('student_invoice', kwargs={'pk': admission.pk}),
            })
        else:
            context.update({
                'admission_group': None,
                'admission_pk': None,
                'admission_paid': False,
                'admission_status': None,
                'invoice_url': None,
            })

        # আপনার লেআউট ইনিশিয়ালাইজার
        context = TemplateLayout.init(self, context)
        return context

    def get_template_names(self):
        # admin হলে admin dashboard; নইলে student dashboard
        if getattr(self.request.user, 'role', '') == 'admin':
            return ['dashboard.html']
        return ['dashboard_student.html']








from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required

@login_required
def dashboard(request):
    print("printing Role: ",request.user.role)
    if request.user.role == 'student':
        return render(request, "dashboard_student.html")
    else:
        return render(request, "dashboard.html")
