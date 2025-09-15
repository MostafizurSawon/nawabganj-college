# apps/exams/utils.py
from apps.admissions.models import HscAdmissions

GROUP_MAP = {
    'science': 'science',
    'humanities': 'arts',       
    'business': 'commerce',      
}

def get_hsc_admissions_for_exam(exam):
    """
    Exam.exam_class (Programs), Exam.exam_session (Session), Exam.group_name → 
    মিলিয়ে HscAdmissions queryset রিটার্ন করবে।
    """
    qs = HscAdmissions.objects.filter(
        add_program=exam.exam_class,
        add_session=exam.exam_session,
    )

    grp = (exam.group_name or '').strip().lower()
    if grp in GROUP_MAP:
        qs = qs.filter(add_admission_group=GROUP_MAP[grp])

    return qs





import re

def _extract_code_tokens(text: str):
    """
    "107 - 108", "PHY-101" ইত্যাদি থেকে সংখ্যাগুলো বের করে set হিসেবে দেয়: {"107","108","101"}
    """
    if not text:
        return set()
    return set(re.findall(r"\d+", str(text)))

def _norm(s: str):
    return (s or "").strip().lower()

def student_allowed_exam_subject_ids(exam, hsc_student, exam_subjects):
    """
    exam_subjects: iterable of Subject (exams app) already selected in Exam
    hsc_student:   HscAdmissions instance (admissions app)
    return: set of exam Subject.id যেগুলো ওই ছাত্রের সাথে apply করবে
    """
    # 1) ছাত্রের সব subject (M2M + singles) জড়ো করি
    adm_subs = list(hsc_student.subjects.all())
    for f in ("main_subject", "fourth_subject", "optional_subject", "optional_subject_2"):
        obj = getattr(hsc_student, f, None)
        if obj:
            adm_subs.append(obj)

    # 2) ছাত্র‑side code/name সেট বানাই
    stu_code_tokens = set()
    stu_names = set()
    for s in adm_subs:
        stu_code_tokens |= _extract_code_tokens(s.code)
        stu_names.add(_norm(getattr(s, "sub_name", None)))  # admissions.Subjects.sub_name

    # 3) exam‑side subjects ফিল্টার
    allowed = set()
    for es in exam_subjects:
        code_match = False
        if es.code:
            es_tokens = _extract_code_tokens(es.code)  # exams.Subject.code
            if es_tokens & stu_code_tokens:
                code_match = True

        name_match = _norm(es.name) in stu_names  # fallback by name

        if code_match or name_match:
            allowed.add(es.id)

    return allowed
