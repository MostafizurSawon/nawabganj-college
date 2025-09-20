from django.db import models
from apps.admissions.models import HscAdmissions, Programs, Session
# from django.contrib.contenttypes.models import ContentType
# from django.contrib.contenttypes.fields import GenericForeignKey
# from decimal import Decimal, ROUND_HALF_UP
# from collections import defaultdict

# # ==============================
# # Exams app models
# # ==============================

# class SchoolClass(models.Model):
#     name = models.CharField(max_length=50)

#     def __str__(self):
#         return self.name

class Subject(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True)
    code = models.CharField(max_length=20, blank=True, null=True)
    program = models.ManyToManyField(Programs, related_name='subjects_by_program', blank=True)
    group_name = models.CharField(
    max_length=20,
    choices=[
        ('all', 'All'),
        ('science', 'Science'),
        ('humanities', 'Humanities'),
        ('business', 'Business Studies'),
    ],
    blank=True,
    null=True,
    default='all'
)


    status = models.CharField(max_length=15, choices=[
        ('active', 'Active'),
        ('inactive', 'Inactive')
    ],blank=True, null=True)

    class Meta:
        ordering = ['name', 'code']   # ✅ subject list stable থাকে

    # def label(self):
    #     return f"{self.name} ({self.code})" if self.code else f"{self.name or ''}".strip()

    def __str__(self):
        return f"{self.name} ({self.code})" if self.code else f"{self.name or ''}".strip()

# class AcademicYear(models.Model):
#     name = models.CharField(max_length=20, unique=True)

#     def __str__(self):
#         return self.name

# # Grading scheme choices
# class GradingScheme(models.TextChoices):
#     JUNIOR = 'junior', 'Junior (Class 6–8)'
#     NINE_SCIENCE = 'nine_science', 'Class 9 – Science'
#     NINE_HUMANITIES = 'nine_arts', 'Class 9 – Humanities'
#     NINE_BUSINESS = 'nine_business', 'Class 9 – Business'
#     TEN_SCIENCE = 'ten_science', 'Class 10 – Science'
#     TEN_HUMANITIES = 'ten_arts', 'Class 10 – Humanities'
#     TEN_BUSINESS = 'ten_business', 'Class 10 – Business'

# class GradingScheme(models.TextChoices):
#     SCIENCE = 'hsc_science', 'Class 9 – Science'
#     HUMANITIES = 'hsc_arts', 'Class 9 – Humanities'
#     BUSINESS = 'hsc_business', 'Class 9 – Business'

# Hsc
class Exam(models.Model):
    exam_name = models.CharField(max_length=150)
    exam_class = models.ForeignKey(Programs, on_delete=models.CASCADE)
    group_name = models.CharField(max_length=20, choices=[
        ('science', 'Science'),
        ('humanities', 'Humanities'),
        ('business', 'Business Studies'),
    ], null=True, blank= True)
    exam_session = models.ForeignKey(Session, on_delete=models.CASCADE)
    exam_start_date = models.DateField()
    exam_end_date = models.DateField()


    subjects = models.ManyToManyField('Subject', through='ExamSubject', related_name='exam_subjects')

    # grading_scheme = models.CharField(
    #     max_length=20,
    #     choices=GradingScheme.choices,
    #     default=GradingScheme.SCIENCE,
    #     help_text="Select the grading scheme used to calculate GPA/grade for this exam."
    # )

    def save(self, *args, **kwargs):
        class_name = (self.exam_class.pro_name or "").strip().lower()
        group_name = (self.group_name or "").strip().lower() if self.group_name else ""

        # scheme = GradingScheme.SCIENCE  # default (6–8)

        # if class_name in {"9", "nine"}:
        #     if group_name == "science":
        #         scheme = GradingScheme.NINE_SCIENCE
        #     elif group_name in {"humanities", "arts"}:
        #         scheme = GradingScheme.NINE_HUMANITIES
        #     elif group_name == "business studies":
        #         scheme = GradingScheme.NINE_BUSINESS

        # elif class_name in {"10", "ten"}:
        #     if group_name == "science":
        #         scheme = GradingScheme.TEN_SCIENCE
        #     elif group_name in {"humanities", "arts"}:
        #         scheme = GradingScheme.TEN_HUMANITIES
        #     elif group_name == "business studies":
        #         scheme = GradingScheme.TEN_BUSINESS

        # self.grading_scheme = scheme
        super().save(*args, **kwargs)


    def __str__(self):
        return f"{self.exam_name} - {self.exam_class.pro_name}"

    class Meta:
        ordering = ['-id']   # ✅ newest first (pagination stable)

    # Lightweight validation (form.save() বা admin clean-এও কাজ করবে)
    def clean(self):
        from django.core.exceptions import ValidationError
        # session & class দুটোই থাকতে হবে
        if not self.exam_session_id or not self.exam_class_id:
            raise ValidationError("Exam session এবং exam class দুটোই সেট করতে হবে।")
        # তারিখ উল্টো হলে আটকাও
        if self.exam_start_date and self.exam_end_date and self.exam_start_date > self.exam_end_date:
            raise ValidationError("Exam start date শেষ তারিখের পরে হতে পারে না।")

# class AdmitBack(models.Model):
#     admit_card = models.TextField(null=True, blank=True)

