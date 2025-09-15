
from django.db import transaction
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver

from .models import Exam, ExamRecord, SubjectMark
from .utils import get_hsc_admissions_for_exam, student_allowed_exam_subject_ids

@receiver(post_save, sender=Exam)
def on_exam_saved(sender, instance: Exam, created, **kwargs):
    _sync_exam_records_and_marks(instance)

@receiver(m2m_changed, sender=Exam.subjects.through)
def on_exam_subjects_changed(sender, instance: Exam, action, **kwargs):
    if action in {"post_add", "post_remove", "post_clear"}:
        _sync_exam_records_and_marks(instance)

@transaction.atomic
def _sync_exam_records_and_marks(exam: Exam):
    # Full objects দরকার, তাই only() ব্যবহার করব না
    qs_students = (
        get_hsc_admissions_for_exam(exam)
        .select_related('add_program', 'add_session')
        .prefetch_related('subjects')
    )

    # existing records map: student_id -> record_id
    sid_to_rid = {
        er.hsc_student_id: er.id
        for er in ExamRecord.objects.filter(exam=exam).only('id', 'hsc_student_id')
    }

    # ✅ এখানে আগে qs_students.only('id') ছিল — এটা সমস্যা করছিল
    new_records = [
        ExamRecord(exam=exam, hsc_student_id=sid)
        for sid in qs_students.values_list('id', flat=True)
        if sid not in sid_to_rid
    ]
    if new_records:
        ExamRecord.objects.bulk_create(new_records, ignore_conflicts=True)
        sid_to_rid = {
            er.hsc_student_id: er.id
            for er in ExamRecord.objects.filter(exam=exam).only('id', 'hsc_student_id')
        }

    exam_subjects = list(exam.subjects.all())
    if not exam_subjects:
        SubjectMark.objects.filter(exam_record__exam=exam).delete()
        return

    existing_pairs = set(
        SubjectMark.objects.filter(exam_record__exam=exam)
        .values_list('exam_record_id', 'subject_id')
    )

    # দ্রুত অ্যাক্সেসের জন্য student map তৈরি
    sid_to_obj = {s.id: s for s in qs_students}  # ← full objects, select_related/prefetch already applied

    to_create, to_delete = [], []

    for sid, rid in sid_to_rid.items():
        stu = sid_to_obj.get(sid)
        if not stu:
            # student আর match করে না — ওই রেকর্ডের সব marks ডিলিট করে দাও (ইচ্ছা থাকলে record-ও drop করতে পারো)
            extras = [pair for pair in existing_pairs if pair[0] == rid]
            if extras:
                SubjectMark.objects.filter(
                    exam_record_id=rid,
                    subject_id__in=[s for (_, s) in extras]
                ).delete()
            continue

        allowed = student_allowed_exam_subject_ids(exam, stu, exam_subjects)
        existing_for_rid = {s for (erid, s) in existing_pairs if erid == rid}

        # add missing
        for s_id in allowed - existing_for_rid:
            to_create.append(SubjectMark(exam_record_id=rid, subject_id=s_id))

        # remove extras
        extras = existing_for_rid - allowed
        if extras:
            to_delete.extend((rid, s_id) for s_id in extras)

    if to_create:
        SubjectMark.objects.bulk_create(to_create, ignore_conflicts=True)

    if to_delete:
        SubjectMark.objects.filter(
            exam_record_id__in=[rid for (rid, _) in to_delete],
            subject_id__in=[sid for (_, sid) in to_delete],
        ).delete()



# from django.db.models.signals import post_save, m2m_changed, post_delete
# from django.dispatch import receiver
# from django.contrib.contenttypes.models import ContentType
# from django.apps import apps

# from .models import ExamRecord, Exam, SubjectMark
# from apps.admissions.models import Admissions, NineAdmissions, Session

# def create_exam_records_for_model(model_class, exam_instance, session):
#     """
#     Exam তৈরি হলে যে স্টুডেন্ট মডেল টার্গেট হবে সেখানে রেকর্ড বানায়।
#     - Class 6–8 => Admissions: add_program == exam.exam_class (FK exact) + add_session
#     - Class 9/10 => NineAdmissions: program/group logic 그대로
#     """
#     if model_class.__name__ == "Admissions":
#         # ✅ কঠোর FK ম্যাচ: pro_name icontains নয়
#         students = model_class.objects.filter(
#             add_program_id=getattr(exam_instance, "exam_class_id", None),
#             add_session_id=getattr(session, "id", None),
#         ).only("id")

#     else:  # NineAdmissions (আপনার আগের লজিক 그대로)
#         if exam_instance.group:
#             group_key = exam_instance.group.group_name.strip().lower()
#             classs = exam_instance.exam_class.name.strip().lower()
#             print("->", group_key, classs)
#             if group_key == 'business studies' and classs == '9':
#                 print("business - class 9")
#                 program_filter = f"nine_business"
#             elif group_key == 'business studies' and classs == '10':
#                 print("business - class 10")
#                 program_filter = f"ten_business"
#             elif group_key == 'humanities' and classs == '9':
#                 print("Class 9 - Humanities")
#                 program_filter = f"nine_arts"
#             elif group_key == 'humanities' and classs == '10':
#                 print("Class 10 - Humanities")
#                 program_filter = f"ten_arts"
#             else:
#                 print("not business")
#                 if classs == '9':
#                     program_filter = f"nine_{group_key}"
#                 else:
#                     program_filter = f"ten_{group_key}"
#         else:
#             program_filter = "nine"

