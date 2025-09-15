from django.contrib import admin, messages
# from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
# from django.http import HttpResponse
# from django.db import transaction
# import csv

from .models import (
     Subject
    #  AcademicYear,
#     Exam, ExamRecord, SubjectMark, ExamSubject, GradingScheme
)





from .models import Exam, ExamSubject, ExamRecord, SubjectMark

class ExamSubjectInline(admin.TabularInline):
    model = ExamSubject
    extra = 1
    raw_id_fields = ('subject',)   # বড় লিস্ট হলে পারফরম্যান্স ভালো থাকবে

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('exam_name', 'exam_session', 'exam_class', 'group_name')
    inlines = [ExamSubjectInline]  # ← filter_horizontal সরিয়ে এটা দিন

@admin.register(ExamRecord)
class ExamRecordAdmin(admin.ModelAdmin):
    list_display = ('exam', 'hsc_student', 'gpa', 'grade')

@admin.register(SubjectMark)
class SubjectMarkAdmin(admin.ModelAdmin):
    list_display = ('exam_record', 'subject', 'total_mark', 'grade')





admin.site.register(Subject)

# # -------------------------
# # Global Admin Branding
# # -------------------------
# admin.site.site_header = "School Management – Admin"
# admin.site.site_title = "School Admin"
# admin.site.index_title = "Dashboard"


# # -------------------------
# # Simple, Useful Admins
# # -------------------------
# @admin.register(SchoolClass)
# class SchoolClassAdmin(admin.ModelAdmin):
#     list_display = ("name",)
#     search_fields = ("name",)
#     ordering = ("name",)


# @admin.register(AcademicYear)
# class AcademicYearAdmin(admin.ModelAdmin):
#     list_display = ("name",)
#     search_fields = ("name",)
#     ordering = ("-name",)


# @admin.register(Subject)
# class SubjectAdmin(admin.ModelAdmin):
#     list_display = ("name", "code", "class_count")
#     search_fields = ("name", "code")
#     filter_horizontal = ("classes",)   # M2M nicer UI
#     list_per_page = 25
#     ordering = ("name",)

#     @admin.display(description="Attached Classes")
#     def class_count(self, obj):
#         return obj.classes.count()


# # -------------------------
# # Inlines
# # -------------------------
# class ExamSubjectInline(admin.TabularInline):
#     model = ExamSubject
#     extra = 1
#     min_num = 0
#     autocomplete_fields = ("subject",)
#     fields = (
#         "subject", "full_marks", "pass_marks",
#         "cq_marks", "cq_pass_marks",
#         "mcq_marks", "mcq_pass_marks",
#         "practical_marks", "practical_pass_marks",
#         "ct_marks", "ct_pass_marks",
#     )
#     verbose_name = "Exam Subject"
#     verbose_name_plural = "Exam Subjects"


# class SubjectMarkInline(admin.TabularInline):
#     model = SubjectMark
#     extra = 0
#     autocomplete_fields = ("subject",)
#     fields = ("subject", "cq_mark", "mcq_mark", "practical_mark", "ct_mark", "total_mark", "grade")
#     readonly_fields = ("total_mark", "grade")
#     show_change_link = True


# # -------------------------
# # Exam Admin
# # -------------------------
# @admin.register(Exam)
# class ExamAdmin(admin.ModelAdmin):
#     list_display = (
#         "exam_name", "exam_class", "exam_year",
#         "group_badge", "scheme_badge",
#         "date_range", "subjects_count",
#     )
#     list_filter = (
#         "exam_year",
#         "exam_class",
#         "group",
#         ("exam_start_date", admin.DateFieldListFilter),
#         ("exam_end_date", admin.DateFieldListFilter),
#         "grading_scheme",
#     )
#     search_fields = ("exam_name", "exam_class__name", "exam_year__name")
#     autocomplete_fields = ("exam_year", "exam_class", "group")
#     inlines = [ExamSubjectInline]
#     date_hierarchy = "exam_start_date"
#     list_per_page = 25
#     ordering = ("-id",)
#     list_select_related = ("exam_year", "exam_class", "group")