class ExamSubject(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

    # Total Marks
    full_marks = models.PositiveIntegerField(default=0)
    pass_marks = models.PositiveIntegerField(default=0)

    # Component-wise Marks
    cq_marks = models.PositiveIntegerField(null=True, blank=True)
    cq_pass_marks = models.PositiveIntegerField(null=True, blank=True)
    mcq_marks = models.PositiveIntegerField(null=True, blank=True)
    mcq_pass_marks = models.PositiveIntegerField(null=True, blank=True)
    practical_marks = models.PositiveIntegerField(null=True, blank=True)
    practical_pass_marks = models.PositiveIntegerField(null=True, blank=True)
    ct_marks = models.PositiveIntegerField(null=True, blank=True)
    ct_pass_marks = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.exam.exam_name} | {self.subject.name}"




# College Exam Record
from apps.admissions.models import HscAdmissions

class ExamRecord(models.Model):
    exam = models.ForeignKey('Exam', on_delete=models.CASCADE, related_name='records')
    hsc_student = models.ForeignKey(HscAdmissions, on_delete=models.CASCADE, related_name='exam_records')

    # ফলাফল ক্ষেত্রগুলো এখন খালি রাখছি; পরে calculation চালু করলে ব্যবহার করব
    total_marks = models.FloatField(null=True, blank=True)
    grade = models.CharField(max_length=5, null=True, blank=True)
    gpa = models.FloatField(null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)

    class Meta:
        unique_together = ('exam', 'hsc_student')  # ডুপ্লিকেট গার্ড
        indexes = [
            models.Index(fields=['exam']),
            models.Index(fields=['hsc_student']),
        ]

    def __str__(self):
        return f"{self.hsc_student.add_name} → {self.exam.exam_name}"




# # ============================== #
# # ExamRecord model (per student) #
# # ============================== #
# from collections import defaultdict
# from decimal import Decimal, ROUND_HALF_UP


# class ExamRecord(models.Model):
#     exam = models.ForeignKey('Exam', on_delete=models.CASCADE)

#     student_content_type = models.ForeignKey(
#         ContentType, on_delete=models.CASCADE, null=True, blank=True
#     )
#     student_object_id = models.PositiveIntegerField(null=True, blank=True)
#     student = GenericForeignKey('student_content_type', 'student_object_id')

#     total_marks = models.FloatField(null=True, blank=True)
#     grade = models.CharField(max_length=5, null=True, blank=True)
#     gpa = models.FloatField(null=True, blank=True)
#     remarks = models.TextField(null=True, blank=True)

#     # --- Cached breakdown fields (optional-aware) ---
#     base_gpa_no_optional = models.FloatField(null=True, blank=True)
#     base_grade_no_optional = models.CharField(max_length=5, null=True, blank=True)

#     optional_subject_label = models.CharField(max_length=64, null=True, blank=True)
#     optional_gp_raw = models.FloatField(null=True, blank=True)
#     optional_gp_adjusted = models.FloatField(null=True, blank=True)

#     mandatory_gp_sum = models.FloatField(null=True, blank=True)
#     mandatory_count = models.PositiveSmallIntegerField(null=True, blank=True)

#     final_total_gp = models.FloatField(null=True, blank=True)
#     final_gpa_raw = models.FloatField(null=True, blank=True)

#     calc_meta = models.JSONField(default=dict, blank=True)

#     def __str__(self):
#         return f"{self.student} - {self.exam.exam_name}"

#     # ---------- Helpers ----------
#     def get_grade_by_percentage(self, mark, full_mark):
#         percentage = (mark / full_mark) * 100 if full_mark else 0
#         if percentage >= 80: return "A+"
#         elif percentage >= 70: return "A"
#         elif percentage >= 60: return "A-"
#         elif percentage >= 50: return "B"
#         elif percentage >= 40: return "C"
#         elif percentage >= 33: return "D"
#         return "F"

#     def get_point_by_percentage(self, percentage):
#         if percentage >= 80: return 5.0
#         elif percentage >= 70: return 4.0
#         elif percentage >= 60: return 3.5
#         elif percentage >= 50: return 3.0
#         elif percentage >= 40: return 2.0
#         elif percentage >= 33: return 1.0
#         return 0.0

#     def get_grade_by_gpa(self, gpa):
#         if gpa >= 5.0: return "A+"
#         elif gpa >= 4.0: return "A"
#         elif gpa >= 3.5: return "A-"
#         elif gpa >= 3.0: return "B"
#         elif gpa >= 2.0: return "C"
#         elif gpa >= 1.0: return "D"
#         return "F"

#     def get_full_marks_map(self):
#         from .models import ExamSubject
#         return {es.subject_id: es.full_marks for es in ExamSubject.objects.filter(exam=self.exam)}

#     # ---------- Core calculation ----------
#     def calculate_total_and_grade(self):
#         """
#         Computes total marks, GPA, grade and remarks for this ExamRecord.

#         NINE_SCIENCE: optional = student's chosen 'fourth' (valid হলে), adjusted = gp-2 (>1 হলে)
#         NINE_BUSINESS: optional = fixed 'Agriculture' (থাকলে), adjusted = gp-2 (>1 হলে)
#         Others: standard average GPA with component-wise pass rules.
#         """
#         from .models import SubjectMark, GradingScheme  # avoid circulars
#         scheme = getattr(self.exam, 'grading_scheme', None)

#         # ---------- Class 9 (Science) ----------
#         if scheme == GradingScheme.NINE_SCIENCE or scheme == GradingScheme.TEN_SCIENCE:
#             # --------- BEGIN: NINE_SCIENCE implementation ----------
#             SubjectMark = self.subjectmark_set.model
#             subject_marks = self.subjectmark_set.select_related("subject").all()
#             if not subject_marks.exists():
#                 self._reset_no_marks()
#                 return

