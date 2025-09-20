# apps/exams/signals.py
from django.db import transaction
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver

from functools import reduce
import operator
from django.db.models import Q

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
    """
    1) Exam-এর টার্গেটেড HSC ছাত্রদের বের করে ExamRecord bulk create করে
    2) Exam.subjects অনুযায়ী SubjectMark add/remove সিঙ্ক করে
    """
    # --- 1) Target students (full objects for subject matching) ---
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

    # create missing ExamRecord
    new_records = [
        ExamRecord(exam=exam, hsc_student_id=sid)
        for sid in qs_students.values_list('id', flat=True)
        if sid not in sid_to_rid
    ]
    if new_records:
        ExamRecord.objects.bulk_create(new_records, ignore_conflicts=True, batch_size=1000)
        # refresh map after insert
        sid_to_rid = {
            er.hsc_student_id: er.id
            for er in ExamRecord.objects.filter(exam=exam).only('id', 'hsc_student_id')
        }

    # --- 2) Subject marks sync ---
    exam_subjects = list(exam.subjects.all())
    if not exam_subjects:
        # কোনো subject নাই → পুরোনো marks মুছে দাও, done
        SubjectMark.objects.filter(exam_record__exam=exam).delete()
        return

    existing_pairs = set(
        SubjectMark.objects.filter(exam_record__exam=exam)
        .values_list('exam_record_id', 'subject_id')
    )

    # দ্রুত অ্যাক্সেসের জন্য student map (full objects)
    sid_to_obj = {s.id: s for s in qs_students}

    to_create, to_delete = [], []

    for sid, rid in sid_to_rid.items():
        stu = sid_to_obj.get(sid)
        if not stu:
            # student আর match করে না — ওই record-এর সব marks ডিলিট
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
        SubjectMark.objects.bulk_create(to_create, ignore_conflicts=True, batch_size=1000)

    if to_delete:
        # exact pair-wise delete (cross-pair ঝামেলা নেই)
        conds = [Q(exam_record_id=rid, subject_id=sid) for (rid, sid) in to_delete]
        SubjectMark.objects.filter(reduce(operator.or_, conds)).delete()
