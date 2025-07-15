from django import forms
from apps.admissions.models import HscAdmissions, Fee

from django.core.exceptions import ValidationError
import re

# 🔹 Global validator
# def validate_mobile_number(mobile: str, field_label: str = "মোবাইল"):
#     if not mobile:
#         return mobile
#     if not re.match(r'^01\d{9}$', mobile):
#         raise ValidationError(f"{field_label} অবশ্যই ১১ সংখ্যার হতে হবে এবং '01' দিয়ে শুরু হতে হবে।")
#     return mobile

def validate_mobile_number(mobile: str, field_label: str = "মোবাইল"):
    if not mobile:
        return mobile

    mobile = str(mobile).strip()  # 🟢 Force string
    if not re.match(r'^01\d{9}$', mobile):
        raise ValidationError(f"{field_label} অবশ্যই ১১ সংখ্যার হতে হবে এবং '01' দিয়ে শুরু হতে হবে।")
    return mobile



class HscAdmissionForm(forms.ModelForm):
    class Meta:
        model = HscAdmissions
        exclude = ['add_program', 'add_admission_group']
        widgets = {
            'add_amount': forms.NumberInput(attrs={
                'readonly': 'readonly',
                'class': 'form-control',
                'id': 'id_add_amount'
            }),
            'add_birthdate': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'placeholder': 'YYYY-MM-DD'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Styling
        for field_name, field in self.fields.items():
            field.widget.attrs.setdefault('class', 'form-control')



        # Required setup
        self.fields['add_session'].required = True
        self.fields['add_amount'].required = False
        self.fields['add_session'].widget.attrs['id'] = 'id_add_session'
        self.fields['add_photo'].required = True


        # Placeholders
        placeholders = {
            'add_name': 'Enter your name in English',
            'add_name_bangla': 'বাংলায় নাম লিখুন',
            'add_mobile': '01XXXXXXXXX',
            'add_father': 'Father\'s Name (English)',
            'add_father_bangla': 'পিতার নাম',
            'add_father_mobile': 'Father\'s Mobile Number',
            'add_mother': 'Mother\'s Name (English)',
            'add_mother_bangla': 'মাতার নাম',
            'add_mother_mobile': 'Mother\'s Mobile Number',
            'add_parent': 'Guardian\'s Name',
            'add_parent_relation': 'Guardian Relation (e.g. Uncle)',
            'add_parent_mobile': 'Guardian\'s Mobile',
            'add_parent_service': 'Guardian Occupation',
            'add_parent_income': 'Monthly Income',
            'add_parent_land_agri': 'Agricultural Land in Decimal',
            'add_parent_land_nonagri': 'Non-Agricultural Land',
            'add_village': 'Present Village',
            'add_post': 'Present Post Office',
            'add_upojella': 'Present Upazila',
            'add_distric': 'Present District',
            'add_village_per': 'Permanent Village',
            'add_post_per': 'Permanent Post Office',
            'add_upojella_per': 'Permanent Upazila',
            'add_distric_per': 'Permanent District',
            'add_birth_certificate_no': '17-digit Birth Certificate No',
            'add_nationality': 'e.g. Bangladeshi',
            'add_ssc_roll': 'SSC Roll Number',
            'add_ssc_reg': 'SSC Registration No',
            'add_ssc_session': 'e.g. 2020-21',
            'add_ssc_gpa': 'SSC GPA (e.g. 5.00)',
            'add_ssc_board': 'e.g. Dhaka',
            'add_ssc_passyear': 'e.g. 2022',
            'add_trxid': 'Transaction ID',
            'add_slip': 'Your Note',
            'add_class_roll': 'HSC Class Roll',
        }

        for field_name, text in placeholders.items():
            if field_name in self.fields:
                self.fields[field_name].widget.attrs['placeholder'] = text

    # ✅ Field-wise mobile validation
    def clean_add_mobile(self):
        return validate_mobile_number(self.cleaned_data.get('add_mobile'), "আপনার মোবাইল")

    def clean_add_father_mobile(self):
        return validate_mobile_number(self.cleaned_data.get('add_father_mobile'), "পিতার মোবাইল")

    def clean_add_mother_mobile(self):
        return validate_mobile_number(self.cleaned_data.get('add_mother_mobile'), "মাতার মোবাইল")

    def clean_add_parent_mobile(self):
        return validate_mobile_number(self.cleaned_data.get('add_parent_mobile'), "অভিভাবকের মোবাইল")




# Arts Admission Form
class ArtsAdmissionForm(forms.ModelForm):
    class Meta:
        model = HscAdmissions
        exclude = ['add_program', 'add_admission_group']
        widgets = {
            'add_amount': forms.NumberInput(attrs={
                'readonly': 'readonly',
                'class': 'form-control',
                'id': 'id_add_amount'
            }),
            'add_birthdate': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'placeholder': 'YYYY-MM-DD'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # All fields styling
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')

        # Required and placeholder setup — like your existing logic
        self.fields['add_session'].required = True
        self.fields['add_amount'].required = False
        self.fields['add_photo'].required = True


        self.fields['add_session'].widget.attrs['id'] = 'id_add_session'

        # You can add placeholder for optional_subject and optional_subject_2 as well
        self.fields['optional_subject'].widget.attrs['placeholder'] = 'Select Optional Subject'
        self.fields['optional_subject_2'].widget.attrs['placeholder'] = 'Select Optional Subject 2'

        # ✅ Placeholders
        placeholders = {
            'add_name': 'Enter your name in English',
            'add_name_bangla': 'বাংলায় নাম লিখুন',
            'add_mobile': '01XXXXXXXXX',
            'add_father': 'Father\'s Name (English)',
            'add_father_bangla': 'পিতার নাম',
            'add_father_mobile': 'Father\'s Mobile Number',
            'add_mother': 'Mother\'s Name (English)',
            'add_mother_bangla': 'মাতার নাম',
            'add_mother_mobile': 'Mother\'s Mobile Number',
            'add_parent': 'Guardian\'s Name',
            'add_parent_relation': 'Guardian Relation (e.g. Uncle)',
            'add_parent_mobile': 'Guardian\'s Mobile',
            'add_parent_service': 'Guardian Occupation',
            'add_parent_income': 'Monthly Income',
            'add_parent_land_agri': 'Agricultural Land in Decimal',
            'add_parent_land_nonagri': 'Non-Agricultural Land',
            'add_village': 'Present Village',
            'add_post': 'Present Post Office',
            'add_upojella': 'Present Upazila',
            'add_distric': 'Present District',
            'add_village_per': 'Permanent Village',
            'add_post_per': 'Permanent Post Office',
            'add_upojella_per': 'Permanent Upazila',
            'add_distric_per': 'Permanent District',
            'add_birth_certificate_no': '17-digit Birth Certificate No',
            'add_nationality': 'e.g. Bangladeshi',
            'add_ssc_roll': 'SSC Roll Number',
            'add_ssc_reg': 'SSC Registration No',
            'add_ssc_session': 'e.g. 2020-21',
            'add_ssc_gpa': 'SSC GPA (e.g. 5.00)',
            'add_ssc_board': 'e.g. Dhaka',
            'add_ssc_passyear': 'e.g. 2022',
            'add_trxid': 'Transaction ID',
            'add_slip': 'Your Note',
            'add_class_roll': 'HSC Class Roll',
        }

        for field_name, text in placeholders.items():
            if field_name in self.fields:
                self.fields[field_name].widget.attrs['placeholder'] = text

    # ✅ Field-wise mobile validation
    def clean_add_mobile(self):
        return validate_mobile_number(self.cleaned_data.get('add_mobile'), "আপনার মোবাইল")

    def clean_add_father_mobile(self):
        return validate_mobile_number(self.cleaned_data.get('add_father_mobile'), "পিতার মোবাইল")

    def clean_add_mother_mobile(self):
        return validate_mobile_number(self.cleaned_data.get('add_mother_mobile'), "মাতার মোবাইল")

    def clean_add_parent_mobile(self):
        return validate_mobile_number(self.cleaned_data.get('add_parent_mobile'), "অভিভাবকের মোবাইল")


# Degree/ honors form
from .models import DegreeAdmission

class DegreeAdmissionForm(forms.ModelForm):
    class Meta:
        model = DegreeAdmission
        exclude = ['add_program', 'add_admission_group']
        widgets = {
            'add_birthdate': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'placeholder': 'YYYY-MM-DD'
            }),
            'add_amount': forms.NumberInput(attrs={
                'readonly': 'readonly',
                'class': 'form-control',
                'id': 'id_add_amount'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ✅ Bootstrap style for all fields
        for field_name, field in self.fields.items():
            field.widget.attrs.setdefault('class', 'form-control')

        # ✅ Required field control
        self.fields['add_session'].required = True
        self.fields['add_amount'].required = False
        self.fields['subjects'].required = False
        self.fields['main_subject'].required = False
        self.fields['add_photo'].required = True


        # ✅ ID for session field (for JS)
        self.fields['add_session'].widget.attrs['id'] = 'id_add_session'

        # ✅ Placeholders
        placeholders = {
            'add_name': 'Enter your name in English',
            'add_name_bangla': 'বাংলায় নাম লিখুন',
            'add_mobile': '01XXXXXXXXX',
            'add_father': 'Father\'s Name (English)',
            'add_father_bangla': 'পিতার নাম',
            'add_father_mobile': 'Father\'s Mobile Number',
            'add_mother': 'Mother\'s Name (English)',
            'add_mother_bangla': 'মাতার নাম',
            'add_mother_mobile': 'Mother\'s Mobile Number',
            'add_parent': 'Guardian\'s Name',
            'add_parent_relation': 'Guardian Relation (e.g. Uncle)',
            'add_parent_mobile': 'Guardian\'s Mobile',
            'add_parent_service': 'Guardian Occupation',
            'add_parent_income': 'Monthly Income',
            'add_parent_land_agri': 'Agricultural Land in Decimal',
            'add_parent_land_nonagri': 'Non-Agricultural Land',
            'add_village': 'Present Village',
            'add_post': 'Present Post Office',
            'add_upojella': 'Present Upazila',
            'add_distric': 'Present District',
            'add_village_per': 'Permanent Village',
            'add_post_per': 'Permanent Post Office',
            'add_upojella_per': 'Permanent Upazila',
            'add_distric_per': 'Permanent District',
            'add_birth_certificate_no': '17-digit Birth Certificate No',
            'add_nationality': 'e.g. Bangladeshi',
            'add_ssc_roll': 'SSC Roll Number',
            'add_ssc_reg': 'SSC Registration No',
            'add_ssc_session': 'e.g. 2020-21',
            'add_ssc_gpa': 'SC GPA (e.g. 5.00)',
            'add_ssc_board': 'e.g. Dhaka',
            'add_ssc_passyear': 'e.g. 2022',
            'add_hsc_roll': 'HSC Roll Number',
            'add_hsc_reg': 'HSC Registration No',
            'add_hsc_session': 'e.g. 2020-21',
            'add_hsc_gpa': 'HSC GPA (e.g. 5.00)',
            'add_hsc_board': 'e.g. Dhaka',
            'add_hsc_passyear': 'e.g. 2022',
            'add_trxid': 'Transaction ID',
            'add_slip': 'Your Note',
            'add_class_roll': 'Class Roll',
        }

        for field_name, text in placeholders.items():
            if field_name in self.fields:
                self.fields[field_name].widget.attrs['placeholder'] = text




    # ✅ Field-wise mobile validation
    def clean_add_mobile(self):
        return validate_mobile_number(self.cleaned_data.get('add_mobile'), "আপনার মোবাইল")

    def clean_add_father_mobile(self):
        return validate_mobile_number(self.cleaned_data.get('add_father_mobile'), "পিতার মোবাইল")

    def clean_add_mother_mobile(self):
        return validate_mobile_number(self.cleaned_data.get('add_mother_mobile'), "মাতার মোবাইল")

    def clean_add_parent_mobile(self):
        return validate_mobile_number(self.cleaned_data.get('add_parent_mobile'), "অভিভাবকের মোবাইল")




class FeeForm(forms.ModelForm):
    class Meta:
        model = Fee
        fields = ['fee_session', 'fee_program', 'fee_group', 'amount']
        widgets = {
            'fee_session': forms.Select(attrs={'class': 'form-control'}),
            'fee_program': forms.Select(attrs={'class': 'form-control'}),
            'fee_group': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        session = cleaned_data.get('fee_session')
        program = cleaned_data.get('fee_program')
        group = cleaned_data.get('fee_group')

        if Fee.objects.filter(fee_session=session, fee_program=program, fee_group=group).exists():
            raise ValidationError("This fee combination already exists.")






# Global session filter form
from .models import Session

class SessionSelectForm(forms.Form):
    session = forms.ModelChoiceField(
        queryset=Session.objects.all(),
        required=True,
        empty_label="Select Session"
    )
