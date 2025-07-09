from django import forms
from apps.admissions.models import HscAdmissions, Fee

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

        # ✅ Bootstrap styling for all fields
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'

        # ✅ Ensure required fields are properly set
        self.fields['add_session'].required = True
        self.fields['add_amount'].required = False

        # ✅ Most important fix: set ID for JavaScript to detect
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