#             exam_subjects = {es.subject_id: es for es in self.exam.examsubject_set.all()}
#             full_marks_map = self.get_full_marks_map()

#             exam_subj_list = list(self.exam.subjects.all())
#             name_to_id = { (s.name or "").strip().lower(): s.id for s in exam_subj_list }
#             code_to_id = { str(s.code).strip(): s.id for s in exam_subj_list if s.code }
#             id_to_name = { s.id: (s.name or "") for s in exam_subj_list }

#             fixed_names = {
#                 "mathematics","bangladesh and global studies","ict","religion","physics","chemistry",
#             }
#             fixed_ids = { name_to_id[n] for n in fixed_names if n in name_to_id }

#             combined_papers_norm = {
#                 "Bangla": {"bangla 1st paper","bangla 2nd paper"},
#                 "English": {"english 1st paper","english 2nd paper"},
#             }

#             def _is_combined_subject_id(subj_id: int) -> bool:
#                 nm = (id_to_name.get(subj_id,"") or "").strip().lower()
#                 return nm in combined_papers_norm["Bangla"] or nm in combined_papers_norm["English"]

#             def _resolve_exam_id_from_adm(adm_sub):
#                 if not adm_sub: return None
#                 nm = (getattr(adm_sub, "sub_name", "") or "").strip().lower()
#                 cd = str(getattr(adm_sub, "code", "") or "").strip()
#                 if nm and nm in name_to_id: return name_to_id[nm]
#                 if cd and cd in code_to_id: return code_to_id[cd]
#                 return None

#             student = self.student
#             main_exam_id = _resolve_exam_id_from_adm(getattr(student, "main_subject", None))
#             fourth_exam_id = _resolve_exam_id_from_adm(getattr(student, "fourth_subject", None))

#             mandatory_id_set = set(fixed_ids)
#             if main_exam_id and main_exam_id not in mandatory_id_set and not _is_combined_subject_id(main_exam_id):
#                 mandatory_id_set.add(main_exam_id)

#             optional_selected_exam_id = fourth_exam_id
#             optional_id_used = fourth_exam_id
#             optional_valid = True
#             if optional_id_used:
#                 if optional_id_used in mandatory_id_set or _is_combined_subject_id(optional_id_used) or (main_exam_id and optional_id_used == main_exam_id):
#                     optional_valid = False
#                     optional_id_used = None

#             grouped_combined = defaultdict(list)
#             single_marks = []
#             for m in subject_marks:
#                 nm_norm = (getattr(m.subject, "name", "") or "").strip().lower()
#                 placed = False
#                 for combo, paper_set in ({"Bangla":{"bangla 1st paper","bangla 2nd paper"},
#                                           "English":{"english 1st paper","english 2nd paper"}}).items():
#                     if nm_norm in paper_set:
#                         grouped_combined[combo].append(m); placed = True; break
#                 if placed: continue
#                 if m.subject_id in mandatory_id_set or (optional_id_used and m.subject_id == optional_id_used):
#                     single_marks.append(m)

#             total_obtained_ex = 0.0; total_full = 0; has_failed_mand = False
#             total_gp_display_mand = 0.0; subject_count_mand = 0
#             per_subject_display_gp = {}

#             for cname, papers in grouped_combined.items():
#                 ex_total = sum((p.total_mark or 0) for p in papers)
#                 full = sum(full_marks_map.get(p.subject.id, 100) for p in papers)
#                 percent_raw = (ex_total / full) * 100 if full else 0.0
#                 gp_disp = self.get_point_by_percentage(percent_raw)
#                 total_gp_display_mand += gp_disp; subject_count_mand += 1
#                 if gp_disp == 0.0: has_failed_mand = True
#                 total_obtained_ex += ex_total; total_full += full

#             optional_selected_gp_display = 0.0
#             for m in single_marks:
#                 full = full_marks_map.get(m.subject.id, 100); ex_total = (m.total_mark or 0)
#                 exam_subject = exam_subjects.get(m.subject_id)
#                 cq = m.cq_mark or 0; mcq = m.mcq_mark or 0; practical = m.practical_mark or 0
#                 failed_component = False
#                 if exam_subject:
#                     failed_component = (
#                         (exam_subject.cq_pass_marks is not None and cq < exam_subject.cq_pass_marks) or
#                         (exam_subject.mcq_pass_marks is not None and mcq < exam_subject.mcq_pass_marks) or
#                         (exam_subject.practical_pass_marks is not None and practical < exam_subject.practical_pass_marks) or
#                         (exam_subject.pass_marks is not None and ex_total < exam_subject.pass_marks)
#                     )
#                 percent_raw = (ex_total / full) * 100 if full else 0.0
#                 gp_disp = 0.0 if failed_component else self.get_point_by_percentage(percent_raw)
#                 grade_disp = "F" if failed_component else self.get_grade_by_percentage(ex_total, full)

#                 m.grade = grade_disp
#                 SubjectMark.objects.filter(pk=m.pk).update(grade=grade_disp)
#                 per_subject_display_gp[m.subject_id] = gp_disp

#                 if m.subject_id in mandatory_id_set:
#                     total_gp_display_mand += gp_disp; subject_count_mand += 1
#                     if failed_component or gp_disp == 0.0: has_failed_mand = True
#                 elif optional_id_used and m.subject_id == optional_id_used:
#                     optional_selected_gp_display = gp_disp

