"""DB-backed error logging used by the admin portal's Logs tab.

`record_error` is safe to call from anywhere (middleware, views, management
commands) and never raises — a failing log write must not break the request
that produced the error. Text fields are truncated so they stay friendly to
both SQLite and PostgreSQL limits.
"""


def record_error(
    level="ERROR",
    message="",
    traceback="",
    path="",
    method="",
    status_code=None,
    ip="",
    user="",
    user_agent="",
):
    """Persist a single row in the ErrorLog table as best-effort."""
    from .models import ErrorLog

    try:
        ErrorLog.objects.create(
            level=level,
            message=(message or "").strip()[:2000],
            traceback=(traceback or "").strip(),
            path=(path or "")[:500],
            method=(method or "")[:10],
            status_code=status_code,
            ip=(ip or "")[:64],
            user=(user or "")[:150],
            user_agent=(user_agent or "")[:500],
        )
    except Exception:
        # Never let logging break the real request.
        pass