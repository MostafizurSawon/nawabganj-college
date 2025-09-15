from django.contrib.contenttypes.models import ContentType
from apps.admissions.models import HscAdmissions, DegreeAdmission
from .models import StudentInvoice

def assign_invoice_to_students(invoice):
    # Lowercase program name check
    program_name = invoice.invoice_program.pro_name.lower()

    if "hsc" in program_name:
        model = HscAdmissions
        content_type = ContentType.objects.get_for_model(HscAdmissions)
        students = model.objects.filter(
            add_session=invoice.invoice_session,
            add_program=invoice.invoice_program,
            add_admission_group=invoice.invoice_group.group_name.lower()
        )

    elif "degree" in program_name:
        model = DegreeAdmission
        content_type = ContentType.objects.get_for_model(DegreeAdmission)
        students = model.objects.filter(
            add_session=invoice.invoice_session,
            add_program=invoice.invoice_program,
            add_admission_group=invoice.invoice_group.group_name
        )

    else:
        return 0  # Unknown type

    created = 0
    for student in students:
        _, is_created = StudentInvoice.objects.get_or_create(
            content_type=content_type,
            object_id=student.id,
            invoice=invoice,
            defaults={'note': 'Assigned automatically'}
        )
        if is_created:
            created += 1

    return created




from django.template.loader import get_template
from django.http import HttpResponse
from xhtml2pdf import pisa
import io
from django.contrib.staticfiles import finders
from django.conf import settings

def link_callback(uri, rel):
    result = finders.find(uri.replace(settings.STATIC_URL, ''))
    if result:
        return result
    return uri

def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = io.BytesIO()
    pdf = pisa.pisaDocument(
        io.BytesIO(html.encode("UTF-8")),
        result,
        link_callback=link_callback  # <-- This line is essential for static file resolution
    )
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None