#                 total_obtained_ex += ex_total; total_full += full

#             if optional_selected_exam_id and optional_id_used is None:
#                 optional_selected_gp_display = per_subject_display_gp.get(optional_selected_exam_id, optional_selected_gp_display)

#             if optional_valid and optional_selected_gp_display > 1.0 and optional_id_used is not None:
#                 adjusted_optional = max(optional_selected_gp_display - 2.0, 0.0)
#             else:
#                 adjusted_optional = 0.0

#             final_total_gp = total_gp_display_mand + adjusted_optional
#             final_gpa_raw = (final_total_gp / subject_count_mand) if subject_count_mand > 0 else 0.0
#             final_gpa_capped = 5.0 if final_gpa_raw > 5.0 else final_gpa_raw

#             base_gpa_no_optional = (total_gp_display_mand / subject_count_mand) if subject_count_mand else 0.0
#             self.base_gpa_no_optional = round(base_gpa_no_optional, 2)
#             self.base_grade_no_optional = self.get_grade_by_gpa(base_gpa_no_optional)

#             self.optional_subject_label = f"subject_id:{optional_selected_exam_id}" if optional_selected_exam_id else None
#             self.optional_gp_raw = float(optional_selected_gp_display)
#             self.optional_gp_adjusted = float(adjusted_optional)
#             self.mandatory_gp_sum = float(total_gp_display_mand)
#             self.mandatory_count = int(subject_count_mand)
#             self.final_total_gp = float(final_total_gp)
#             self.final_gpa_raw = float(final_gpa_capped)

#             self.total_marks = total_obtained_ex
#             if has_failed_mand:
#                 self.grade = "F"; self.gpa = 0.0; self.remarks = "Failed"
#             else:
#                 self.gpa = float(Decimal(final_gpa_capped).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
#                 self.grade = self.get_grade_by_gpa(self.gpa); self.remarks = "Passed"

#             self.calc_meta = {
#                 "mandatory_ids": sorted(list(mandatory_id_set)),
#                 "optional_selected_exam_id": optional_selected_exam_id,
#                 "optional_valid": optional_valid,
#                 "total_full_marks": total_full,
#                 "gpa_policy": "avg(9 mandatory) + (optional>1 ? optional-2 : 0), cap 5.00",
#             }
#             self.save(update_fields=[
#                 "total_marks","gpa","grade","remarks",
#                 "base_gpa_no_optional","base_grade_no_optional",
#                 "optional_subject_label","optional_gp_raw","optional_gp_adjusted",
#                 "mandatory_gp_sum","mandatory_count","final_total_gp","final_gpa_raw","calc_meta",
#             ])
#             return
#             # --------- END: NINE_SCIENCE implementation ----------

#         # ---------- Class 9 (Business) ----------
#         elif scheme == GradingScheme.NINE_BUSINESS or scheme == GradingScheme.TEN_BUSINESS:
#             SubjectMark = self.subjectmark_set.model
#             subject_marks = self.subjectmark_set.select_related("subject").all()
#             if not subject_marks.exists():
#                 self._reset_no_marks()
#                 return

#             exam_subjects = {es.subject_id: es for es in self.exam.examsubject_set.all()}
#             full_marks_map = self.get_full_marks_map()

#             exam_subj_list = list(self.exam.subjects.all())
#             name_to_id = { (s.name or "").strip().lower(): s.id for s in exam_subj_list }
#             id_to_name = { s.id: (s.name or "") for s in exam_subj_list }

#             # ---- fixed mandatory (singles) ----
#             fixed_names = {
#                 "mathematics",
#                 "bangladesh and global studies",
#                 "ict",
#                 "religion",
#                 "accounting",
#                 "finance & banking",
#                 "business entrepreneurship",
#             }
#             fixed_ids = { name_to_id[n] for n in fixed_names if n in name_to_id }

#             # ---- combined groups ----
#             combined_papers_norm = {
#                 "Bangla": {"bangla 1st paper","bangla 2nd paper"},
#                 "English": {"english 1st paper","english 2nd paper"},
#             }
#             def _is_combined_subject_id(subj_id: int) -> bool:
#                 nm = (id_to_name.get(subj_id,"") or "").strip().lower()
#                 return nm in combined_papers_norm["Bangla"] or nm in combined_papers_norm["English"]

#             # ---- optional = fixed Agriculture ----
#             agriculture_exam_id = None
#             if "agriculture" in name_to_id:
#                 agriculture_exam_id = name_to_id["agriculture"]
#             else:
#                 # ফallback: নামের মধ্যে 'agric' থাকলে ধরো
#                 for s in exam_subj_list:
#                     nm = (s.name or "").strip().lower()
#                     if "agric" in nm:
#                         agriculture_exam_id = s.id
#                         break

#             mandatory_id_set = set(fixed_ids)  # business এ আলাদা main_subject নেই
#             optional_selected_exam_id = agriculture_exam_id
#             optional_id_used = agriculture_exam_id
#             optional_valid = bool(agriculture_exam_id)  # থাকলেই valid
#             if optional_id_used and (_is_combined_subject_id(optional_id_used) or optional_id_used in mandatory_id_set):
#                 # theoretically হওয়ার কথা নয়, তবু নিরাপত্তা
#                 optional_valid = False
#                 optional_id_used = None

