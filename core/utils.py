from .models import SessionAuditLog
from django.http import JsonResponse
from django.contrib.auth.views import redirect_to_login

def register_audit(session, user, action, changes=''):
    SessionAuditLog.objects.create(
        session=session,
        user=user,
        action=action,
        changes=changes
    )

def ajax_login_required(view_func):
    from functools import wraps
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'error': 'login_required'}, status=403)
            else:
                return redirect_to_login(request.get_full_path())
        return view_func(request, *args, **kwargs)
    return wrapper
