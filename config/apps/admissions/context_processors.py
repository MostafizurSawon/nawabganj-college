from .models import Session

def active_session(request):
    session_id = request.session.get('active_session_id')
    session_obj = None
    if session_id:
        try:
            session_obj = Session.objects.get(id=session_id)
        except Session.DoesNotExist:
            session_obj = None
    return {'active_session': session_obj}