#             # ---- partition marks ----
#             grouped_combined = defaultdict(list)
#             single_marks = []
#             for m in subject_marks:
#                 nm_norm = (getattr(m.subject, "name", "") or "").strip().lower()
#                 placed = False
#                 for combo, paper_set in combined_papers_norm.items():
#                     if nm_norm in paper_set:
#                         grouped_combined[combo].append(m); placed = True; break
#                 if placed: continue

#                 if m.subject_id in mandatory_id_set or (optional_id_used and m.subject_id == optional_id_used):
#                     single_marks.append(m)

#             # ---- aggregates ----
#             total_obtained_ex = 0.0; total_full = 0; has_failed_mand = False
#             total_gp_display_mand = 0.0; subject_count_mand = 0
#             per_subject_display_gp = {}

#             # combined (Bangla/English)
#             for cname, papers in grouped_combined.items():
#                 ex_total = sum((p.total_mark or 0) for p in papers)
#                 full = sum(full_marks_map.get(p.subject.id, 100) for p in papers)
#                 percent_raw = (ex_total / full) * 100 if full else 0.0
#                 gp_disp = self.get_point_by_percentage(percent_raw)
#                 total_gp_display_mand += gp_disp; subject_count_mand += 1
#                 if gp_disp == 0.0: has_failed_mand = True
#                 total_obtained_ex += ex_total; total_full += full

#             # singles (mandatory + agriculture optional)
#             optional_selected_gp_display = 0.0
#             for m in single_marks:
#                 full = full_marks_map.get(m.subject.id, 100)
#                 ex_total = (m.total_mark or 0)

#                 exam_subject = exam_subjects.get(m.subject_id)
#                 cq = m.cq_mark or 0; mcq = m.mcq_mark or 0; practical = m.practical_mark or 0
#                 failed_component = False
#                 if exam_subject:
#                     failed_component = (
#                         (exam_subject.cq_pass_marks is not None and cq < exam_subject.cq_pass_marks) or
#                         (exam_subject.mcq_pass_marks is not None and mcq < exam_subject.mcq_pass_marks) or
#                         (exam_subject.practical_pass_marks is not None and practical < exam_subject.practical_pass_marks) or
#                         (exam_subject.pass_marks is not None and ex_total < exam_subject.pass_marks)
#                     )

#                 percent_raw = (ex_total / full) * 100 if full else 0.0
#                 if failed_component:
#                     grade_disp = "F"; gp_disp = 0.0
#                 else:
#                     grade_disp = self.get_grade_by_percentage(ex_total, full)
#                     gp_disp = self.get_point_by_percentage(percent_raw)

#                 m.grade = grade_disp
#                 SubjectMark.objects.filter(pk=m.pk).update(grade=grade_disp)
#                 per_subject_display_gp[m.subject_id] = gp_disp

#                 if m.subject_id in mandatory_id_set:
#                     total_gp_display_mand += gp_disp; subject_count_mand += 1
#                     if failed_component or gp_disp == 0.0: has_failed_mand = True
#                 elif optional_id_used and m.subject_id == optional_id_used:
#                     optional_selected_gp_display = gp_disp

#                 total_obtained_ex += ex_total; total_full += full

#             # optional selected but invalid হলে (shouldn't happen), then just display GP if present
#             if optional_selected_exam_id and optional_id_used is None:
#                 optional_selected_gp_display = per_subject_display_gp.get(optional_selected_exam_id, optional_selected_gp_display)

#             # ---- Final GPA: avg(9 mandatory) + adjusted optional (agriculture), cap 5.00 ----
#             if optional_valid and optional_selected_gp_display > 1.0 and optional_id_used is not None:
#                 adjusted_optional = max(optional_selected_gp_display - 2.0, 0.0)
#             else:
#                 adjusted_optional = 0.0

#             final_total_gp = total_gp_display_mand + adjusted_optional
#             final_gpa_raw = (final_total_gp / subject_count_mand) if subject_count_mand > 0 else 0.0
#             final_gpa_capped = 5.0 if final_gpa_raw > 5.0 else final_gpa_raw

#             # cache
#             base_gpa_no_optional = (total_gp_display_mand / subject_count_mand) if subject_count_mand else 0.0
#             self.base_gpa_no_optional = round(base_gpa_no_optional, 2)
#             self.base_grade_no_optional = self.get_grade_by_gpa(base_gpa_no_optional)

#             self.optional_subject_label = f"subject_id:{optional_selected_exam_id}" if optional_selected_exam_id else None
#             self.optional_gp_raw = float(optional_selected_gp_display)
#             self.optional_gp_adjusted = float(adjusted_optional)
#             self.mandatory_gp_sum = float(total_gp_display_mand)
#             self.mandatory_count = int(subject_count_mand)
#             self.final_total_gp = float(final_total_gp)
#             self.final_gpa_raw = float(final_gpa_capped)

#             # finalize
#             self.total_marks = total_obtained_ex
#             if has_failed_mand:
#                 self.grade = "F"; self.gpa = 0.0; self.remarks = "Failed"
#             else:
#                 self.gpa = float(Decimal(final_gpa_capped).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
#                 self.grade = self.get_grade_by_gpa(self.gpa); self.remarks = "Passed"

