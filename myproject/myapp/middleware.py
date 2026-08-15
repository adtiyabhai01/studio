import traceback

from django.http import HttpResponse
from django.shortcuts import render

from .maintenance import maintenance_enabled

BYPASS_PREFIXES = (
    "/admin",
    "/admin-portal",
    "/static/",
    "/media/",
    "/maintenance/mode",
    "/api/visitor",
    "/theme.json",
    "/sitemap.xml",
    "/robots.txt",
    "/favicon",
    "/health",
)


class MaintenanceModeMiddleware:
    """Show a maintenance screen across the whole site while maintenance is on.

    Admin/portal routes and logged-in staff keep working so the mode can be
    switched back off. Public visitors see the maintenance page on any URL.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not self._bypass(request) and maintenance_enabled():
            user_ok = request.user.is_authenticated and (
                request.user.is_staff or request.user.is_superuser
            )
            if not user_ok:
                return maintenance_response(request)
        return self.get_response(request)

    @staticmethod
    def _bypass(request):
        if request.method != "GET":
            return True
        path = request.path
        for prefix in BYPASS_PREFIXES:
            if path == prefix or path.startswith(prefix.rstrip("/") + "/"):
                return True
        return False


def maintenance_response(request):
    from .models import SiteSettings

    site = SiteSettings.load()
    return render(
        request,
        "maintenance.html",
        {"brand_name": site.brand_name, "logo": site.logo.url if site.logo else None, "_maintenance": True},
        status=503,
    )


class ShowErrorsMiddleware:
    """Record every site error into the ErrorLog table so it can be reviewed in
    the admin portal's Logs tab. For real exceptions an admin also sees the full
    traceback in the browser; everyone else gets Django's normal response."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from .logdb import record_error
        from .views import _client_ip

        is_staff = False
        username = ""
        user = getattr(request, "user", None)
        if user is not None:
            try:
                authenticated = bool(user.is_authenticated)
            except Exception:
                authenticated = False
            is_staff = authenticated and (user.is_staff or user.is_superuser)
            if authenticated:
                username = user.get_username() or ""

        response = self.get_response(request)
        # Exceptions are persisted in process_exception — don't double-log them.
        if getattr(request, "_ap_log_recorded", False):
            return response
        status = getattr(response, "status_code", 200)
        if status >= 400:
            record_error(
                level="ERROR" if status >= 500 else "WARNING",
                message=f"HTTP {status} on {request.path}",
                path=request.path,
                method=request.method,
                status_code=status,
                ip=_client_ip(request),
                user=username,
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
            )
        return response

    def process_exception(self, request, exception):
        from django.http import Http404

        from .logdb import record_error
        from .views import _client_ip

        is_staff = False
        username = ""
        user = getattr(request, "user", None)
        if user is not None:
            try:
                authenticated = bool(user.is_authenticated)
            except Exception:
                authenticated = False
            is_staff = authenticated and (user.is_staff or user.is_superuser)
            if authenticated:
                username = user.get_username() or ""
        is_404 = isinstance(exception, Http404)

        try:
            detail = "".join(
                traceback.format_exception(type(exception), exception, exception.__traceback__)
            )
        except Exception:
            detail = str(exception)

        record_error(
            level="WARNING" if is_404 else "ERROR",
            message=str(exception) or (request.path if is_404 else type(exception).__name__),
            traceback=detail,
            path=request.path,
            method=request.method,
            status_code=404 if is_404 else 500,
            ip=_client_ip(request),
            user=username,
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )
        request._ap_log_recorded = True
        if is_staff and not is_404:
            return HttpResponse(detail, status=500, content_type="text/plain")
        return None
