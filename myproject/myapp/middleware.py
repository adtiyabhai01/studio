import sys
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
    """Temporary diagnostic: render the exception traceback in the browser."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if not (request.path.startswith("/admin") and request.user.is_authenticated):
            pass
        exc_type, exc_value, tb = sys.exc_info()
        detail = "".join(traceback.format_exception(exc_type, exc_value, tb))
        html = f"<pre style='font-size:13px'>{detail}</pre>"
        return HttpResponse(html, status=500, content_type="text/html")
