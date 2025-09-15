from django.views.generic import TemplateView
from web_project import TemplateLayout, TemplateHelper

from django.views.generic import TemplateView, ListView
from django.db.models import Count, Q
from django.contrib.auth.mixins import LoginRequiredMixin

"""
This file is a view controller for multiple pages as a module.
Here you can override the page view layout.
Refer to sample/urls.py file for more pages.
"""
from django.views.generic import TemplateView
from django.db.models import Count
from django.urls import reverse
from urllib.parse import urlencode

from apps.admissions.models import HscAdmissions

from django.db.models import Q

# class SampleView(TemplateView):
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

#         active_session_id = self.request.session.get('active_session_id')
#         qs = HscAdmissions.objects.all()
#         if active_session_id:
#             qs = qs.filter(add_session_id=active_session_id)

#         # ===== Admin cards (existing) =====
#         group_field = HscAdmissions._meta.get_field('add_admission_group')
#         choices = list(group_field.choices)
#         raw = {r['add_admission_group']: r['n']
#                for r in qs.values('add_admission_group').annotate(n=Count('id'))}
#         counts = {value: raw.get(value, 0) for (value, _lbl) in choices}
#         context.update({
#             'hsc_total': qs.count(),
#             'hsc_counts': counts,
#             'hsc_labels': dict(choices),
#         })

#         # ===== Student side: fetch admission by normalized phone =====
#         if getattr(user, 'role', '') != 'admin':
#             norm = self._normalize_phone(getattr(user, 'phone_number', ''))
#             last11 = norm[-11:] if norm else None

#             qs_user = qs  # already filtered by active_session if any
#             admission = qs_user.filter(
#                 Q(created_by=user) |
#                 Q(user=user) |
#                 Q(add_mobile=norm) |
#                 (Q(add_mobile__endswith=last11) if last11 else Q(pk__isnull=True))
#             ).order_by('-id').first()

#             context.update({
#                 'admission': admission,
#                 'admission_pk': admission.pk if admission else None,
#                 'admission_group': getattr(admission, 'add_admission_group', None) if admission else None,
#                 'admission_status': getattr(admission, 'add_status', None) if admission else None,
#                 'admission_paid': (getattr(admission, 'add_status', '') == 'paid') if admission else False,
#             })

#         # keep your TemplateLayout init
#         context = TemplateLayout.init(self, context)
#         return context

#     def get_template_names(self):
#         if getattr(self.request.user, 'role', '') == 'admin':
#             return ['dashboard.html']
#         return ['dashboard_student.html']






# latest
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin

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

        # Active session filter
        active_session_id = self.request.session.get('active_session_id')
        qs = HscAdmissions.objects.all()
        if active_session_id:
            qs = qs.filter(add_session_id=active_session_id)

        # --- Admin cards (আগের মতো) ---
        group_field = HscAdmissions._meta.get_field('add_admission_group')
        choices = list(group_field.choices)
        raw = {
            r['add_admission_group']: r['n']
            for r in qs.values('add_admission_group').annotate(n=Count('id'))
        }
        counts = {value: raw.get(value, 0) for (value, _lbl) in choices}
        context.update({
            'hsc_total': qs.count(),
            'hsc_counts': counts,
            'hsc_labels': dict(choices),
        })

        # ✅ HSC urls build করুন (session/program থাকলে সাথে জুড়ে দিন)
        base = reverse('admitted_students_list')  # আপনার লিস্ট ভিউয়ের নাম
        # HSC program id (থাকলে)
        try:
            hsc_program_id = Programs.objects.filter(pro_name__iexact='hsc').values_list('id', flat=True).first()
        except Exception:
            hsc_program_id = None

        def make_url(group_key: str) -> str:
            params = {'group': group_key}
            if active_session_id:
                params['session'] = active_session_id
            if hsc_program_id:
                params['program'] = hsc_program_id
            return f"{base}?{urlencode(params)}"

        context['hsc_urls'] = {
            'science': make_url('science'),
            'arts': make_url('arts'),
            'commerce': make_url('commerce'),
        }

        # ----- Student section (আগের মতো) -----
        if user.is_authenticated:
            norm = self._normalize_phone(getattr(user, 'phone_number', ''))
            last11 = norm[-11:] if norm else None

            admission = qs.filter(
                Q(created_by=user) |
                Q(add_mobile=norm) |
                (Q(add_mobile__endswith=last11) if last11 else Q(pk__isnull=True))
            ).order_by('-id').first()

            # ✅ invoice_url build
            invoice_url = None
            if admission and getattr(admission, 'add_payment_status', '') == 'paid':
                # তোমার ইনভয়েস ভিউয়ের URL name অনুযায়ী একটা বেছে নাও:
                try:
                    # যদি এই রুট থাকে
                    invoice_url = reverse('student_invoice', kwargs={'pk': admission.pk})
                except Exception:
                    try:
                        # অথবা যদি এটা থাকে
                        invoice_url = reverse('hsc_admission_view', kwargs={'pk': admission.pk})
                    except Exception:
                        # fallback: প্রিন্ট ভিউ ব্যবহার করলেও হবে
                        invoice_url = reverse('hsc_admission_view', kwargs={'pk': admission.pk})

            context.update({
                'admission': admission,
                'admission_pk': admission.pk if admission else None,
                'admission_group': getattr(admission, 'add_admission_group', None) if admission else None,
                'admission_status': getattr(admission, 'add_payment_status', None) if admission else None,
                'admission_paid': (getattr(admission, 'add_payment_status', '') == 'paid') if admission else False,
                'invoice_url': invoice_url,  # ✅ new
            })

        context = TemplateLayout.init(self, context)
        return context

    def get_template_names(self):
        return ['dashboard.html'] if getattr(self.request.user, 'role', '') == 'admin' else ['dashboard_student.html']


