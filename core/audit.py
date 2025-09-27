from core.models import SessionAuditLog

def log_session_action(session, user, action, changes=""):
    """
    Cria um registro de auditoria para uma sessão.
    """
    SessionAuditLog.objects.create(
        session=session,
        user=user,
        action=action,
        changes=changes
    )
