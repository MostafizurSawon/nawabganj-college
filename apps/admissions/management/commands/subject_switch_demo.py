# apps/admissions/management/commands/subject_switch_demo.py
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import F

try:
    from django.db.models.functions import Greatest
    HAS_GREATEST = True
except Exception:
    HAS_GREATEST = False

from apps.admissions.models import Subjects, HscAdmissions, Programs, Session


class Command(BaseCommand):
    help = "Demo: A->C subject switch with atomic + used_count updates. Also prints before/after."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete any A1/B1/C1 subjects & related demo student first."
        )
        parser.add_argument(
            "--no-floor",
            action="store_true",
            help="Allow used_count to go below 0 if decremented (default prevents if Greatest is available)."
        )

    def handle(self, *args, **opts):
        reset = opts.get("reset")
        no_floor = opts.get("no_floor")

        if reset:
            self.stdout.write(self.style.WARNING("Resetting existing demo data (A1/B1/C1 + demo student if any)..."))
            HscAdmissions.objects.filter(
                optional_subject__code__in=["A1", "B1", "C1"]
            ).delete()
            HscAdmissions.objects.filter(
                fourth_subject__code__in=["A1", "B1", "C1"]
            ).delete()
            Subjects.objects.filter(code__in=["A1", "B1", "C1"]).delete()

        # --- Seed subjects ---
        A, _ = Subjects.objects.get_or_create(
            code="A1",
            defaults=dict(sub_name="Civics", group="arts", limit=1, used_count=1, sub_status="active", sub_select=["optional"]),
        )
        B, _ = Subjects.objects.get_or_create(
            code="B1",
            defaults=dict(sub_name="History", group="arts", limit=1, used_count=1, sub_status="active", sub_select=["fourth"]),
        )
        C, _ = Subjects.objects.get_or_create(
            code="C1",
            defaults=dict(sub_name="Economics", group="arts", limit=2, used_count=1, sub_status="active", sub_select=["optional"]),
        )

        prog = Programs.objects.filter(pro_name__iexact="hsc").first()
        if not prog:
            prog = Programs.objects.create(pro_name="hsc")

        ses = Session.objects.first()
        if not ses:
            ses = Session.objects.create(ses_name="2025 - 2026", ses_status="active")

        stu = HscAdmissions.objects.filter(
            add_name="Test Student",
            add_admission_group="arts"
        ).first()
        if not stu:
            stu = HscAdmissions.objects.create(
                add_name="Test Student",
                add_program=prog,
                add_session=ses,
                add_admission_group="arts",
                optional_subject=A,
                fourth_subject=B,
            )

        def snapshot(label):
            data = list(Subjects.objects.filter(code__in=["A1", "B1", "C1"]).values("code", "used_count", "limit"))
            self.stdout.write(self.style.HTTP_INFO(f"{label}: {data}"))

        snapshot("INIT")

        # --- Switch A -> C ---
        with transaction.atomic():
            old_opt = stu.optional_subject_id
            new_opt = C.id

            if old_opt != new_opt:
                qs = Subjects.objects.filter(id=old_opt)
                if HAS_GREATEST and not no_floor:
                    qs.update(used_count=Greatest(F("used_count") - 1, 0))
                else:
                    qs.update(used_count=F("used_count") - 1)

                c = Subjects.objects.select_for_update().get(id=new_opt)
                if (c.limit is not None) and (c.used_count >= c.limit):
                    raise RuntimeError(f"Seat Full trying to switch to {c.sub_name} (code={c.code})")

                c.used_count = F("used_count") + 1
                c.save(update_fields=["used_count"])

                stu.optional_subject_id = new_opt
                stu.save(update_fields=["optional_subject"])

        A.refresh_from_db(); B.refresh_from_db(); C.refresh_from_db()
        snapshot("AFTER")

        self.stdout.write(self.style.SUCCESS("Done. Expectation: A decremented, C incremented, B unchanged."))