#         students = model_class.objects.filter(
#             add_program__pro_name__icontains=program_filter,
#             add_session=session
#         ).only("id")

#     if not students.exists():
#         print(f"⚠️ No students in {model_class.__name__} for class='{exam_instance.exam_class}', session={session}")
#         return

#     ct = ContentType.objects.get_for_model(model_class)

#     # ডুপ্লিকেট সেফটি (signal একাধিকবার চললে)
#     existing_ids = set(
#         ExamRecord.objects.filter(exam=exam_instance, student_content_type=ct)
#         .values_list("student_object_id", flat=True)
#     )

#     to_create = [
#         ExamRecord(
#             exam=exam_instance,
#             student_content_type=ct,
#             student_object_id=s.id
#         )
#         for s in students if s.id not in existing_ids
#     ]

#     if to_create:
#         ExamRecord.objects.bulk_create(to_create, ignore_conflicts=True)
#         print(f"📥 Created {len(to_create)} ExamRecords for {model_class.__name__}.")
#     else:
#         print(f"ℹ️ Nothing to create for {model_class.__name__} (already exists).")





# # 1️⃣ Create ExamRecords when a new Exam is created
# @receiver(post_save, sender=Exam)
# def create_exam_records(sender, instance, created, **kwargs):
#     if not created:
#         return

#     print(f"🎯 Creating ExamRecord for exam: {instance.exam_name}")
#     print(f"🔎 Matching students from class: {instance.exam_class.name}")
#     print(f"🔎 Matching academic year: {instance.exam_year.name}")

#     session = Session.objects.filter(ses_name=instance.exam_year.name).first()
#     if not session:
#         print(f"⚠️ No session found for year: {instance.exam_year.name}")
#         return

#     # Normalise class name and check if exam is class 9
#     exam_class_name = instance.exam_class.name.strip().lower()
#     is_class_nine = any(token in exam_class_name for token in ["9", "nine", "10", "ten"])
#     # is_class_ten = any(token in exam_class_name for token in ["10", "ten"])

#     # If class 9 exam with group science, use NineAdmissions, else fallback
#     if is_class_nine and instance.group:
#         group_name = instance.group.group_name.strip().lower()
#         print("2nd", group_name, instance, instance.group)
#         if group_name == "science":
#             print("✅ Detected class 9/10 science exam; using NineAdmissions for records.")
#             create_exam_records_for_model(NineAdmissions, instance, session)
#             return
#         elif group_name == "business studies":
#             print("✅ Detected class 9/10 Business exam; using NineAdmissions for records.")
#             create_exam_records_for_model(NineAdmissions, instance, session)
#             return
#         elif group_name == "humanities":
#             print("✅ Detected class 9/10 Humanities exam; using NineAdmissions for records.")
#             create_exam_records_for_model(NineAdmissions, instance, session)
#             return
#         else:
#             print(f"ℹ️ Class 9/10 exam with group '{group_name}' doesn't match NineAdmissions; falling back to Admissions.")

#     # Classes 6–8 (or class 9 non-science) use Admissions
#     create_exam_records_for_model(Admissions, instance, session)


# # 2️⃣ Create SubjectMarks when ExamRecord is created
# @receiver(post_save, sender=ExamRecord)
# def create_subject_marks(sender, instance, created, **kwargs):
#     if created:
#         subjects = instance.exam.subjects.all()
#         for subject in subjects:
#             SubjectMark.objects.get_or_create(exam_record=instance, subject=subject)


# # 3️⃣ Update SubjectMarks if Exam subjects change (m2m signal)
# @receiver(m2m_changed, sender=Exam.subjects.through)
# def update_subject_marks_on_subject_change(sender, instance, action, **kwargs):
#     if action in ['post_add', 'post_remove', 'post_clear']:
#         subjects = instance.subjects.all()
#         exam_records = ExamRecord.objects.filter(exam=instance)
#         for exam_record in exam_records:
#             # ❌ Remove marks for removed subjects
#             SubjectMark.objects.filter(exam_record=exam_record).exclude(subject__in=subjects).delete()
#             # ✅ Add marks for new subjects
#             for subject in subjects:
#                 SubjectMark.objects.get_or_create(exam_record=exam_record, subject=subject)


# # 4️⃣ Update ExamRecord GPA/grade when SubjectMark is saved
# @receiver(post_save, sender=SubjectMark)
# def update_exam_record_on_mark_save(sender, instance, **kwargs):
#     exam_record = instance.exam_record
#     exam_record.calculate_total_and_grade()
#     exam_record.save()


# # 5️⃣ Update ExamRecord GPA/grade when SubjectMark is deleted
# @receiver(post_delete, sender=SubjectMark)
# def update_exam_record_on_mark_delete(sender, instance, **kwargs):
#     exam_record = instance.exam_record
#     exam_record.calculate_total_and_grade()
#     exam_record.save()
