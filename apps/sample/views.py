from web_project import TemplateLayout, TemplateHelper

from django.views.generic import TemplateView, ListView
from django.db.models import Count, Q
from django.contrib.auth.mixins import LoginRequiredMixin

"""
This file is a view controller for multiple pages as a module.
Here you can override the page view layout.
Refer to sample/urls.py file for more pages.
"""
from django.db.models import Count
from django.urls import reverse
from urllib.parse import urlencode
from apps.admissions.models import HscAdmissions, DegreeAdmission, Programs, DegreePrograms
from django.db.models import Q




# class SampleView(LoginRequiredMixin, TemplateView):
#     template_name = 'dashboard.html'

#     @staticmethod
#     def _normalize_phone(s: str) -> str:
#         s = (s or '').strip()
#         if s.startswith('+880'):
#             s = s[4:]
#         elif s.startswith('880'):
#             s = s[3:]
#         if s and not s.startswith('0') and s[0] == '1':
#             s = '0' + s
#         return s

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         user = self.request.user
#         context['user'] = user

#         # Active session filter
#         active_session_id = self.request.session.get('active_session_id')
#         qs = HscAdmissions.objects.all()
#         if active_session_id:
#             qs = qs.filter(add_session_id=active_session_id)

#         # --- Admin cards (আগের মতো) ---
#         group_field = HscAdmissions._meta.get_field('add_admission_group')
#         choices = list(group_field.choices)
#         raw = {
#             r['add_admission_group']: r['n']
#             for r in qs.values('add_admission_group').annotate(n=Count('id'))
#         }
#         counts = {value: raw.get(value, 0) for (value, _lbl) in choices}
#         context.update({
#             'hsc_total': qs.count(),
#             'hsc_counts': counts,
#             'hsc_labels': dict(choices),
#         })

#         # ✅ HSC urls build করুন (session/program থাকলে সাথে জুড়ে দিন)
#         base = reverse('admitted_students_list')  # আপনার লিস্ট ভিউয়ের নাম
#         # HSC program id (থাকলে)
#         try:
#             hsc_program_id = Programs.objects.filter(pro_name__iexact='hsc').values_list('id', flat=True).first()
#         except Exception:
#             hsc_program_id = None

#         def make_url(group_key: str) -> str:
#             params = {'group': group_key}
#             if active_session_id:
#                 params['session'] = active_session_id
#             if hsc_program_id:
#                 params['program'] = hsc_program_id
#             return f"{base}?{urlencode(params)}"

#         context['hsc_urls'] = {
#             'science': make_url('science'),
#             'arts': make_url('arts'),
#             'commerce': make_url('commerce'),
#         }

#         # ----- Student section (আগের মতো) -----
#         if user.is_authenticated:
#             norm = self._normalize_phone(getattr(user, 'phone_number', ''))
#             last11 = norm[-11:] if norm else None

#             admission = qs.filter(
#                 Q(created_by=user) |
#                 Q(add_mobile=norm) |
#                 (Q(add_mobile__endswith=last11) if last11 else Q(pk__isnull=True))
#             ).order_by('-id').first()

#             # ✅ invoice_url build
#             invoice_url = None
#             if admission and getattr(admission, 'add_payment_status', '') == 'paid':
#                 # তোমার ইনভয়েস ভিউয়ের URL name অনুযায়ী একটা বেছে নাও:
#                 try:
#                     # যদি এই রুট থাকে
#                     invoice_url = reverse('student_invoice', kwargs={'pk': admission.pk})
#                 except Exception:
#                     try:
#                         # অথবা যদি এটা থাকে
#                         invoice_url = reverse('hsc_admission_view', kwargs={'pk': admission.pk})
#                     except Exception:
#                         # fallback: প্রিন্ট ভিউ ব্যবহার করলেও হবে
#                         invoice_url = reverse('hsc_admission_view', kwargs={'pk': admission.pk})

#             context.update({
#                 'admission': admission,
#                 'admission_pk': admission.pk if admission else None,
#                 'admission_group': getattr(admission, 'add_admission_group', None) if admission else None,
#                 'admission_status': getattr(admission, 'add_payment_status', None) if admission else None,
#                 'admission_paid': (getattr(admission, 'add_payment_status', '') == 'paid') if admission else False,
#                 'invoice_url': invoice_url,  # ✅ new
#             })

#         context = TemplateLayout.init(self, context)
#         return context

#     def get_template_names(self):
#         return ['dashboard.html'] if getattr(self.request.user, 'role', '') == 'admin' else ['dashboard_student.html']


