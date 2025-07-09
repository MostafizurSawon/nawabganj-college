from django.contrib import admin
from .models import Programs, DegreePrograms, Session, Subjects ,HscAdmissions, Group, Fee

# Register your models here.
admin.site.register(Programs)
admin.site.register(DegreePrograms)
admin.site.register(Session)
admin.site.register(Subjects)
admin.site.register(HscAdmissions)
admin.site.register(Group)
admin.site.register(Fee)