# # ---------- List (click করলে যে পেজে যাবে) ----------
# # @method_decorator(admin_role_required, name='dispatch')  # শুধুই admin দেখবে—আপনার যেভাবে দরকার
# class HscStudentListView(LoginRequiredMixin, ListView):
#     model = HscAdmissions
#     template_name = 'admissions/hsc_student_list.html'  # নিচে টেমপ্লেট স্নিপেট দিলাম
#     context_object_name = 'students'
#     paginate_by = 25

#     def get_queryset(self):
#         qs = HscAdmissions.objects.all().order_by('-id')
#         group = self.request.GET.get('group', '').lower().strip()
#         if group in ('science', 'humanities', 'business'):
#             qs = qs.filter(add_admission_group=group)

#         q = self.request.GET.get('q', '').strip()
#         if q:
#             qs = qs.filter(Q(add_name__icontains=q) | Q(add_mobile__icontains=q))
#         return qs

#     def get_context_data(self, **kwargs):
#         ctx = super().get_context_data(**kwargs)
#         ctx['active_group'] = self.request.GET.get('group', '')
#         return ctx



# from django.urls import reverse

# from apps.admissions.models import HscAdmissions

# class SampleView(TemplateView):
#     """
#     Student Dashboard (default) / Admin Dashboard (role=admin) switcher.
#     Context adds:
#       - admission_group, admission_pk
#       - admission_paid (bool), admission_status ('paid'|'pending'|'unpaid'|None)
#       - invoice_url (student view)
#     """
#     template_name = 'dashboard.html'

#     @staticmethod
#     def _normalize_phone(s: str) -> str:
#         """+880 / 880 সরিয়ে 0 দিয়ে শুরু—DB-এর add_mobile এর সাথে মেলানোর জন্য।"""
#         s = (s or '').strip()
#         if s.startswith('+880'):
#             s = s[4:]
#         elif s.startswith('880'):
#             s = s[3:]
#         # ensure leading 0 (যেমন '1...' হলে '01...')
#         if s and not s.startswith('0') and s[0] == '1':
#             s = '0' + s
#         return s

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         user = self.request.user
#         context['user'] = user

#         admission = None
#         if getattr(user, 'is_authenticated', False) and hasattr(user, 'phone_number'):
#             phone = self._normalize_phone(user.phone_number)
#             # সর্বশেষ রেকর্ড (সাম্প্রতিক আবেদন) নিন
#             admission = (
#                 HscAdmissions.objects
#                 .filter(add_mobile=phone)
#                 .order_by('-id')
#                 .first()
#             )

#         if admission:
#             admission_paid = (admission.add_payment_status == 'paid')
#             context.update({
#                 'admission': admission,
#                 'admission_group': admission.get_add_admission_group_display() or admission.add_admission_group,
#                 'admission_pk': admission.pk,
#                 'admission_paid': admission_paid,
#                 'admission_status': admission.add_payment_status,  # 'paid' | 'pending' | 'unpaid'
#                 # ইনভয়েস ইউআরএল—স্টুডেন্টের ভিউ; টেমপ্লেটে বাটন disabled/hidden হ্যান্ডেল করুন
#                 'invoice_url': reverse('student_invoice', kwargs={'pk': admission.pk}),
#             })
#         else:
#             context.update({
#                 'admission_group': None,
#                 'admission_pk': None,
#                 'admission_paid': False,
#                 'admission_status': None,
#                 'invoice_url': None,
#             })

#         # আপনার লেআউট ইনিশিয়ালাইজার
#         context = TemplateLayout.init(self, context)
#         return context

#     def get_template_names(self):
#         # admin হলে admin dashboard; নইলে student dashboard
#         if getattr(self.request.user, 'role', '') == 'admin':
#             return ['dashboard.html']
#         return ['dashboard_student.html']








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