#             self.calc_meta = {
#                 "mandatory_ids": sorted(list(mandatory_id_set)),
#                 "optional_selected_exam_id": optional_selected_exam_id,
#                 "optional_valid": optional_valid,
#                 "total_full_marks": total_full,
#                 "gpa_policy": "avg(9 mandatory) + (agriculture>1 ? agriculture-2 : 0), cap 5.00",
#             }
#             self.save(update_fields=[
#                 "total_marks","gpa","grade","remarks",
#                 "base_gpa_no_optional","base_grade_no_optional",
#                 "optional_subject_label","optional_gp_raw","optional_gp_adjusted",
#                 "mandatory_gp_sum","mandatory_count","final_total_gp","final_gpa_raw","calc_meta",
#             ])
#             return
#         # --------- END: NINE_BUSINESS implementation ----------


#         # ---------- Class 9/10 (Arts) ----------
#         elif scheme == GradingScheme.NINE_HUMANITIES or scheme == GradingScheme.TEN_HUMANITIES:
#             SubjectMark = self.subjectmark_set.model
#             subject_marks = self.subjectmark_set.select_related("subject").all()
#             if not subject_marks.exists():
#                 self._reset_no_marks()
#                 return

#             exam_subjects = {es.subject_id: es for es in self.exam.examsubject_set.all()}
#             full_marks_map = self.get_full_marks_map()

#             exam_subj_list = list(self.exam.subjects.all())
#             name_to_id = { (s.name or "").strip().lower(): s.id for s in exam_subj_list }
#             id_to_name = { s.id: (s.name or "") for s in exam_subj_list }

#             # ---- fixed mandatory (singles) ----
#             fixed_names = {
#                 "mathematics",
#                 "bangladesh and global studies",
#                 "ict",
#                 "religion",
#                 "history of bangladesh and world civilization",
#                 "geography and environment",
#                 "civics and citizenship",
#             }
#             fixed_ids = { name_to_id[n] for n in fixed_names if n in name_to_id }

#             # ---- combined groups ----
#             combined_papers_norm = {
#                 "Bangla": {"bangla 1st paper","bangla 2nd paper"},
#                 "English": {"english 1st paper","english 2nd paper"},
#             }
#             def _is_combined_subject_id(subj_id: int) -> bool:
#                 nm = (id_to_name.get(subj_id,"") or "").strip().lower()
#                 return nm in combined_papers_norm["Bangla"] or nm in combined_papers_norm["English"]

#             # ---- optional = fixed Agriculture ----
#             agriculture_exam_id = None
#             if "agriculture" in name_to_id:
#                 agriculture_exam_id = name_to_id["agriculture"]
#             else:
#                 # Fallback: নামের মধ্যে 'agric' থাকলে ধরো
#                 for s in exam_subj_list:
#                     nm = (s.name or "").strip().lower()
#                     if "agric" in nm:
#                         agriculture_exam_id = s.id
#                         break

#             mandatory_id_set = set(fixed_ids)  # business এ আলাদা main_subject নেই
#             optional_selected_exam_id = agriculture_exam_id
#             optional_id_used = agriculture_exam_id
#             optional_valid = bool(agriculture_exam_id)  # থাকলেই valid
#             if optional_id_used and (_is_combined_subject_id(optional_id_used) or optional_id_used in mandatory_id_set):
#                 # theoretically হওয়ার কথা নয়, তবু নিরাপত্তা
#                 optional_valid = False
#                 optional_id_used = None

#             # ---- partition marks ----
#             grouped_combined = defaultdict(list)
#             single_marks = []
#             for m in subject_marks:
#                 nm_norm = (getattr(m.subject, "name", "") or "").strip().lower()
#                 placed = False
#                 for combo, paper_set in combined_papers_norm.items():
#                     if nm_norm in paper_set:
#                         grouped_combined[combo].append(m); placed = True; break
#                 if placed: continue

#                 if m.subject_id in mandatory_id_set or (optional_id_used and m.subject_id == optional_id_used):
#                     single_marks.append(m)

#             # ---- aggregates ----
#             total_obtained_ex = 0.0; total_full = 0; has_failed_mand = False
#             total_gp_display_mand = 0.0; subject_count_mand = 0
#             per_subject_display_gp = {}

#             # combined (Bangla/English)
#             for cname, papers in grouped_combined.items():
#                 ex_total = sum((p.total_mark or 0) for p in papers)
#                 full = sum(full_marks_map.get(p.subject.id, 100) for p in papers)
#                 percent_raw = (ex_total / full) * 100 if full else 0.0
#                 gp_disp = self.get_point_by_percentage(percent_raw)
#                 total_gp_display_mand += gp_disp; subject_count_mand += 1
#                 if gp_disp == 0.0: has_failed_mand = True
#                 total_obtained_ex += ex_total; total_full += full

#             # singles (mandatory + agriculture optional)
#             optional_selected_gp_display = 0.0
#             for m in single_marks:
#                 full = full_marks_map.get(m.subject.id, 100)
#                 ex_total = (m.total_mark or 0)

#                 exam_subject = exam_subjects.get(m.subject_id)
#                 cq = m.cq_mark or 0; mcq = m.mcq_mark or 0; practical = m.practical_mark or 0
#                 failed_component = False
#                 if exam_subject:
#                     failed_component = (
#                         (exam_subject.cq_pass_marks is not None and cq < exam_subject.cq_pass_marks) or
#                         (exam_subject.mcq_pass_marks is not None and mcq < exam_subject.mcq_pass_marks) or
#                         (exam_subject.practical_pass_marks is not None and practical < exam_subject.practical_pass_marks) or
#                         (exam_subject.pass_marks is not None and ex_total < exam_subject.pass_marks)
#                     )

