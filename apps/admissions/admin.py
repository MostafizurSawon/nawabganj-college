from django.contrib import admin
from .models import Programs, DegreePrograms, Session,DegreeSession, Subjects, DegreeSubjects ,HscAdmissions, Group, Fee, DegreeAdmission

# Register your models here.
admin.site.register(Programs)
admin.site.register(DegreePrograms)
admin.site.register(Session)
admin.site.register(DegreeSession)
admin.site.register(Subjects)
admin.site.register(DegreeSubjects)
admin.site.register(HscAdmissions)
admin.site.register(DegreeAdmission)
admin.site.register(Group)
admin.site.register(Fee)
