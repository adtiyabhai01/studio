import os
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'myproject'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

try:
    from myproject.wsgi import application as app
except Exception:
    tb = traceback.format_exc()

    def app(environ, start_response):
        start_response("500 Internal Server Error", [("Content-Type", "text/plain; charset=utf-8")])
        return [tb.encode("utf-8")]