#                 percent_raw = (ex_total / full) * 100 if full else 0.0
#                 if failed_component:
#                     grade_disp = "F"; gp_disp = 0.0
#                 else:
#                     grade_disp = self.get_grade_by_percentage(ex_total, full)
#                     gp_disp = self.get_point_by_percentage(percent_raw)

#                 m.grade = grade_disp
#                 SubjectMark.objects.filter(pk=m.pk).update(grade=grade_disp)
#                 per_subject_display_gp[m.subject_id] = gp_disp

#                 if m.subject_id in mandatory_id_set:
#                     total_gp_display_mand += gp_disp; subject_count_mand += 1
#                     if failed_component or gp_disp == 0.0: has_failed_mand = True
#                 elif optional_id_used and m.subject_id == optional_id_used:
#                     optional_selected_gp_display = gp_disp

#                 total_obtained_ex += ex_total; total_full += full

#             # optional selected but invalid হলে (shouldn't happen), then just display GP if present
#             if optional_selected_exam_id and optional_id_used is None:
#                 optional_selected_gp_display = per_subject_display_gp.get(optional_selected_exam_id, optional_selected_gp_display)

#             # ---- Final GPA: avg(9 mandatory) + adjusted optional (agriculture), cap 5.00 ----
#             if optional_valid and optional_selected_gp_display > 1.0 and optional_id_used is not None:
#                 adjusted_optional = max(optional_selected_gp_display - 2.0, 0.0)
#             else:
#                 adjusted_optional = 0.0

#             final_total_gp = total_gp_display_mand + adjusted_optional
#             final_gpa_raw = (final_total_gp / subject_count_mand) if subject_count_mand > 0 else 0.0
#             final_gpa_capped = 5.0 if final_gpa_raw > 5.0 else final_gpa_raw

#             # cache
#             base_gpa_no_optional = (total_gp_display_mand / subject_count_mand) if subject_count_mand else 0.0
#             self.base_gpa_no_optional = round(base_gpa_no_optional, 2)
#             self.base_grade_no_optional = self.get_grade_by_gpa(base_gpa_no_optional)

#             self.optional_subject_label = f"subject_id:{optional_selected_exam_id}" if optional_selected_exam_id else None
#             self.optional_gp_raw = float(optional_selected_gp_display)
#             self.optional_gp_adjusted = float(adjusted_optional)
#             self.mandatory_gp_sum = float(total_gp_display_mand)
#             self.mandatory_count = int(subject_count_mand)
#             self.final_total_gp = float(final_total_gp)
#             self.final_gpa_raw = float(final_gpa_capped)

#             # finalize
#             self.total_marks = total_obtained_ex
#             if has_failed_mand:
#                 self.grade = "F"; self.gpa = 0.0; self.remarks = "Failed"
#             else:
#                 self.gpa = float(Decimal(final_gpa_capped).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
#                 self.grade = self.get_grade_by_gpa(self.gpa); self.remarks = "Passed"

#             self.calc_meta = {
#                 "mandatory_ids": sorted(list(mandatory_id_set)),
#                 "optional_selected_exam_id": optional_selected_exam_id,
#                 "optional_valid": optional_valid,
#                 "total_full_marks": total_full,
#                 "gpa_policy": "avg(9 mandatory) + (agriculture>1 ? agriculture-2 : 0), cap 5.00",
#             }
#             self.save(update_fields=[
#                 "total_marks","gpa","grade","remarks",
#                 "base_gpa_no_optional","base_grade_no_optional",
#                 "optional_subject_label","optional_gp_raw","optional_gp_adjusted",
#                 "mandatory_gp_sum","mandatory_count","final_total_gp","final_gpa_raw","calc_meta",
#             ])
#             return
#         # --------- END: NINE_BUSINESS implementation ----------







#         # ---------- Junior & other schemes ----------
#         subject_marks = self.subjectmark_set.select_related("subject").all()
#         if not subject_marks.exists():
#             self._reset_no_marks()
#             return

#         exam_subjects = {es.subject_id: es for es in self.exam.examsubject_set.all()}
#         full_marks_map = self.get_full_marks_map()

#         combined_subjects = {
#             "Bangla": ["Bangla 1st Paper", "Bangla 2nd Paper"],
#             "English": ["English 1st Paper", "English 2nd Paper"],
#         }
#         grouped_marks = defaultdict(list)
#         regular_subject_marks = []

#         for mark in subject_marks:
#             found = False
#             subj_name = getattr(mark.subject, "name", "") or ""
#             for combined_name, paper_names in combined_subjects.items():
#                 if subj_name in paper_names:
#                     grouped_marks[combined_name].append(mark)
#                     found = True
#                     break
#             if not found:
#                 regular_subject_marks.append(mark)

#         total_obtained = 0
#         total_full = 0
#         total_gps = 0.0
#         subject_count = 0
#         has_failed = False

#         for name, papers in grouped_marks.items():
#             total = sum((p.total_mark or 0) for p in papers)
#             full = sum(full_marks_map.get(p.subject.id, 100) for p in papers)
#             percentage = (total / full) * 100 if full else 0
#             gpa_val = self.get_point_by_percentage(percentage)
#             total_obtained += total; total_full += full
#             total_gps += gpa_val; subject_count += 1
#             if gpa_val == 0.0: has_failed = True