#     actions = ("duplicate_exam_with_subjects",)

#     @admin.display(description="Group", ordering="group__group_name")
#     def group_badge(self, obj):
#         if not obj.group:
#             return format_html('<span style="padding:2px 6px;border-radius:10px;background:#eee;color:#666;">—</span>')
#         return format_html(
#             '<span style="padding:2px 6px;border-radius:10px;background:#EEF2FF;color:#4338CA;font-weight:600;">{}</span>',
#             obj.group.group_name
#         )

#     @admin.display(description="Scheme", ordering="grading_scheme")
#     def scheme_badge(self, obj):
#         color = {
#             GradingScheme.JUNIOR: "#065f46",          # green-800
#             GradingScheme.NINE_SCIENCE: "#1d4ed8",    # blue-700
#             GradingScheme.NINE_HUMANITIES: "#7c3aed", # violet-700
#             GradingScheme.NINE_BUSINESS: "#b45309",   # amber-700
#             GradingScheme.TEN_SCIENCE: "#2563eb",
#             GradingScheme.TEN_HUMANITIES: "#8b5cf6",
#             GradingScheme.TEN_BUSINESS: "#d97706",
#         }.get(obj.grading_scheme, "#374151")
#         return format_html(
#             '<span style="padding:2px 8px;border-radius:999px;background:{}20;color:{};font-weight:600;">{}</span>',
#             color, color, obj.get_grading_scheme_display()
#         )

#     @admin.display(description="Date")
#     def date_range(self, obj):
#         return f"{obj.exam_start_date} → {obj.exam_end_date}"

#     @admin.display(description="Subjects")
#     def subjects_count(self, obj):
#         return obj.subjects.count()

#     @admin.action(description="Duplicate selected exam(s) with subjects")
#     def duplicate_exam_with_subjects(self, request, queryset):
#         created = 0
#         with transaction.atomic():
#             for exam in queryset:
#                 new_exam = Exam.objects.create(
#                     exam_name=f"{exam.exam_name} (Copy)",
#                     exam_year=exam.exam_year,
#                     exam_class=exam.exam_class,
#                     group=exam.group,
#                     exam_start_date=exam.exam_start_date,
#                     exam_end_date=exam.exam_end_date,
#                 )
#                 # copy ExamSubject rows
#                 for es in exam.examsubject_set.all():
#                     ExamSubject.objects.create(
#                         exam=new_exam,
#                         subject=es.subject,
#                         full_marks=es.full_marks,
#                         pass_marks=es.pass_marks,
#                         cq_marks=es.cq_marks, cq_pass_marks=es.cq_pass_marks,
#                         mcq_marks=es.mcq_marks, mcq_pass_marks=es.mcq_pass_marks,
#                         practical_marks=es.practical_marks, practical_pass_marks=es.practical_pass_marks,
#                         ct_marks=es.ct_marks, ct_pass_marks=es.ct_pass_marks,
#                     )
#                 created += 1
#         self.message_user(request, _(f"Successfully duplicated {created} exam(s)."), level=messages.SUCCESS)


# # -------------------------
# # ExamRecord Admin
# # -------------------------
# @admin.register(ExamRecord)
# class ExamRecordAdmin(admin.ModelAdmin):
#     list_display = (
#         "exam", "student_display",
#         "total_marks", "grade_badge", "gpa",
#         "remarks",
#     )
#     list_filter = (
#         "exam",
#         ("gpa", admin.AllValuesFieldListFilter),
#         "grade",
#     )
#     search_fields = (
#         # student generic relation—fallback string search on JSON repr
#         "remarks",
#     )
#     autocomplete_fields = ("exam",)
#     inlines = [SubjectMarkInline]
#     list_per_page = 30
#     ordering = ("-id",)
#     list_select_related = ("exam",)

