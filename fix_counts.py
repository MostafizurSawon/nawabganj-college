from django.db.models import Q
from apps.admissions.models import HscAdmissions, Subjects

for subject in Subjects.objects.all():
    code = (subject.code or '').strip()
    if not code:
        subject.used_count = 0
        subject.save(update_fields=['used_count'])
        continue

    total = HscAdmissions.objects.filter(
        Q(main_subject__code=code) |
        Q(fourth_subject__code=code) |
        Q(optional_subject__code=code) |
        Q(optional_subject_2__code=code)
    ).distinct().count()

    subject.used_count = total
    subject.save(update_fields=['used_count'])

print("used_count আপডেট সম্পন্ন।")