#         for mark in regular_subject_marks:
#             full = full_marks_map.get(mark.subject.id, 100)
#             total = mark.total_mark or 0
#             percentage = (total / full) * 100 if full else 0

#             exam_subject = exam_subjects.get(mark.subject_id)
#             cq = mark.cq_mark or 0
#             mcq = mark.mcq_mark or 0
#             practical = mark.practical_mark or 0
#             ct = mark.ct_mark or 0
#             if exam_subject:
#                 failed = (
#                     (exam_subject.cq_pass_marks is not None and cq < exam_subject.cq_pass_marks) or
#                     (exam_subject.mcq_pass_marks is not None and mcq < exam_subject.mcq_pass_marks) or
#                     (exam_subject.practical_pass_marks is not None and practical < exam_subject.practical_pass_marks) or
#                     (exam_subject.ct_pass_marks is not None and ct < exam_subject.ct_pass_marks) or
#                     (exam_subject.pass_marks is not None and total < exam_subject.pass_marks)
#                 )
#             else:
#                 failed = False

#             if failed:
#                 grade = "F"; gpa_val = 0.0
#             else:
#                 grade = self.get_grade_by_percentage(total, full)
#                 gpa_val = self.get_point_by_percentage(percentage)

#             SubjectMark.objects.filter(pk=mark.pk).update(grade=grade)

#             total_obtained += total; total_full += full
#             total_gps += gpa_val; subject_count += 1
#             if gpa_val == 0.0: has_failed = True

#         self.total_marks = total_obtained
#         if has_failed:
#             self.grade = "F"; self.gpa = 0.0; self.remarks = "Failed"
#         else:
#             avg_gpa = Decimal(total_gps / subject_count).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) if subject_count else Decimal("0.00")
#             self.gpa = float(avg_gpa)
#             self.grade = self.get_grade_by_gpa(self.gpa)
#             self.remarks = "Passed"

#         # clear caches for non-optional schemes
#         self.base_gpa_no_optional = None
#         self.base_grade_no_optional = None
#         self.optional_subject_label = None
#         self.optional_gp_raw = None
#         self.optional_gp_adjusted = None
#         self.mandatory_gp_sum = None
#         self.mandatory_count = None
#         self.final_total_gp = None
#         self.final_gpa_raw = None
#         self.calc_meta = {}

#         self.save(update_fields=[
#             "total_marks","gpa","grade","remarks",
#             "base_gpa_no_optional","base_grade_no_optional",
#             "optional_subject_label","optional_gp_raw","optional_gp_adjusted",
#             "mandatory_gp_sum","mandatory_count",
#             "final_total_gp","final_gpa_raw","calc_meta",
#         ])

#     def _reset_no_marks(self):
#         """Utility: when no marks exist."""
#         self.total_marks = 0
#         self.gpa = 0.0
#         self.grade = "F"
#         self.remarks = "No marks"
#         self.base_gpa_no_optional = None
#         self.base_grade_no_optional = None
#         self.optional_subject_label = None
#         self.optional_gp_raw = None
#         self.optional_gp_adjusted = None
#         self.mandatory_gp_sum = None
#         self.mandatory_count = None
#         self.final_total_gp = None
#         self.final_gpa_raw = None
#         self.calc_meta = {}
#         self.save(update_fields=[
#             "total_marks","gpa","grade","remarks",
#             "base_gpa_no_optional","base_grade_no_optional",
#             "optional_subject_label","optional_gp_raw","optional_gp_adjusted",
#             "mandatory_gp_sum","mandatory_count","final_total_gp","final_gpa_raw","calc_meta",
#         ])


# class SubjectMark(models.Model):
#     exam_record = models.ForeignKey(ExamRecord, on_delete=models.CASCADE)
#     subject = models.ForeignKey('Subject', on_delete=models.CASCADE)
#     grade = models.CharField(max_length=5, null=True, blank=True)

#     cq_mark = models.IntegerField(null=True, blank=True)
#     mcq_mark = models.IntegerField(null=True, blank=True)
#     practical_mark = models.IntegerField(null=True, blank=True)
#     ct_mark = models.IntegerField(null=True, blank=True)
#     total_mark = models.FloatField(null=True, blank=True)

#     def __str__(self):
#         try:
#             return f"Name: {self.exam_record.student.add_name} | Subject: {self.subject.name}"
#         except Exception:
#             return f"SubjectMark {self.id}"

#     def save(self, *args, **kwargs):
#         self.total_mark = sum([
#             self.cq_mark or 0,
#             self.mcq_mark or 0,
#             self.practical_mark or 0,
#             self.ct_mark or 0
#         ])
#         super().save(*args, **kwargs)



class SubjectMark(models.Model):
    exam_record = models.ForeignKey('ExamRecord', on_delete=models.CASCADE, related_name='marks')
    subject      = models.ForeignKey('Subject', on_delete=models.CASCADE)

    cq_mark       = models.FloatField(null=True, blank=True)
    mcq_mark      = models.FloatField(null=True, blank=True)
    practical_mark= models.FloatField(null=True, blank=True)
    ct_mark       = models.FloatField(null=True, blank=True)

    total_mark    = models.FloatField(null=True, blank=True)
    grade         = models.CharField(max_length=5, null=True, blank=True)

    class Meta:
        unique_together = ('exam_record', 'subject')
        indexes = [
            models.Index(fields=['exam_record']),
            models.Index(fields=['subject']),
        ]

    def __str__(self):
        return f"{self.exam_record} → {self.subject.name}"