#     readonly_fields = (
#         "base_gpa_no_optional", "base_grade_no_optional",
#         "optional_subject_label", "optional_gp_raw", "optional_gp_adjusted",
#         "mandatory_gp_sum", "mandatory_count",
#         "final_total_gp", "final_gpa_raw",
#     )

#     fields = (
#         "exam", "student_content_type", "student_object_id", "student",
#         "total_marks", ("grade", "gpa"), "remarks",
#         ("base_gpa_no_optional", "base_grade_no_optional"),
#         ("optional_subject_label", "optional_gp_raw", "optional_gp_adjusted"),
#         ("mandatory_gp_sum", "mandatory_count"),
#         ("final_total_gp", "final_gpa_raw"),
#     )

#     list_editable = ("remarks",)
#     actions = ("recalculate_selected", "export_csv")

#     @admin.display(description="Student", ordering="student_object_id")
#     def student_display(self, obj):
#         # try to show a nice label if present
#         label = getattr(obj.student, "add_name", None) or str(obj.student)
#         return label

#     @admin.display(description="Grade")
#     def grade_badge(self, obj):
#         color_map = {
#             "A+": "#047857", "A": "#059669", "A-": "#10b981",
#             "B": "#2563eb", "C": "#7c3aed", "D": "#f59e0b", "F": "#ef4444",
#         }
#         color = color_map.get(obj.grade or "F", "#6b7280")
#         text = obj.grade or "—"
#         return format_html(
#             '<span style="padding:2px 8px;border-radius:999px;background:{}20;color:{};font-weight:700;">{}</span>',
#             color, color, text
#         )

#     @admin.action(description="Recalculate total/GPA for selected records")
#     def recalculate_selected(self, request, queryset):
#         updated = 0
#         for rec in queryset:
#             rec.calculate_total_and_grade()
#             updated += 1
#         self.message_user(request, _(f"Recalculated {updated} record(s)."), level=messages.SUCCESS)

#     @admin.action(description="Export selected to CSV")
#     def export_csv(self, request, queryset):
#         # Safe CSV export with useful columns
#         resp = HttpResponse(content_type="text/csv")
#         resp["Content-Disposition"] = "attachment; filename=exam_records.csv"
#         writer = csv.writer(resp)
#         writer.writerow([
#             "Exam", "Student", "Total Marks", "GPA", "Grade", "Remarks",
#             "Base GPA (no optional)", "Base Grade (no optional)",
#             "Optional Label", "Optional GP Raw", "Optional GP Adjusted",
#             "Mandatory GP Sum", "Mandatory Count",
#             "Final Total GP", "Final GPA Raw",
#         ])
#         for r in queryset.select_related("exam"):
#             student_label = getattr(r.student, "add_name", None) or str(r.student)
#             writer.writerow([
#                 str(r.exam),
#                 student_label,
#                 r.total_marks,
#                 r.gpa,
#                 r.grade,
#                 r.remarks,
#                 r.base_gpa_no_optional,
#                 r.base_grade_no_optional,
#                 r.optional_subject_label,
#                 r.optional_gp_raw,
#                 r.optional_gp_adjusted,
#                 r.mandatory_gp_sum,
#                 r.mandatory_count,
#                 r.final_total_gp,
#                 r.final_gpa_raw,
#             ])
#         return resp


# # -------------------------
# # SubjectMark admin (optional direct)
# # -------------------------
# @admin.register(SubjectMark)
# class SubjectMarkAdmin(admin.ModelAdmin):
#     list_display = ("exam_record", "subject", "total_mark", "grade")
#     list_filter = ("subject", "grade")
#     search_fields = ("exam_record__remarks", "subject__name", "subject__code")
#     autocomplete_fields = ("exam_record", "subject")
#     ordering = ("-id",)
#     list_per_page = 30
#     readonly_fields = ("total_mark", "grade")


# # -------------------------
# # (Optional) Unregister default admin if you want to hide
# # -------------------------
# # from django.contrib.auth.models import Group as AuthGroup
# # admin.site.unregister(AuthGroup)
