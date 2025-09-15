from django.contrib import admin
from .models import Programs, DegreePrograms, Session,DegreeSession, Subjects, DegreeSubjects ,HscAdmissions, Group, Fee, DegreeAdmission

# Register your models here.
admin.site.register(Programs)
admin.site.register(DegreePrograms)
admin.site.register(Session)
admin.site.register(DegreeSession)
admin.site.register(Subjects)
admin.site.register(DegreeSubjects)
# admin.site.register(HscAdmissions)
# admin.site.register(DegreeAdmission)
admin.site.register(Group)
admin.site.register(Fee)


@admin.register(HscAdmissions)
class HscAdmissionAdmin(admin.ModelAdmin):
    list_display = ('add_name', 'add_admission_group', 'add_session', 'created_by', 'submitted_via', 'is_self_submitted', 'created_at')
    list_filter  = ('submitted_via', 'add_admission_group', 'add_session')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(DegreeAdmission)
class DegreeAdmissionAdmin(admin.ModelAdmin):
    list_display = ('add_name', 'add_admission_group', 'add_session', 'created_by', 'submitted_via', 'is_self_submitted', 'created_at')
    list_filter  = ('submitted_via', 'add_admission_group', 'add_session')
    readonly_fields = ('created_at', 'updated_at')
