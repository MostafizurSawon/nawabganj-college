from apps.admissions.models import HscAdmissions
import re

# UI → DB mapping
GROUP_MAP = {
    'science': 'science',
    'humanities': 'arts',     # UI 'Humanities' → DB 'arts'
    'business': 'commerce',   # UI 'Business'   → DB 'commerce'
}

def _canon(s: str) -> str:
    return (s or "").strip().lower()


def get_hsc_admissions_for_exam(exam):
    """
    Exam.exam_class (Programs FK), Exam.exam_session (Session FK), Exam.group_name মিলিয়ে
    HscAdmissions queryset রিটার্ন করবে।
    """
    if not getattr(exam, "exam_class_id", None) or not getattr(exam, "exam_session_id", None):
        return HscAdmissions.objects.none()

    qs = HscAdmissions.objects.filter(
        add_program=exam.exam_class,     # exact FK match
        add_session=exam.exam_session,   # exact FK match
    )

    grp_in = _canon(getattr(exam, "group_name", None))
    grp = GROUP_MAP.get(grp_in)
    if grp:
        qs = qs.filter(add_admission_group=grp)

    return qs.distinct()


# ==============================
# Subject matching helpers
# ==============================

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

    # 2) ছাত্র-side সেট বানাই
    stu_code_tokens, stu_names, stu_codes_exact = set(), set(), set()
    for s in adm_subs:
        if getattr(s, "code", None):
            stu_code_tokens |= _extract_code_tokens(s.code)
            stu_codes_exact.add(_norm(s.code))
        stu_names.add(_norm(getattr(s, "sub_name", None)))

    # 3) exam-side subjects ফিল্টার
    allowed = set()
    for es in exam_subjects:
        exact_code_match = bool(getattr(es, "code", None) and _norm(es.code) in stu_codes_exact)

        token_match = False
        if getattr(es, "code", None):
            token_match = bool(_extract_code_tokens(es.code) & stu_code_tokens)

        name_match = _norm(getattr(es, "name", None)) in stu_names

        if exact_code_match or token_match or name_match:
            allowed.add(es.id)

    return allowed
