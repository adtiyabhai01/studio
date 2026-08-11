import os
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'myproject'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

_IMPORT_ERROR = None

try:
    from myproject.wsgi import application as _application
except Exception:
    _IMPORT_ERROR = traceback.format_exc()
    _application = None


def application(environ, start_response):
    if _application is not None:
        return _application(environ, start_response)
    start_response("500 Internal Server Error", [("Content-Type", "text/plain; charset=utf-8")])
    return [_IMPORT_ERROR.encode("utf-8")]
