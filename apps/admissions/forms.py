from .utils import get_allowed_ssc_rolls
from django import forms
from django.core.exceptions import ValidationError
from django.forms.widgets import ClearableFileInput
import re
from .models import HscAdmissions, Session, Subjects, Fee, DegreeAdmission

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
            # date & number widgets
            'add_birthdate': forms.DateInput(attrs={'type': 'date', 'placeholder': 'YYYY-MM-DD'}),
            'add_father_birthdate': forms.DateInput(attrs={'type': 'date', 'placeholder': 'YYYY-MM-DD'}),
            'add_mother_birthdate': forms.DateInput(attrs={'type': 'date', 'placeholder': 'YYYY-MM-DD'}),
            'add_ssc_roll': forms.NumberInput(),
            'add_ssc_passyear': forms.NumberInput(),
            'add_ssc_reg': forms.NumberInput(),
            'add_postal': forms.NumberInput(),
            'add_postal_per': forms.NumberInput(),
            'add_parent_income': forms.NumberInput(),
            'merit_position': forms.NumberInput(),
            'add_class_roll': forms.NumberInput(),
            # text widgets
            'add_birth_certificate_no': forms.TextInput(),
            'add_father_nid': forms.TextInput(),
            'add_mother_nid': forms.TextInput(),
            'add_parent_nid': forms.TextInput(),
            'add_class_id': forms.TextInput(),
            # file
            'add_photo': ClearableFileInput(),
            # computed / fee
            'add_amount': forms.NumberInput(attrs={'readonly': 'readonly', 'id': 'id_add_amount'}),
        }

    def __init__(self, *args, **kwargs):
        # capture request/user if passed from view
        self.request = kwargs.pop('request', None)
        self.user = kwargs.pop('user', getattr(self.request, 'user', None))
        super().__init__(*args, **kwargs)

        # -------- Required fields (existing) --------
        self.fields['add_name'].required = True
        self.fields['add_name'].error_messages['required'] = "নাম প্রয়োজন।"

        self.fields['add_ssc_roll'].required = True
        self.fields['add_ssc_roll'].error_messages['required'] = "SSC রোল প্রয়োজন।"

        self.fields['add_parent_service'].required = True
        self.fields['add_parent_service'].error_messages['required'] = "অভিভাবকের পেশা প্রয়োজন।"

        self.fields['add_parent_income'].required = True
        self.fields['add_parent_income'].error_messages['required'] = "অভিভাবকের মাসিক আয় প্রয়োজন।"

        # -------- Bulk required (your full list) --------
        required_map = {
            # Personal
            'add_name': "নাম প্রয়োজন।",
            'add_age': "বয়স প্রয়োজন।",
            'add_birthdate': "জন্মতারিখ প্রয়োজন।",
            'add_marital_status': "বৈবাহিক অবস্থা প্রয়োজন।",
            'add_birth_certificate_no': "জন্ম নিবন্ধন নম্বর প্রয়োজন।",
            'add_gender': "লিঙ্গ নির্বাচন করুন।",
            'add_nationality': "জাতীয়তা প্রয়োজন।",
            'add_religion': "ধর্ম নির্বাচন করুন।",

            # Father / Mother
            'add_father': "পিতার নাম প্রয়োজন।",
            'add_father_mobile': "পিতার মোবাইল প্রয়োজন।",
            'add_father_nid': "পিতার NID প্রয়োজন।",
            'add_father_birthdate': "পিতার জন্মতারিখ প্রয়োজন।",
            'add_mother': "মাতার নাম প্রয়োজন।",

            # Guardian
            'add_parent_select': "অভিভাবক নির্বাচন করুন।",
            'add_parent': "অভিভাবকের নাম প্রয়োজন।",
            'add_parent_mobile': "অভিভাবকের মোবাইল প্রয়োজন।",
            'add_parent_relation': "অভিভাবকের সম্পর্ক প্রয়োজন।",
            'add_parent_service': "অভিভাবকের পেশা প্রয়োজন।",
            'add_parent_income': "অভিভাবকের মাসিক আয় প্রয়োজন।",

            # Present address
            'add_village': "বর্তমান গ্রাম প্রয়োজন।",
            'add_post': "বর্তমান ডাকঘর প্রয়োজন।",
            'add_police': "বর্তমান থানা/উপজেলা প্রয়োজন।",
            'add_postal': "বর্তমান পোস্টকোড প্রয়োজন।",
            'add_distric': "বর্তমান জেলা প্রয়োজন।",

            # Permanent address
            'add_village_per': "স্থায়ী গ্রাম প্রয়োজন।",
            'add_post_per': "স্থায়ী ডাকঘর প্রয়োজন।",
            'add_police_per': "স্থায়ী থানা/উপজেলা প্রয়োজন।",
            'add_postal_per': "স্থায়ী পোস্টকোড প্রয়োজন।",
            'add_distric_per': "স্থায়ী জেলা প্রয়োজন।",

            # SSC
            'add_ssc_roll': "SSC রোল প্রয়োজন।",
            'add_ssc_reg': "SSC রেজিস্ট্রেশন নম্বর প্রয়োজন।",
            'add_ssc_session': "SSC সেশন প্রয়োজন।",
            'add_ssc_institute': "SSC ইনস্টিটিউট প্রয়োজন।",
            'add_ssc_gpa': "SSC GPA প্রয়োজন।",
            'add_ssc_group': "SSC গ্রুপ নির্বাচন করুন।",
            'add_ssc_board': "SSC বোর্ড নির্বাচন করুন।",
            'add_ssc_passyear': "SSC পাশের বছর প্রয়োজন।",
        }
        for fname, msg in required_map.items():
            if fname in self.fields:
                self.fields[fname].required = True
                self.fields[fname].error_messages['required'] = msg

        # Quota name only when qouta is True
        if 'qouta_name' in self.fields:
            want_quota = None
            if self.data:
                # respect form prefix if any
                qkey = self.add_prefix('qouta')
                want_quota = self.data.get(qkey) in ('True', 'true', '1', 'on', 'yes')
            elif self.instance and getattr(self.instance, 'qouta', False):
                want_quota = True
            self.fields['qouta_name'].required = bool(want_quota)
            if want_quota:
                self.fields['qouta_name'].error_messages['required'] = "কোটা নাম প্রয়োজন।"

        # Photo: new → required, edit with existing photo → optional
        if not self.instance.pk or (self.instance.pk and not getattr(self.instance, 'add_photo', None)):
            self.fields['add_photo'].required = True
            self.fields['add_photo'].error_messages['required'] = "ফটো আপলোড করা প্রয়োজন।"
        else:
            self.fields['add_photo'].required = False

        # Session field config
        self.fields['add_session'].required = True
        self.fields['add_amount'].required = False  # fee auto-filled

        # trxid & slip must be present
        for name in ("add_trxid", "add_slip"):
            if name in self.fields:
                self.fields[name].required = True
                self.fields[name].widget.attrs["required"] = "required"

        # Lock session for students (disabled in UI, enforced in clean)
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
                self._locked_session = default_sess

        # ---- Style widgets smartly ----
        for name, field in self.fields.items():
            w = field.widget
            css = w.attrs.get('class', '')
            if isinstance(w, (forms.Select, forms.SelectMultiple)):
                if 'form-select' not in css:
                    w.attrs['class'] = (css + ' form-select').strip()
            else:
                if 'form-control' not in css and not isinstance(w, forms.CheckboxInput):
                    w.attrs['class'] = (css + ' form-control').strip()

        # Ensure explicit ids for JS
        self.fields['add_session'].widget.attrs.setdefault('id', 'id_add_session')
        self.fields['add_amount'].widget.attrs.setdefault('id', 'id_add_amount')

        # Checkbox widget for address_same (not required)
        if 'add_address_same' in self.fields:
            self.fields['add_address_same'].widget = forms.CheckboxInput(
                attrs={'class': 'switch-input', 'id': 'id_add_address_same'}
            )

        # Placeholders (nice-to-have)
        placeholders = {
            'add_name': 'Enter your name in English',
            'add_mobile': '01XXXXXXXXX',
            'add_parent_service': 'Guardian Occupation',
            'add_parent_income': 'Monthly Income',
            'add_trxid': 'Transaction ID',
            'add_slip': 'Payment Mobile Number',
            'add_ssc_roll': 'SSC Roll Number',
            'add_ssc_reg': 'SSC Registration No',
            'add_ssc_passyear': 'e.g. 2022',
            'add_birthdate': 'YYYY-MM-DD',
            'add_father_birthdate': 'YYYY-MM-DD',
            'add_mother_birthdate': 'YYYY-MM-DD',
        }
        for name, ph in placeholders.items():
            if name in self.fields:
                self.fields[name].widget.attrs.setdefault('placeholder', ph)

        # Student mobile autofill + readonly
        if getattr(self.user, 'is_authenticated', False) and getattr(self.user, 'role', None) == 'student':
            phone = getattr(self.user, 'phone_number', '') or ''
            if phone and not self.initial.get('add_mobile'):
                self.fields['add_mobile'].initial = phone
            self.fields['add_mobile'].widget.attrs['readonly'] = 'readonly'

    # ----------------- Clean Methods -----------------

    def clean_add_session(self):
        if getattr(self.user, 'is_authenticated', False) and getattr(self.user, 'role', None) == 'student':
            if getattr(self, '_locked_session', None):
                return self._locked_session
        return self.cleaned_data.get('add_session')

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

    def clean_add_parent_income(self):
        income = self.cleaned_data.get('add_parent_income')
        if income is None or income == '':
            raise ValidationError("অভিভাবকের মাসিক আয় প্রয়োজন।")
        try:
            if int(income) <= 0:
                raise ValidationError("মাসিক আয় শূন্যের চেয়ে বেশি হতে হবে।")
        except (TypeError, ValueError):
            raise ValidationError("মাসিক আয় সঠিক সংখ্যা দিন।")
        return income

    def clean_add_class_roll(self):
        roll = self.cleaned_data.get('add_class_roll')
        if roll is None or roll == '':
            return roll
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
                "readonly": "readonly", "id": "id_add_amount"
            }),
            "add_birthdate": forms.DateInput(attrs={
                "type": "date", "placeholder": "YYYY-MM-DD"
            }),
            "add_father_birthdate": forms.DateInput(attrs={
                "type": "date", "placeholder": "YYYY-MM-DD"
            }),
            "add_mother_birthdate": forms.DateInput(attrs={
                "type": "date", "placeholder": "YYYY-MM-DD"
            }),
            "add_photo": ClearableFileInput(),
            "add_ssc_roll": forms.NumberInput(),
            "add_ssc_reg": forms.NumberInput(),
            "add_ssc_passyear": forms.NumberInput(),
            "add_birth_certificate_no": forms.TextInput(),
            "add_father_nid": forms.TextInput(),
            "add_mother_nid": forms.TextInput(),
            "add_parent_nid": forms.TextInput(),
            "add_postal": forms.NumberInput(),
            "add_postal_per": forms.NumberInput(),
            "add_parent_income": forms.NumberInput(),
            "merit_position": forms.NumberInput(),
            "add_class_roll": forms.NumberInput(),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        self.user = kwargs.pop("user", getattr(self.request, "user", None))
        super().__init__(*args, **kwargs)

        # ---------- Existing required ----------
        self.fields['add_name'].required = True
        self.fields['add_name'].error_messages['required'] = "নাম প্রয়োজন।"

        self.fields['add_ssc_roll'].required = True
        self.fields['add_ssc_roll'].error_messages['required'] = "SSC রোল প্রয়োজন।"

        self.fields['add_parent_service'].required = True
        self.fields['add_parent_service'].error_messages['required'] = "অভিভাবকের পেশা প্রয়োজন।"

        self.fields['add_parent_income'].required = True
        self.fields['add_parent_income'].error_messages['required'] = "অভিভাবকের মাসিক আয় প্রয়োজন।"

        # ---------- Bulk required (full list) ----------
        required_map = {
            # Personal
            'add_name': "নাম প্রয়োজন।",
            'add_age': "বয়স প্রয়োজন।",
            'add_birthdate': "জন্মতারিখ প্রয়োজন।",
            'add_marital_status': "বৈবাহিক অবস্থা প্রয়োজন।",
            'add_birth_certificate_no': "জন্ম নিবন্ধন নম্বর প্রয়োজন।",
            'add_gender': "লিঙ্গ নির্বাচন করুন।",
            'add_nationality': "জাতীয়তা প্রয়োজন।",
            'add_religion': "ধর্ম নির্বাচন করুন।",

            # Father / Mother
            'add_father': "পিতার নাম প্রয়োজন।",
            'add_father_mobile': "পিতার মোবাইল প্রয়োজন।",
            'add_father_nid': "পিতার NID প্রয়োজন।",
            'add_father_birthdate': "পিতার জন্মতারিখ প্রয়োজন।",
            'add_mother': "মাতার নাম প্রয়োজন।",

            # Guardian
            'add_parent_select': "অভিভাবক নির্বাচন করুন।",
            'add_parent': "অভিভাবকের নাম প্রয়োজন।",
            'add_parent_mobile': "অভিভাবকের মোবাইল প্রয়োজন।",
            'add_parent_relation': "অভিভাবকের সম্পর্ক প্রয়োজন।",
            'add_parent_service': "অভিভাবকের পেশা প্রয়োজন।",
            'add_parent_income': "অভিভাবকের মাসিক আয় প্রয়োজন।",

            # Present address
            'add_village': "বর্তমান গ্রাম প্রয়োজন।",
            'add_post': "বর্তমান ডাকঘর প্রয়োজন।",
            'add_police': "বর্তমান থানা/উপজেলা প্রয়োজন।",
            'add_postal': "বর্তমান পোস্টকোড প্রয়োজন।",
            'add_distric': "বর্তমান জেলা প্রয়োজন।",

            # Permanent address
            'add_village_per': "স্থায়ী গ্রাম প্রয়োজন।",
            'add_post_per': "স্থায়ী ডাকঘর প্রয়োজন।",
            'add_police_per': "স্থায়ী থানা/উপজেলা প্রয়োজন।",
            'add_postal_per': "স্থায়ী পোস্টকোড প্রয়োজন।",
            'add_distric_per': "স্থায়ী জেলা প্রয়োজন।",

            # SSC
            'add_ssc_roll': "SSC রোল প্রয়োজন।",
            'add_ssc_reg': "SSC রেজিস্ট্রেশন নম্বর প্রয়োজন।",
            'add_ssc_session': "SSC সেশন প্রয়োজন।",
            'add_ssc_institute': "SSC ইনস্টিটিউট প্রয়োজন।",
            'add_ssc_gpa': "SSC GPA প্রয়োজন।",
            'add_ssc_group': "SSC গ্রুপ নির্বাচন করুন।",
            'add_ssc_board': "SSC বোর্ড নির্বাচন করুন।",
            'add_ssc_passyear': "SSC পাশের বছর প্রয়োজন।",
        }
        for fname, msg in required_map.items():
            if fname in self.fields:
                self.fields[fname].required = True
                self.fields[fname].error_messages['required'] = msg

        # Quota name only when qouta is True
        if 'qouta_name' in self.fields:
            want_quota = None
            if self.data:
                qkey = self.add_prefix('qouta')
                want_quota = self.data.get(qkey) in ('True', 'true', '1', 'on', 'yes')
            elif self.instance and getattr(self.instance, 'qouta', False):
                want_quota = True
            self.fields['qouta_name'].required = bool(want_quota)
            if want_quota:
                self.fields['qouta_name'].error_messages['required'] = "কোটা নাম প্রয়োজন।"

        # Photo: new → required, edit → optional
        if not self.instance.pk or (self.instance.pk and not getattr(self.instance, 'add_photo', None)):
            self.fields['add_photo'].required = True
            self.fields['add_photo'].error_messages['required'] = "ফটো আপলোড করা প্রয়োজন।"
        else:
            self.fields['add_photo'].required = False

        # ---- Session field ----
        self.fields["add_session"].required = True
        self.fields["add_session"].widget.attrs.setdefault("id", "id_add_session")

        # Fee auto-filled by JS
        self.fields["add_amount"].required = False

        # Students: payment fields required; staff: optional
        is_student = getattr(self.user, "is_authenticated", False) and getattr(self.user, "role", None) == "student"
        for name in ("add_trxid", "add_slip", "add_payment_method"):
            if name in self.fields:
                self.fields[name].required = is_student
                if is_student:
                    self.fields[name].widget.attrs["required"] = "required"

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
                    "class": "form-select",
                    "style": "pointer-events:none;background:#f8f9fa;",
                    "data-locked": "1",
                })
                self._locked_session = locked

        # ---- Style widgets ----
        for name, field in self.fields.items():
            w = field.widget
            css = w.attrs.get("class", "")
            if isinstance(w, (forms.Select, forms.SelectMultiple)):
                if "form-select" not in css:
                    w.attrs["class"] = (css + " form-select").strip()
            elif not isinstance(w, forms.CheckboxInput):
                if "form-control" not in css:
                    w.attrs["class"] = (css + " form-control").strip()

        # Checkbox widget for address_same
        if "add_address_same" in self.fields:
            self.fields["add_address_same"].widget = forms.CheckboxInput(
                attrs={"class": "switch-input", "id": "id_add_address_same"}
            )

        # Placeholders (optional)
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
            "add_photo": "Upload Photo (Required)",
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

        # Student: autofill + readonly mobile
        if is_student:
            phone = getattr(self.user, "phone_number", "") or ""
            if phone and not self.initial.get("add_mobile"):
                self.fields["add_mobile"].initial = phone
            self.fields["add_mobile"].widget.attrs["readonly"] = "readonly"

    # ----------------- CLEAN METHODS -----------------

    def clean_add_session(self):
        if getattr(self.user, "is_authenticated", False) and getattr(self.user, "role", None) == "student":
            if getattr(self, "_locked_session", None):
                return self._locked_session
        return self.cleaned_data.get("add_session")

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

    def clean_add_parent_income(self):
        income = self.cleaned_data.get('add_parent_income')
        if income in (None, ""):
            raise ValidationError("অভিভাবকের মাসিক আয় প্রয়োজন।")
        try:
            if int(income) <= 0:
                raise ValidationError("মাসিক আয় শূন্যের চেয়ে বেশি হতে হবে।")
        except (TypeError, ValueError):
            raise ValidationError("মাসিক আয় সঠিক সংখ্যা দিন।")
        return income

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
        if roll is None or roll == '':
            return roll
        group = getattr(self.instance, "add_admission_group", None) or "arts"
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


# Subject wise studentt data

class CustomModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        # Show sub_name and "All" if group is None or empty, otherwise show the group display name
        group_display = "All" if not obj.group else obj.get_group_display()
        return f"{obj.sub_name} ({group_display})"

class SubjectFilterForm(forms.Form):
    subject = CustomModelChoiceField(
        queryset=Subjects.objects.filter(sub_status="active").order_by("group", "sub_name"),
        required=False,
        empty_label="— Select a subject —",
        label="Subject",
        to_field_name="id",
    )
