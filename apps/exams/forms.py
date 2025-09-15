from django import forms
from apps.admissions.models import Programs
from .models import Subject

class SubjectForm(forms.ModelForm):
    program = forms.ModelMultipleChoiceField(
        label="Programs",
        queryset=Programs.objects.filter(pro_status='active'),  
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
    )

    class Meta:
        model = Subject
        fields = ['name', 'code', 'program', 'group_name', 'status']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'group_name': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            self.fields['program'].initial = self.instance.program.all()



from .models import Exam

class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = ['exam_name', 'exam_class', 'group_name', 'exam_session', 'exam_start_date', 'exam_end_date', 'subjects']
        widgets = {
            'exam_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter exam name'}),
            'exam_class': forms.Select(attrs={'class': 'form-select'}),
            'group_name': forms.Select(attrs={'class': 'form-select'}),
            'exam_session': forms.Select(attrs={'class': 'form-select'}),
            'exam_start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'exam_end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'subjects': forms.SelectMultiple(attrs={'class': 'form-select'}),
        }



        

# from .models import AdmitBack

# class AdmitBackForm(forms.ModelForm):
#     class Meta:
#         model = AdmitBack
#         fields = ['admit_card']
#         widgets = {
#             'admit_card': forms.Textarea(attrs={'class': 'form-control', 'rows': 4})
#         }







# # apps/exam/forms.py
# from django import forms
from .models import SubjectMark

class SubjectMarkForm(forms.ModelForm):
    class Meta:
        model = SubjectMark
        fields = ['cq_mark', 'mcq_mark', 'practical_mark', 'ct_mark']
        widgets = {
            'cq_mark': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'CQ'}),
            'mcq_mark': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'MCQ'}),
            'practical_mark': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Practical'}),
            'ct_mark': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'CT'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].required = False  # ✅ Make all fields optional
