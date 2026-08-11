import sys
import traceback

from django.http import HttpResponse


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