class SampleView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

    @staticmethod
    def _normalize_phone(s: str) -> str:
        s = (s or '').strip()
        if s.startswith('+880'):
            s = s[4:]
        elif s.startswith('880'):
            s = s[3:]
        if s and not s.startswith('0') and s[0] == '1':
            s = '0' + s
        return s

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['user'] = user

        # -------- HSC SECTION --------
        active_session_id = self.request.session.get('active_session_id')
        hsc_qs = HscAdmissions.objects.all()
        if active_session_id:
            hsc_qs = hsc_qs.filter(add_session_id=active_session_id)

        group_field = HscAdmissions._meta.get_field('add_admission_group')
        hsc_choices = list(group_field.choices)
        raw_hsc = {
            r['add_admission_group']: r['n']
            for r in hsc_qs.values('add_admission_group').annotate(n=Count('id'))
        }
        hsc_counts = {value: raw_hsc.get(value, 0) for (value, _lbl) in hsc_choices}
        context.update({
            'hsc_total': hsc_qs.count(),
            'hsc_counts': hsc_counts,
            'hsc_labels': dict(hsc_choices),
        })

        # HSC urls
        base = reverse('admitted_students_list')
        try:
            hsc_program_id = Programs.objects.filter(
                pro_name__iexact='hsc'
            ).values_list('id', flat=True).first()
        except Exception:
            hsc_program_id = None

        def make_hsc_url(group_key: str) -> str:
            params = {'group': group_key}
            if active_session_id:
                params['session'] = active_session_id
            if hsc_program_id:
                params['program'] = hsc_program_id
            return f"{base}?{urlencode(params)}"

        context['hsc_urls'] = {
            'science': make_hsc_url('science'),
            'arts': make_hsc_url('arts'),
            'commerce': make_hsc_url('commerce'),
        }

        # -------- DEGREE SECTION --------
        deg_qs = DegreeAdmission.objects.all()
        if active_session_id:
            deg_qs = deg_qs.filter(add_session_id=active_session_id)

        raw_deg = {
            r['add_admission_group']: r['n']
            for r in deg_qs.values('add_admission_group').annotate(n=Count('id'))
        }
        deg_group_choices = [
            ('Ba', 'BA'),
            ('Bss', 'BSS'),
            ('Bbs', 'BBS'),
            ('Bsc', 'BSC'),
        ]
        deg_counts = {value: raw_deg.get(value, 0) for (value, _lbl) in deg_group_choices}
        context.update({
            'deg_total': deg_qs.count(),
            'deg_counts': deg_counts,
            'deg_labels': dict(deg_group_choices),
        })

        # Degree urls
        deg_base = reverse('degree_admitted_students_list')

        def make_deg_url(group_key: str) -> str:
            params = {'group': group_key}
            if active_session_id:
                params['session'] = active_session_id
            return f"{deg_base}?{urlencode(params)}"

        context['deg_urls'] = {
            'ba': make_deg_url('Ba'),
            'bss': make_deg_url('Bss'),
            'bbs': make_deg_url('Bbs'),
            'bsc': make_deg_url('Bsc'),
        }

        # -------- Student SELF admission (HSC + Degree) --------
        if user.is_authenticated:
            norm = self._normalize_phone(getattr(user, 'phone_number', ''))
            last11 = norm[-11:] if norm else None

            # HSC admission detect
            admission = hsc_qs.filter(
                Q(created_by=user) |
                Q(add_mobile=norm) |
                (Q(add_mobile__endswith=last11) if last11 else Q(pk__isnull=True))
            ).order_by('-id').first()

            hsc_invoice_url = None
            if admission and getattr(admission, 'add_payment_status', '') == 'paid':
                try:
                    hsc_invoice_url = reverse('student_invoice', kwargs={'pk': admission.pk})
                except Exception:
                    hsc_invoice_url = reverse('hsc_admission_view', kwargs={'pk': admission.pk})

            context.update({
                'admission': admission,
                'admission_pk': admission.pk if admission else None,
                'admission_group': getattr(admission, 'add_admission_group', None) if admission else None,
                'admission_status': getattr(admission, 'add_payment_status', None) if admission else None,
                'admission_paid': (getattr(admission, 'add_payment_status', '') == 'paid') if admission else False,
                'invoice_url': hsc_invoice_url,
            })

            # Degree admission detect
            deg_admission = deg_qs.filter(
                Q(created_by=user) |
                Q(add_mobile=norm) |
                (Q(add_mobile__endswith=last11) if last11 else Q(pk__isnull=True))
            ).order_by('-id').first()

            deg_invoice_url = None
            if deg_admission and getattr(deg_admission, 'add_payment_status', '') == 'paid':
                try:
                    deg_invoice_url = reverse('degree_student_invoice', kwargs={'pk': deg_admission.pk})
                except Exception:
                    deg_invoice_url = reverse('degree_student_invoice', kwargs={'pk': deg_admission.pk})

            context.update({
                'deg_admission': deg_admission,
                'deg_admission_pk': deg_admission.pk if deg_admission else None,
                'deg_admission_group': getattr(deg_admission, 'add_admission_group', None) if deg_admission else None,
                'deg_admission_status': getattr(deg_admission, 'add_payment_status', None) if deg_admission else None,
                'deg_admission_paid': (getattr(deg_admission, 'add_payment_status', '') == 'paid') if deg_admission else False,
                'deg_invoice_url': deg_invoice_url,
            })

        context = TemplateLayout.init(self, context)
        return context

    def get_template_names(self):
        return (
            ['dashboard.html']
            if getattr(self.request.user, 'role', '') == 'admin'
            else ['dashboard_student.html']
        )





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
