from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from datetime import timedelta
from django.http import HttpResponse
from django.utils.text import slugify
from django.core.files.storage import default_storage

import io
import os
import csv
import zipfile

from .models import (
    Programs, DegreePrograms, Session, DegreeSession,
    Subjects, DegreeSubjects, HscAdmissions, Group, Fee, DegreeAdmission
)

# ----------------------------
# Bulk status actions (HSC)
# ----------------------------
def mark_as_paid(modeladmin, request, queryset):
    queryset.update(add_payment_status='paid')
mark_as_paid.short_description = "Mark selected admissions as Paid"

def mark_as_unpaid(modeladmin, request, queryset):
    queryset.update(add_payment_status='unpaid')
mark_as_unpaid.short_description = "Mark selected admissions as Unpaid"

def mark_as_pending(modeladmin, request, queryset):
    queryset.update(add_payment_status='pending')
mark_as_pending.short_description = "Mark selected admissions as Pending"


# ----------------------------
# Date filter (generic)
# ----------------------------
class CreatedAtFilter(admin.SimpleListFilter):
    title = 'Created At'
    parameter_name = 'created_at'

    def lookups(self, request, model_admin):
        return (
            ('today', 'Today'),
            ('this_week', 'This Week'),
            ('this_month', 'This Month'),
            ('past_30_days', 'Past 30 Days'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'today':
            today = timezone.now().date()
            return queryset.filter(created_at__date=today)
        if self.value() == 'this_week':
            start_of_week = timezone.now().date() - timedelta(days=timezone.now().weekday())
            return queryset.filter(created_at__date__gte=start_of_week)
        if self.value() == 'this_month':
            start_of_month = timezone.now().date().replace(day=1)
            return queryset.filter(created_at__date__gte=start_of_month)
        if self.value() == 'past_30_days':
            thirty_days_ago = timezone.now().date() - timedelta(days=30)
            return queryset.filter(created_at__date__gte=thirty_days_ago)
        return queryset


# -------------------------------------------------------
# Admin action: Download names + photos as a ZIP (HSC)
# -------------------------------------------------------
def download_names_photos_zip(modeladmin, request, queryset):
    """
    Packages selected HscAdmissions students' add_name + add_photo into a ZIP.
    - Subfolders per Session (add_session.ses_name)
    - Adds manifest.csv per session: add_name, photo_filename
    - Respects current admin filters
    """
    if not queryset.exists():
        modeladmin.message_user(request, "No records selected.", level="warning")
        return

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        sessions = {}
        for obj in queryset:
            ses_name = obj.add_session.ses_name if obj.add_session else "No-Session"
            sessions.setdefault(ses_name, []).append(obj)

        for ses_name, items in sessions.items():
            safe_session = slugify(ses_name or "No-Session") or "no-session"

            manifest_rows = [("add_name", "photo_filename")]
            for s in items:
                base_name = f"{s.add_class_roll or 'no-roll'}_{slugify(s.add_name or 'no-name')}"
                photo_filename = "no-photo"

                if s.add_photo:
                    photo_path = s.add_photo.name  # storage-relative path
                    _, ext = os.path.splitext(photo_path)
                    ext = ext or ".jpg"
                    photo_filename = f"{base_name}{ext}"
                    arcname = f"{safe_session}/{photo_filename}"

                    try:
                        with default_storage.open(photo_path, "rb") as fp:
                            zf.writestr(arcname, fp.read())
                    except Exception:
                        photo_filename = "photo-missing.txt"
                        zf.writestr(
                            f"{safe_session}/{base_name}_photo-missing.txt",
                            f"Photo not found for: {s.add_name}"
                        )

                manifest_rows.append((s.add_name or "", photo_filename))

            # write manifest.csv for this session folder
            csv_buffer = io.StringIO()
            writer = csv.writer(csv_buffer)
            writer.writerows(manifest_rows)
            zf.writestr(f"{safe_session}/manifest.csv", csv_buffer.getvalue())

    buf.seek(0)
    resp = HttpResponse(buf.getvalue(), content_type="application/zip")
    resp["Content-Disposition"] = 'attachment; filename="hscadmissions_names_photos.zip"'
    return resp
download_names_photos_zip.short_description = "Download ZIP (names + photos)"


# ----------------------------
# Inlines
# ----------------------------
class HscSubjectsInline(admin.TabularInline):
    model = HscAdmissions.subjects.through
    extra = 1
    verbose_name = "Subject"
    verbose_name_plural = "Subjects"

class DegreeSubjectsInline(admin.TabularInline):
    model = DegreeAdmission.subjects.through
    extra = 1
    verbose_name = "Degree Subject"
    verbose_name_plural = "Degree Subjects"


# ----------------------------
# Simple models
# ----------------------------
@admin.register(Programs)
class ProgramsAdmin(admin.ModelAdmin):
    list_display = ('pro_name', 'pro_status', 'pro_year')
    list_filter = ('pro_status', 'pro_year')
    search_fields = ('pro_name',)
    list_editable = ('pro_status',)
    ordering = ('pro_name',)
    list_per_page = 20


@admin.register(DegreePrograms)
class DegreeProgramsAdmin(admin.ModelAdmin):
    list_display = ('deg_name', 'deg_status', 'deg_year')
    list_filter = ('deg_status', 'deg_year')
    search_fields = ('deg_name',)
    list_editable = ('deg_status',)
    ordering = ('deg_name',)
    list_per_page = 20


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('ses_name', 'ses_status')
    list_filter = ('ses_status',)
    search_fields = ('ses_name',)
    list_editable = ('ses_status',)
    ordering = ('ses_name',)
    list_per_page = 20


@admin.register(DegreeSession)
class DegreeSessionAdmin(admin.ModelAdmin):
    list_display = ('ses_name', 'ses_status')
    list_filter = ('ses_status',)
    search_fields = ('ses_name',)
    list_editable = ('ses_status',)
    ordering = ('ses_name',)
    list_per_page = 20


@admin.register(Subjects)
class SubjectsAdmin(admin.ModelAdmin):
    list_display = ('sub_name', 'group', 'code', 'sub_select', 'sub_status', 'used_count', 'limit')
    list_filter = ('group', 'sub_status', 'sub_select')
    search_fields = ('sub_name', 'code')
    list_editable = ('sub_status', 'limit', 'used_count')
    ordering = ('sub_name',)
    list_per_page = 20


@admin.register(DegreeSubjects)
class DegreeSubjectsAdmin(admin.ModelAdmin):
    list_display = ('sub_name', 'group', 'code', 'sub_status')
    list_filter = ('group', 'sub_status')
    search_fields = ('sub_name', 'code')
    list_editable = ('sub_status',)
    ordering = ('sub_name',)
    list_per_page = 20


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('group_name',)
    search_fields = ('group_name',)
    ordering = ('group_name',)
    list_per_page = 20


@admin.register(Fee)
class FeeAdmin(admin.ModelAdmin):
    list_display = ('fee_session', 'fee_program', 'fee_group', 'amount')
    list_filter = ('fee_session', 'fee_program', 'fee_group')
    search_fields = ('fee_session__ses_name', 'fee_program__pro_name', 'fee_group__group_name')
    list_editable = ('amount',)
    ordering = ('fee_session',)
    list_per_page = 20


# ----------------------------
# HSC Admissions
# ----------------------------
@admin.register(HscAdmissions)
class HscAdmissionAdmin(admin.ModelAdmin):
    list_display = (
        'add_name',
        'add_admission_group',
        'add_session',
        'add_class_roll',
        'add_payment_status',
        'display_photo',
        'add_mobile',
        'created_by',
        'submitted_via',
        'is_self_submitted',
        'created_at',
    )
    list_filter = (
        'add_admission_group',
        'add_session',
        'add_payment_status',
        CreatedAtFilter,
        'submitted_via',
        'add_gender',
        'add_blood_group',
    )
    search_fields = (
        'add_name',
        'add_name_bangla',
        'add_mobile',
        'add_class_roll',
        'add_trxid',
        'add_ssc_roll',
    )
    list_editable = ('add_payment_status',)
    readonly_fields = ('created_at', 'updated_at', 'display_photo')
    inlines = [HscSubjectsInline]
    actions = [mark_as_paid, mark_as_unpaid, mark_as_pending, download_names_photos_zip]
    list_per_page = 20
    ordering = ('-created_at',)
    # date_hierarchy = 'created_at'  # Disabled to avoid MySQL timezone crash

    fieldsets = (
        ('Personal Information', {
            'fields': (
                'add_name', 'add_name_bangla', 'add_mobile', 'add_photo',
                'add_birthdate', 'add_age', 'add_gender', 'add_nationality',
                'add_religion', 'add_blood_group', 'add_birth_certificate_no',
                'qouta', 'qouta_name', 'community', 'community_name',
            )
        }),
        ('Academic Information', {
            'fields': (
                'add_program', 'add_admission_group', 'add_session', 'add_class_roll',
                'add_hsc_year', 'merit_position', 'subjects', 'main_subject',
                'fourth_subject', 'optional_subject', 'optional_subject_2',
            )
        }),
        ('SSC Information', {
            'fields': (
                'add_ssc_roll', 'add_ssc_reg', 'add_ssc_session', 'add_ssc_institute',
                'add_ssc_gpa', 'add_ssc_group', 'add_ssc_board', 'add_ssc_passyear',
            )
        }),
        ('Parent/Guardian Information', {
            'fields': (
                'add_father', 'add_father_mobile', 'add_father_nid', 'add_father_birthdate',
                'add_mother', 'add_mother_mobile', 'add_mother_nid', 'add_mother_birthdate',
                'add_parent_select', 'add_parent', 'add_parent_mobile', 'add_parent_relation',
                'add_parent_service', 'add_parent_income', 'add_parent_nid',
                'add_parent_land_agri', 'add_parent_land_nonagri',
            )
        }),
        ('Address Information', {
            'fields': (
                'add_village', 'add_post', 'add_police', 'add_postal', 'add_distric',
                'add_address_same', 'add_village_per', 'add_post_per', 'add_police_per',
                'add_postal_per', 'add_distric_per',
            )
        }),
        ('Payment Information', {
            'fields': (
                'add_payment_method', 'add_amount', 'add_trxid', 'add_slip',
                'add_payment_status', 'add_payment_note',
            )
        }),
        ('Metadata', {
            'fields': ('created_by', 'submitted_via', 'created_at', 'updated_at')
        }),
    )

    def display_photo(self, obj):
        if obj.add_photo:
            return format_html('<img src="{}" width="50" height="50" style="border-radius:50%;" />', obj.add_photo.url)
        return "No Photo"
    display_photo.short_description = "Photo"

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        if search_term:
            queryset |= self.model.objects.filter(
                add_name__icontains=search_term
            ) | self.model.objects.filter(
                add_name_bangla__icontains=search_term
            ) | self.model.objects.filter(
                add_mobile__icontains=search_term
            )
        return queryset, True


# ----------------------------
# Degree Admissions
# ----------------------------
@admin.register(DegreeAdmission)
class DegreeAdmissionAdmin(admin.ModelAdmin):
    list_display = (
        'add_name',
        'add_admission_group',
        'add_session',
        'add_class_roll',
        'display_photo',
        'add_mobile',
        'created_by',
        'submitted_via',
        'is_self_submitted',
        'created_at',
    )
    list_filter = (
        'add_admission_group',
        'add_session',
        CreatedAtFilter,
        'submitted_via',
        'add_gender',
        'add_blood_group',
    )
    search_fields = (
        'add_name', 'add_name_bangla', 'add_mobile',
        'add_class_roll', 'add_trxid', 'add_ssc_roll', 'add_hsc_roll',
    )
    readonly_fields = ('created_at', 'updated_at', 'display_photo')
    inlines = [DegreeSubjectsInline]
    list_per_page = 20
    ordering = ('-created_at',)

    fieldsets = (
        ('Personal Information', {
            'fields': (
                'add_name', 'add_name_bangla', 'add_mobile', 'add_photo',
                'add_birthdate', 'add_age', 'add_gender', 'add_nationality',
                'add_religion', 'add_blood_group', 'add_birth_certificate_no',
                'qouta', 'qouta_name', 'community', 'community_name',
            )
        }),
        ('Academic Information', {
            'fields': (
                'add_program', 'add_admission_group', 'add_session',
                'add_class_roll', 'merit_position', 'subjects', 'main_subject',
            )
        }),
        ('SSC Information', {
            'fields': (
                'add_ssc_roll', 'add_ssc_reg', 'add_ssc_session',
                'add_ssc_institute', 'add_ssc_gpa', 'add_ssc_group',
                'add_ssc_board', 'add_ssc_passyear',
            )
        }),
        ('HSC Information', {
            'fields': (
                'add_hsc_roll', 'add_hsc_reg', 'add_hsc_session',
                'add_hsc_institute', 'add_hsc_gpa', 'add_hsc_group',
                'add_hsc_board', 'add_hsc_passyear',
            )
        }),
        ('Parent/Guardian Information', {
            'fields': (
                'add_father', 'add_father_mobile', 'add_father_nid', 'add_father_birthdate',
                'add_mother', 'add_mother_mobile', 'add_mother_nid', 'add_mother_birthdate',
                'add_parent_select', 'add_parent', 'add_parent_mobile',
                'add_parent_relation', 'add_parent_service', 'add_parent_income',
                'add_parent_nid', 'add_parent_land_agri', 'add_parent_land_nonagri',
            )
        }),
        ('Address Information', {
            'fields': (
                'add_village', 'add_post', 'add_police', 'add_postal', 'add_distric',
                'add_address_same', 'add_village_per', 'add_post_per',
                'add_police_per', 'add_postal_per', 'add_distric_per',
            )
        }),
        ('Payment Information', {
            'fields': ('add_payment_method', 'add_amount', 'add_trxid', 'add_slip')
        }),
        ('Metadata', {
            'fields': ('created_by', 'submitted_via', 'created_at', 'updated_at')
        }),
    )

    def display_photo(self, obj):
        if obj.add_photo:
            return format_html('<img src="{}" width="50" height="50" style="border-radius:50%;" />', obj.add_photo.url)
        return "No Photo"
    display_photo.short_description = "Photo"

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        if search_term:
            queryset |= self.model.objects.filter(
                add_name__icontains=search_term
            ) | self.model.objects.filter(
                add_name_bangla__icontains=search_term
            ) | self.model.objects.filter(
                add_mobile__icontains=search_term
            ) | self.model.objects.filter(
                add_hsc_roll__icontains=search_term
            )
        return queryset, True
