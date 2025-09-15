from .utils import get_allowed_ssc_rolls
from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.forms.widgets import ClearableFileInput
from .models import HscAdmissions, Session
from .utils import get_allowed_ssc_rolls
import re
from .models import HscAdmissions, Subjects, Fee, DegreeAdmission, Session

# ---------- Helpers ----------
def validate_mobile_number(mobile: str, field_label: str = "মোবাইল"):
    """Normalize +880/880 -> 0, ensure 01xxxxxxxxx (11 digits)."""
    if not mobile:
        return mobile
    mobile = str(mobile).strip()
    mobile = mobile.replace('+880', '').replace('880', '')
    if not mobile.startswith('0'):
        mobile = '0' + mobile
    if not re.match(r'^01\d{9}$', mobile):
        raise ValidationError(f"{field_label} অবশ্যই ১১ সংখ্যার হতে হবে এবং '01' দিয়ে শুরু হতে হবে।")
    return mobile


# ---------- Forms ----------
class HscAdmissionForm(forms.ModelForm):
    class Meta:
        model = HscAdmissions
        exclude = [
            'add_program', 'add_admission_group',
            'created_by', 'submitted_via', 'created_at', 'updated_at'
        ]
        widgets = {
            'add_amount': forms.NumberInput(attrs={'readonly': 'readonly', 'class': 'form-control', 'id': 'id_add_amount'}),
            'add_birthdate': forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'placeholder': 'YYYY-MM-DD'}),
            'add_father_birthdate': forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'placeholder': 'YYYY-MM-DD'}),
            'add_mother_birthdate': forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'placeholder': 'YYYY-MM-DD'}),
            'add_photo': ClearableFileInput(attrs={'class': 'form-control'}),
            'add_ssc_roll': forms.NumberInput(attrs={'class': 'form-control'}),
            'add_ssc_passyear': forms.NumberInput(attrs={'class': 'form-control'}),
            'add_birth_certificate_no': forms.TextInput(attrs={'class': 'form-control'}),
            'add_father_nid': forms.TextInput(attrs={'class': 'form-control'}),
            'add_mother_nid': forms.TextInput(attrs={'class': 'form-control'}),
            'add_parent_nid': forms.TextInput(attrs={'class': 'form-control'}),
            'add_ssc_reg': forms.NumberInput(attrs={'class': 'form-control'}),
            'add_postal': forms.NumberInput(attrs={'class': 'form-control'}),
            'add_postal_per': forms.NumberInput(attrs={'class': 'form-control'}),
            'add_parent_income': forms.NumberInput(attrs={'class': 'form-control'}),
            'merit_position': forms.NumberInput(attrs={'class': 'form-control'}),
            'add_class_roll': forms.NumberInput(attrs={'class': 'form-control'}),
            'add_class_id': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        # allow passing request/user from view
        self.request = kwargs.pop('request', None)
        self.user = kwargs.pop('user', getattr(self.request, 'user', None))
        super().__init__(*args, **kwargs)

        # --- required fields (super() এর পর) ---
        self.fields['add_name'].required = True
        self.fields['add_ssc_roll'].required = True
        self.fields['add_name'].error_messages['required'] = "নাম প্রয়োজন।"
        self.fields['add_ssc_roll'].error_messages['required'] = "SSC রোল প্রয়োজন।"
        self.fields['add_photo'].required = True

        # basic styling
        for f in self.fields.values():
            f.widget.attrs.setdefault('class', 'form-control')

        # session field config
        self.fields['add_session'].required = True
        self.fields['add_session'].widget.attrs['id'] = 'id_add_session'
        self.fields['add_amount'].required = False

        # make trxid & slip required at form-level (solves template method call error)
        for name in ("add_trxid", "add_slip"):
            if name in self.fields:
                self.fields[name].required = True
                self.fields[name].widget.attrs["required"] = "required"

        # -------- Session: student হলে ডিফল্ট + লক --------
        def get_default_session_2025_2026():
            s = Session.objects.filter(ses_name__iexact='2025 - 2026').first()
            if s: return s
            s = Session.objects.filter(ses_name__in=['2025-2026', '2025-26', '2025 - 26']).first()
            if s: return s
            s = Session.objects.filter(ses_status='active').first()
            if s: return s
            return Session.objects.order_by('-id').first()

        self._locked_session = None
        if getattr(self.user, 'is_authenticated', False) and getattr(self.user, 'role', None) == 'student':
            default_sess = get_default_session_2025_2026()
            if default_sess:
                self.fields['add_session'].initial = default_sess.pk
                self.fields['add_session'].required = False
                self.fields['add_session'].disabled = True
                self.fields['add_session'].widget.attrs.update({
                    'class': 'form-select',
                    'style': 'pointer-events:none;background:#f8f9fa;',
                    'data-locked': '1',
                })
                self._locked_session = default_sess
        else:
            self.fields['add_session'].widget.attrs.setdefault('class', 'form-select')

        # placeholders
        placeholders = {
            'add_name': 'Enter your name in English',
            'add_name_bangla': 'বাংলায় নাম লিখুন',
            'add_mobile': '01XXXXXXXXX',
            'add_age': 'e.g. 16',
            'add_father': "Father's Name (English)",
            'add_father_mobile': "Father's Mobile Number",
            'add_father_nid': "Father's NID Number",
            'add_father_birthdate': 'Father Birthdate (YYYY-MM-DD)',
            'add_mother': "Mother's Name (English)",
            'add_mother_mobile': "Mother's Mobile Number",
            'add_mother_nid': "Mother's NID Number",
            'add_mother_birthdate': 'Mother Birthdate (YYYY-MM-DD)',
            'add_parent_select': 'Select Parent/Guardian Type',
            'add_parent': "Guardian's Name",
            'add_parent_mobile': "Guardian's Mobile",
            'add_parent_relation': 'Guardian Relation (e.g. Uncle)',
            'add_parent_service': 'Guardian Occupation',
            'add_parent_income': 'Monthly Income',
            'add_parent_nid': 'Guardian NID Number',
            'add_parent_land_agri': 'Agricultural Land in Decimal',
            'add_parent_land_nonagri': 'Non-Agricultural Land',
            'add_village': 'Present Village',
            'add_post': 'Present Post Office',
            'add_police': 'Present Police Station/Upazila',
            'add_postal': 'Present Postal Code',
            'add_distric': 'Present District',
            'add_village_per': 'Permanent Village',
            'add_post_per': 'Permanent Post Office',
            'add_police_per': 'Permanent Police Station/Upazila',
            'add_postal_per': 'Permanent Postal Code',
            'add_distric_per': 'Permanent District',
            'add_birthdate': 'Your Birthdate (YYYY-MM-DD)',
            'add_marital_status': 'Select Marital Status',
            'add_ssc_roll': 'SSC Roll Number',
            'add_ssc_reg': 'SSC Registration No',
            'add_ssc_session': 'e.g. 2020-21',
            'add_ssc_institute': 'SSC Institute Name',
            'add_ssc_gpa': 'SSC GPA (e.g. 5.00)',
            'add_ssc_group': 'Select SSC Group',
            'add_ssc_board': 'e.g. Dhaka',
            'add_ssc_passyear': 'e.g. 2022',
            'add_payment_method': 'Select Payment Method',
            'add_trxid': 'Transaction ID',
            'add_slip': 'Payment Mobile Number',
            'add_class_roll': 'HSC Class Roll',
            'add_class_id': 'Add Student Class ID',
            'add_hsc_year': 'Select HSC Year',
            'add_blood_group': 'Select Blood Group',
            'add_birth_certificate_no': 'Birth Certificate No',
            'add_gender': 'Select Gender',
            'add_nationality': 'e.g. Bangladeshi',
            'add_religion': 'Select Religion',
            'add_photo': 'Upload Photo',
            'qouta_name': 'Quota Name if Applicable',
            'community_name': 'Community Name if Applicable',
            'merit_position': 'Merit Position',
            'main_subject': 'Select Main Subject',
            'fourth_subject': 'Select Fourth Subject',
            'optional_subject': 'Select Optional Subject',
            'optional_subject_2': 'Select Optional Subject 2',
        }
        for name, ph in placeholders.items():
            if name in self.fields:
                self.fields[name].widget.attrs.setdefault('placeholder', ph)

        # student হলে মোবাইল read-only + auto-fill
        if getattr(self.user, 'is_authenticated', False) and getattr(self.user, 'role', None) == 'student':
            phone = getattr(self.user, 'phone_number', '') or ''
            if phone and not self.initial.get('add_mobile'):
                self.fields['add_mobile'].initial = phone
            self.fields['add_mobile'].widget.attrs['readonly'] = 'readonly'

    # ----------------- CLEAN METHODS -----------------
    def clean_add_session(self):
        if getattr(self.user, 'is_authenticated', False) and getattr(self.user, 'role', None) == 'student':
            if getattr(self, '_locked_session', None):
                return self._locked_session
        return self.cleaned_data.get('add_session')

    def clean_add_mobile(self):
        if getattr(self.user, 'is_authenticated', False) and getattr(self.user, 'role', None) == 'student':
            phone = getattr(self.user, 'phone_number', '') or ''
            return validate_mobile_number(phone, "আপনার মোবাইল")
        return validate_mobile_number(self.cleaned_data.get('add_mobile'), "আপনার মোবাইল")

    def clean_add_slip(self):
        return validate_mobile_number(self.cleaned_data.get('add_slip'), "Payment Mobile Number")

    def clean_add_trxid(self):
        v = (self.cleaned_data.get('add_trxid') or '').strip()
        if not v:
            raise ValidationError("Transaction ID প্রয়োজন।")
        qs = HscAdmissions.objects.filter(add_trxid=v)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("এই ট্রানজ্যাকশন আইডি ইতিমধ্যে ব্যবহৃত হয়েছে।")
        return v

    def clean_add_ssc_roll(self):
        roll = self.cleaned_data.get("add_ssc_roll")
        if roll in (None, ""):
            return roll  # required/optional rules handle empties

        allowed = get_allowed_ssc_rolls()
        if not allowed:
            return roll  # CSV missing/empty => skip check

        try:
            r = int(roll)
        except (TypeError, ValueError):
            r = None

        if r not in allowed:
            raise ValidationError("এই SSC Roll অনুমোদিত তালিকায় নেই। সঠিক রোল দিন বা অফিসে যোগাযোগ করুন।")
        return roll

    def clean_add_class_roll(self):
        roll = self.cleaned_data.get('add_class_roll')
        if roll is None:
            return roll

        # Determine group: instance > URL hint
        group = getattr(self.instance, 'add_admission_group', None)
        if not group and self.request:
            p = (self.request.path or '').lower()
            if 'apply/arts' in p:
                group = 'arts'
            elif 'apply/commerce' in p:
                group = 'commerce'
            else:
                group = 'science'

        if group:
            qs = HscAdmissions.objects.filter(add_admission_group=group, add_class_roll=roll)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError("এই গ্রুপে এই রোল নম্বর ইতিমধ্যেই আছে।")
        return roll


