import sys
import traceback
from datetime import timedelta

from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from .maintenance import maintenance_enabled

BYPASS_PREFIXES = (
    "/admin",
    "/admin-portal",
    "/static/",
    "/media/",
    "/maintenance/mode",
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


class VisitTrackingMiddleware:
    """Log one SiteVisit row per public page view so the studio can see who came."""

    SKIP_PREFIXES = (
        "/admin",
        "/admin-portal",
        "/static/",
        "/media/",
        "/maintenance/mode",
        "/theme.json",
        "/sitemap.xml",
        "/robots.txt",
        "/favicon",
        "/health",
        "/maintenance",
    )

    BOT_AGENTS = ("bot", "spider", "crawl", "slurp", "bing", "yandex", "baidu", "duckduck")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        self._record(request)
        return response

    def _record(self, request):
        try:
            if request.method != "GET":
                return
            path = request.path
            for prefix in self.SKIP_PREFIXES:
                if path == prefix or path.startswith(prefix.rstrip("/") + "/"):
                    return
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return
            user = getattr(request, "user", None)
            if user is not None and user.is_authenticated and (user.is_staff or user.is_superuser):
                return
            agent = request.META.get("HTTP_USER_AGENT", "") or ""
            agent_lower = agent.lower()
            if any(part in agent_lower for part in self.BOT_AGENTS):
                return
            ip = request.META.get("HTTP_X_FORWARDED_FOR") or request.META.get("REMOTE_ADDR") or ""
            ip = ip.split(",")[0].strip()
            city, region, country = lookup_location(ip)

            from .models import SiteVisit

            SiteVisit.objects.create(
                path=path,
                ip=ip[:64],
                city=city[:120],
                region=region[:120],
                country=country[:120],
                referrer=(request.META.get("HTTP_REFERER", "") or "")[:500],
                user_agent=agent[:300],
            )
            _prune_old_visits()
        except Exception:
            pass


_LAST_PRUNE = [0.0]


def _prune_old_visits():
    """Keep the table small — oldest beyond 60 days or 5000 latest rows are dropped."""
    import time

    now = time.time()
    if now - _LAST_PRUNE[0] < 3600:
        return
    _LAST_PRUNE[0] = now
    from .models import SiteVisit

    SiteVisit.objects.filter(created_at__lt=timezone.now() - timedelta(days=60)).delete()
    ids = list(SiteVisit.objects.order_by("-id").values_list("id", flat=True)[5000:])
    if ids:
        SiteVisit.objects.filter(id__in=ids).delete()


_LOCATION_CACHE = {}
_LOCATION_CACHE_SIZE = 256


def lookup_location(ip):
    """Best-effort city/country from the IP via ip-api.com (free, no key)."""
    if not ip or ip in ("127.0.0.1", "::1", "localhost"):
        return "", "", ""
    if ip in _LOCATION_CACHE:
        return _LOCATION_CACHE[ip]
    try:
        import json
        import urllib.request

        url = f"http://ip-api.com/json/{ip}?fields=status,city,region,country"
        with urllib.request.urlopen(url, timeout=2) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if data.get("status") == "success":
            result = (data.get("city", "") or "", data.get("region", "") or "", data.get("country", "") or "")
        else:
            result = ("", "", "")
    except Exception:
        result = ("", "", "")
    if len(_LOCATION_CACHE) < _LOCATION_CACHE_SIZE:
        _LOCATION_CACHE[ip] = result
    return result


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