class ArtsAdmissionForm(forms.ModelForm):
    class Meta:
        model = HscAdmissions
        exclude = [
            "add_program", "add_admission_group",
            "created_by", "submitted_via", "created_at", "updated_at",
        ]
        widgets = {
            "add_amount": forms.NumberInput(attrs={
                "readonly": "readonly", "class": "form-control", "id": "id_add_amount"
            }),
            "add_birthdate": forms.DateInput(attrs={
                "type": "date", "class": "form-control", "placeholder": "YYYY-MM-DD"
            }),
            "add_father_birthdate": forms.DateInput(attrs={
                "type": "date", "class": "form-control", "placeholder": "YYYY-MM-DD"
            }),
            "add_mother_birthdate": forms.DateInput(attrs={
                "type": "date", "class": "form-control", "placeholder": "YYYY-MM-DD"
            }),
            "add_photo": ClearableFileInput(attrs={"class": "form-control"}),
            "add_ssc_roll": forms.NumberInput(attrs={"class": "form-control"}),
            "add_ssc_reg": forms.NumberInput(attrs={"class": "form-control"}),
            "add_ssc_passyear": forms.NumberInput(attrs={"class": "form-control"}),
            'add_birth_certificate_no': forms.TextInput(attrs={'class': 'form-control'}),
            "add_father_nid": forms.TextInput(attrs={"class": "form-control"}),
            "add_mother_nid": forms.TextInput(attrs={"class": "form-control"}),
            "add_parent_nid": forms.TextInput(attrs={"class": "form-control"}),
            "add_postal": forms.NumberInput(attrs={"class": "form-control"}),
            "add_postal_per": forms.NumberInput(attrs={"class": "form-control"}),
            "add_parent_income": forms.NumberInput(attrs={"class": "form-control"}),
            "merit_position": forms.NumberInput(attrs={"class": "form-control"}),
            "add_class_roll": forms.NumberInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        self.user = kwargs.pop("user", getattr(self.request, "user", None))
        super().__init__(*args, **kwargs)

        # --- required fields (super() এর পর) ---
        self.fields['add_name'].required = True
        self.fields['add_ssc_roll'].required = True
        self.fields['add_name'].error_messages['required'] = "নাম প্রয়োজন।"
        self.fields['add_ssc_roll'].error_messages['required'] = "SSC রোল প্রয়োজন।"

        # Add bootstrap class to all non-radio/checkbox widgets.
        for f in self.fields.values():
            w = f.widget
            if getattr(w, "input_type", None) not in ("radio", "checkbox"):
                w.attrs["class"] = (w.attrs.get("class", "") + " form-control").strip()

        # Session select look + requirements
        self.fields["add_session"].widget.attrs["id"] = "id_add_session"
        self.fields["add_session"].widget.attrs["class"] = "form-select"
        self.fields["add_session"].required = True

        # amount is filled by JS
        self.fields["add_amount"].required = False

        # Students must provide payment fields; staff can keep them optional.
        is_student = getattr(self.user, "is_authenticated", False) and getattr(self.user, "role", None) == "student"
        if "add_trxid" in self.fields:
            self.fields["add_trxid"].required = is_student
        if "add_slip" in self.fields:
            self.fields["add_slip"].required = is_student
        if "add_payment_method" in self.fields:
            self.fields["add_payment_method"].required = is_student

        # ----- Session locking for students -----
        def get_default_session_2025_2026():
            s = Session.objects.filter(ses_name__iexact="2025 - 2026").first()
            if s: return s
            s = Session.objects.filter(ses_name__in=["2025-2026", "2025-26", "2025 - 26"]).first()
            if s: return s
            s = Session.objects.filter(ses_status="active").first()
            if s: return s
            return Session.objects.order_by("-id").first()

        self._locked_session = None
        if is_student:
            locked = getattr(self.instance, "add_session", None) or get_default_session_2025_2026()
            if locked:
                self.fields["add_session"].initial = locked.pk
                self.fields["add_session"].disabled = True
                self.fields["add_session"].required = False
                self.fields["add_session"].widget.attrs.update({
                    "style": "pointer-events:none;background:#f8f9fa;",
                    "data-locked": "1",
                })
                self._locked_session = locked

        # Placeholders
        placeholders = {
            "add_name": "Enter your name in English",
            "add_name_bangla": "বাংলায় নাম লিখুন",
            "add_mobile": "01XXXXXXXXX",
            "add_age": "e.g. 16",
            "add_father": "Father's Name",
            "add_father_mobile": "Father's Mobile Number",
            "add_father_nid": "Father's NID Number",
            "add_father_birthdate": "Father Birthdate (YYYY-MM-DD)",
            "add_mother": "Mother's Name",
            "add_mother_mobile": "Mother's Mobile Number",
            "add_mother_nid": "Mother's NID Number",
            "add_mother_birthdate": "Mother Birthdate (YYYY-MM-DD)",
            "add_parent_select": "Select Parent/Guardian Type",
            "add_parent": "Guardian's Name",
            "add_parent_mobile": "Guardian's Mobile",
            "add_parent_relation": "Guardian Relation",
            "add_parent_service": "Guardian Occupation",
            "add_parent_income": "Monthly Income",
            "add_parent_nid": "Guardian NID Number",
            "add_parent_land_agri": "Agricultural Land (dec.)",
            "add_parent_land_nonagri": "Non-agri Land",
            "add_village": "Present Village",
            "add_post": "Present Post Office",
            "add_police": "Present Police Station/Upazila",
            "add_postal": "Present Postal Code",
            "add_distric": "Present District",
            "add_village_per": "Permanent Village",
            "add_post_per": "Permanent Post Office",
            "add_police_per": "Permanent Police Station/Upazila",
            "add_postal_per": "Permanent Postal Code",
            "add_distric_per": "Permanent District",
            "add_birthdate": "Your Birthdate (YYYY-MM-DD)",
            "add_marital_status": "Select Marital Status",
            "add_ssc_roll": "SSC Roll",
            "add_ssc_reg": "SSC Registration",
            "add_ssc_session": "e.g. 2020-21",
            "add_ssc_institute": "SSC Institute Name",
            "add_ssc_gpa": "SSC GPA (e.g. 5.00)",
            "add_ssc_group": "Select SSC Group",
            "add_ssc_board": "e.g. Dhaka",
            "add_ssc_passyear": "e.g. 2022",
            "add_payment_method": "Select Payment Method",
            "add_trxid": "Transaction ID",
            "add_slip": "Payment Mobile Number",
            "add_class_roll": "HSC Class Roll",
            "add_hsc_year": "Select HSC Year",
            "add_blood_group": "Select Blood Group",
            "add_birth_certificate_no": "Birth Cert. No",
            "add_gender": "Select Gender",
            "add_nationality": "e.g. Bangladeshi",
            "add_religion": "Select Religion",
            "add_photo": "Upload Photo",
            "qouta_name": "Quota Name if Applicable",
            "community_name": "Community Name if Applicable",
            "merit_position": "Merit Position",
            "main_subject": "Select Main Subject",
            "fourth_subject": "Select Fourth Subject",
            "optional_subject": "Select Optional Subject",
            "optional_subject_2": "Select Optional Subject 2",
        }
        for name, ph in placeholders.items():
            if name in self.fields:
                self.fields[name].widget.attrs.setdefault("placeholder", ph)

        # Student: autofill + lock mobile
        if is_student:
            phone = getattr(self.user, "phone_number", "") or ""
            if phone and not self.initial.get("add_mobile"):
                self.fields["add_mobile"].initial = phone
            self.fields["add_mobile"].widget.attrs["readonly"] = "readonly"

    # ---------- CLEAN METHODS ----------
    def clean_add_session(self):
        if getattr(self.user, "is_authenticated", False) and getattr(self.user, "role", None) == "student":
            if getattr(self, "_locked_session", None):
                return self._locked_session
        return self.cleaned_data.get("add_session")

    def clean_add_mobile(self):
        if getattr(self.user, "is_authenticated", False) and getattr(self.user, "role", None) == "student":
            phone = getattr(self.user, "phone_number", "") or ""
            return validate_mobile_number(phone, "আপনার মোবাইল")
        return validate_mobile_number(self.cleaned_data.get("add_mobile"), "আপনার মোবাইল")

    def clean_add_slip(self):
        return validate_mobile_number(self.cleaned_data.get("add_slip"), "Payment Mobile Number")

    def clean_add_trxid(self):
        v = (self.cleaned_data.get("add_trxid") or "").strip()
        if not v:
            return None
        qs = HscAdmissions.objects.filter(add_trxid=v)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("এই ট্রানজ্যাকশন আইডি ইতিমধ্যে ব্যবহৃত হয়েছে।")
        return v

    def clean(self):
        cleaned = super().clean()
        main_sub   = cleaned.get("main_subject")
        fourth_sub = cleaned.get("fourth_subject")
        opt1_sub   = cleaned.get("optional_subject")
        opt2_sub   = cleaned.get("optional_subject_2")

        picked = [s for s in (main_sub, fourth_sub, opt1_sub, opt2_sub) if s]

        # Prevent duplicate subject code
        codes = [(s.code or "").strip() for s in picked]
        if len(codes) != len(set(codes)):
            raise ValidationError("একই subject code দু’বার নেওয়া যাবে না।")

        # Capacity check in Arts
        qs = HscAdmissions.objects.filter(add_admission_group="arts")
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        for sub in picked:
            code = (sub.code or "").strip()
            if not code or sub.limit is None:
                continue
            used = qs.filter(
                Q(main_subject__code=code) |
                Q(fourth_subject__code=code) |
                Q(optional_subject__code=code) |
                Q(optional_subject_2__code=code)
            ).count()
            if used >= sub.limit:
                self.add_error(None, f"'{sub.sub_name}' (code: {code}) আসন পূর্ণ ({used}/{sub.limit}).")

        return cleaned

    def clean_add_ssc_roll(self):
        roll = self.cleaned_data.get("add_ssc_roll")
        if roll in (None, ""):
            return roll

        allowed = get_allowed_ssc_rolls()
        if not allowed:
            return roll

        try:
            r = int(roll)
        except (TypeError, ValueError):
            r = None

        if r not in allowed:
            raise ValidationError("এই SSC Roll অনুমোদিত তালিকায় নেই। সঠিক রোল দিন বা অফিসে যোগাযোগ করুন।")
        return roll

    def clean_add_class_roll(self):
        roll = self.cleaned_data.get("add_class_roll")
        if roll is None:
            return roll

        group = getattr(self.instance, "add_admission_group", None)
        if not group and self.request:
            if "apply/arts" in (self.request.path or "").lower():
                group = "arts"

        if group:
            qs = HscAdmissions.objects.filter(add_admission_group=group, add_class_roll=roll)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError("এই গ্রুপে এই রোল নম্বর ইতিমধ্যেই আছে।")
        return roll


# from .models import HscAdmissions

# class HscPaymentReviewForm(forms.ModelForm):
#     class Meta:
#         model = HscAdmissions
#         fields = [
#             "add_payment_method",
#             "add_amount",
#             "add_trxid",
#             "add_slip",
#             "add_payment_status",
#             "add_payment_note",
#         ]
#         widgets = {
#             "add_payment_method": forms.Select(attrs={"class": "form-select"}),
#             "add_amount": forms.NumberInput(attrs={"class": "form-control"}),
#             "add_trxid": forms.TextInput(attrs={"class": "form-control"}),
#             "add_slip": forms.TextInput(attrs={"class": "form-control", "placeholder": "From number"}),
#             "add_payment_status": forms.Select(attrs={"class": "form-select"}),
#             "add_payment_note": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
#         }

#     # ফাঁকা ট্রান্স্যাকশন আইডি None করে দেই (unique=true হলে খালি স্ট্রিং সমস্যা এড়ায়)
#     def clean_add_trxid(self):
#         v = (self.cleaned_data.get("add_trxid") or "").strip()
#         return v or None



from django import forms
from .models import HscAdmissions

class HscPaymentReviewForm(forms.ModelForm):
    class Meta:
        model = HscAdmissions
        fields = [
            "add_payment_method",
            "add_amount",
            "add_trxid",
            "add_slip",
            "add_payment_status",
            "add_payment_note",
        ]
        widgets = {
            "add_payment_method": forms.Select(attrs={"class": "form-select", "disabled": "disabled"}),
            "add_amount": forms.NumberInput(attrs={"class": "form-control", "disabled": "disabled"}),
            "add_trxid": forms.TextInput(attrs={"class": "form-control", "disabled": "disabled"}),
            "add_slip": forms.TextInput(attrs={"class": "form-control", "placeholder": "From number", "disabled": "disabled"}),
            "add_payment_status": forms.Select(attrs={"class": "form-select"}),
            "add_payment_note": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def clean_add_trxid(self):
        v = (self.cleaned_data.get("add_trxid") or "").strip()
        return v or None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure disabled fields are included in the form submission
        for field in ["add_payment_method", "add_amount", "add_trxid", "add_slip"]:
            self.fields[field].required = False  # Prevent validation errors for disabled fields



# Degree/ honors form
class DegreeAdmissionForm(forms.ModelForm):
    class Meta:
        model = DegreeAdmission
        exclude = [
            'add_program','add_admission_group',
            'created_by','submitted_via','created_at','updated_at'
        ]
        widgets = {
            'add_birthdate': forms.DateInput(attrs={
                'type': 'date','class': 'form-control','placeholder': 'YYYY-MM-DD'
            }),
            'add_father_birthdate': forms.DateInput(attrs={'type':'date','class':'form-control','placeholder':'YYYY-MM-DD'}),
            'add_mother_birthdate': forms.DateInput(attrs={'type':'date','class':'form-control','placeholder':'YYYY-MM-DD'}),
            'add_amount': forms.NumberInput(attrs={
                'readonly': 'readonly','class': 'form-control','id': 'id_add_amount'
            }),
            'add_photo': forms.FileInput(attrs={'class': 'form-control'}),
            'add_ssc_roll': forms.TextInput(attrs={'class': 'form-control'}),  # CharField, so TextInput
            'add_ssc_reg': forms.TextInput(attrs={'class': 'form-control'}),
            'add_hsc_roll': forms.TextInput(attrs={'class': 'form-control'}),
            'add_hsc_reg': forms.TextInput(attrs={'class': 'form-control'}),
            'add_postal': forms.NumberInput(attrs={'class': 'form-control'}),
            'add_postal_per': forms.NumberInput(attrs={'class': 'form-control'}),
            'add_parent_income': forms.NumberInput(attrs={'class': 'form-control'}),
            'merit_position': forms.TextInput(attrs={'class': 'form-control'}),
            'add_class_roll': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.user = kwargs.pop('user', getattr(self.request, 'user', None))
        super().__init__(*args, **kwargs)

        # style
        for f in self.fields.values():
            f.widget.attrs.setdefault('class', 'form-control')

        # required flags
        self.fields['add_session'].required = True
        self.fields['add_amount'].required = False
        self.fields['subjects'].required = False
        self.fields['main_subject'].required = False
        self.fields['add_photo'].required = True
        self.fields['add_session'].widget.attrs['id'] = 'id_add_session'

        # placeholders (corrected: add_police, added missing like add_father_nid, hsc fields, etc.)
        placeholders = {
            'add_name': 'Enter your name in English',
            'add_name_bangla': 'বাংলায় নাম লিখুন',
            'add_mobile': '01XXXXXXXXX',
            'add_age': 'e.g. 18',
            'add_photo': 'Upload Photo',
            'add_birthdate': 'Your Birthdate (YYYY-MM-DD)',
            'add_blood_group': 'Select Blood Group',
            'add_birth_certificate_no': 'Birth Cert. No',
            'add_gender': 'Select Gender',
            'add_nationality': 'e.g. Bangladeshi',
            'add_religion': 'Select Religion',
            'add_ssc_roll': 'SSC Roll',
            'add_ssc_reg': 'SSC Registration',
            'add_ssc_session': 'e.g. 2020-21',
            'add_ssc_gpa': 'SSC GPA (e.g. 5.00)',
            'add_ssc_board': 'e.g. Dhaka',
            'add_ssc_passyear': 'e.g. 2022',
            'add_ssc_institute': 'SSC Institute',
            'add_ssc_group': 'Select SSC Group',
            'add_father': "Father's Name",
            'add_father_mobile': "Father's Mobile Number",
            'add_father_nid': "Father's NID Number",
            'add_father_birthdate': 'Father Birthdate (YYYY-MM-DD)',
            'add_mother': "Mother's Name",
            'add_mother_mobile': "Mother's Mobile Number",
            'add_mother_nid': "Mother's NID Number",
            'add_mother_birthdate': 'Mother Birthdate (YYYY-MM-DD)',
            'add_parent_select': 'Select Parent/Guardian Type',
            'add_parent': "Guardian's Name",
            'add_parent_mobile': "Guardian's Mobile",
            'add_parent_relation': 'Guardian Relation',
            'add_parent_service': 'Guardian Occupation',
            'add_parent_nid': 'Guardian NID Number',
            'add_parent_income': 'Monthly Income',
            'add_parent_land_agri': 'Agricultural Land (dec.)',
            'add_parent_land_nonagri': 'Non-agri Land',
            'add_hsc_roll': 'HSC Roll',
            'add_hsc_reg': 'HSC Registration',
            'add_hsc_session': 'e.g. 2020-21',
            'add_hsc_gpa': 'HSC GPA (e.g. 5.00)',
            'add_hsc_board': 'e.g. Dhaka',
            'add_hsc_passyear': 'e.g. 2022',
            'add_hsc_institute': 'HSC Institute',
            'add_hsc_group': 'Select HSC Group',
            'add_village': 'Present Village',
            'add_post': 'Present Post Office',
            'add_police': 'Present Police Station/Upazila',
            'add_postal': 'Present Postal Code',
            'add_distric': 'Present District',
            'add_village_per': 'Permanent Village',
            'add_post_per': 'Permanent Post Office',
            'add_police_per': 'Permanent Police Station/Upazila',
            'add_postal_per': 'Permanent Postal Code',
            'add_distric_per': 'Permanent District',
            'add_marital_status': 'Select Marital Status',
            'add_session': 'Select Session',
            'main_subject': 'Select Main Subject',
            'add_class_roll': 'Class Roll',
            'merit_position': 'Merit Position',
            'add_payment_method': 'Select Payment Method',
            'add_trxid': 'Transaction ID',
            'add_slip': 'Your Note',
            'qouta_name': 'Quota Name if Applicable',
            'community_name': 'Community Name if Applicable',
        }
        for k, v in placeholders.items():
            if k in self.fields:
                self.fields[k].widget.attrs.setdefault('placeholder', v)

        # student হলে ফোন অটো-ফিল + readonly (tamper-proof)
        if getattr(self.user, 'is_authenticated', False) and getattr(self.user, 'role', None) == 'student':
            phone = getattr(self.user, 'phone_number', '') or ''
            if phone and not self.initial.get('add_mobile'):
                self.fields['add_mobile'].initial = phone
            self.fields['add_mobile'].widget.attrs['readonly'] = 'readonly'

    # mobiles
    def clean_add_mobile(self):
        if getattr(self.user, 'is_authenticated', False) and getattr(self.user, 'role', None) == 'student':
            phone = getattr(self.user, 'phone_number', '') or ''
            return validate_mobile_number(phone, "আপনার মোবাইল")
        return validate_mobile_number(self.cleaned_data.get('add_mobile'), "আপনার মোবাইল")

    # def clean_add_father_mobile(self):
    #     return validate_mobile_number(self.cleaned_data.get('add_father_mobile'), "পিতার মোবাইল")

    # def clean_add_mother_mobile(self):
    #     return validate_mobile_number(self.cleaned_data.get('add_mother_mobile'), "মাতার মোবাইল")

    # def clean_add_parent_mobile(self):
    #     return validate_mobile_number(self.cleaned_data.get('add_parent_mobile'), "অভিভাবকের মোবাইল")

    # add_trxid: '' → None + unique check (edit-safe)
    def clean_add_trxid(self):
        v = (self.cleaned_data.get('add_trxid') or '').strip()
        if not v:
            return None
        qs = DegreeAdmission.objects.filter(add_trxid=v)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("এই ট্রানজ্যাকশন আইডি ইতিমধ্যে ব্যবহৃত হয়েছে।")
        return v


class FeeForm(forms.ModelForm):
    class Meta:
        model = Fee
        fields = ['fee_session', 'fee_program', 'fee_group', 'amount']
        widgets = {
            'fee_session': forms.Select(attrs={'class': 'form-control'}),
            'fee_program': forms.Select(attrs={'class': 'form-control'}),
            'fee_group': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter Amount'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        session = cleaned_data.get('fee_session')
        program = cleaned_data.get('fee_program')
        group = cleaned_data.get('fee_group')

        if session and program and group:
            qs = Fee.objects.filter(
                fee_session=session,
                fee_program=program,
                fee_group=group
            )

            # ✅ Exclude current instance during update
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)

            if qs.exists():
                raise ValidationError("This fee combination already exists.")


# Global session filter form
class SessionSelectForm(forms.Form):
    session = forms.ModelChoiceField(
        queryset=Session.objects.all(),
        required=True,
        empty_label="Select Session",
        widget=forms.Select(attrs={'class': 'form-control'})
    )