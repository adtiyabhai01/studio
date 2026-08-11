import json
import os
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

from django.core.files.base import ContentFile, File
from django.core.files.storage import Storage
from django.utils.encoding import force_bytes

API_BASE = "https://api.vercel.com/v3/blobs"


class VercelBlobStorage(Storage):
    """Django storage backend backed by Vercel Blob Storage.

    The FileField ``name`` is stored as the full public Blob URL returned at
    upload time, so ``url()`` simply returns the stored name.
    """

    def __init__(self, access="public", token=None):
        self.access = access
        self.token = token or os.environ.get("BLOB_READ_WRITE_TOKEN", "")

    # -- helpers ---------------------------------------------------------

    def _auth_headers(self, content_type="application/octet-stream"):
        return {
            "Authorization": "Bearer %s" % self.token,
            "Content-Type": content_type,
        }

    def _request(self, url, method="GET", headers=None, body=None):
        req = Request(url, data=body, method=method, headers=headers or {})
        try:
            return urlopen(req, timeout=30)
        except HTTPError as exc:
            raise IOError(
                "Vercel Blob error (%s): %s" % (exc.code, exc.read().decode(errors="replace"))
            )

    # -- Storage API -----------------------------------------------------

    def _save(self, name, content):
        if not self.token:
            raise ValueError("BLOB_READ_WRITE_TOKEN is not configured.")
        content.seek(0)
        data = force_bytes(content.read())
        ctype = getattr(content, "content_type", None) or "application/octet-stream"
        url = "%s?pathname=%s&access=%s&addRandomSuffix=true&contentType=%s" % (
            API_BASE,
            quote(name),
            quote(self.access),
            quote(ctype),
        )
        resp = self._request(url, method="POST", headers=self._auth_headers(ctype), body=data)
        payload = json.loads(resp.read().decode("utf-8"))
        return payload["url"]

    def url(self, name):
        return name

    def exists(self, name):
        try:
            resp = self._request(name, method="HEAD")
            return resp.status == 200
        except Exception:
            return False

    def size(self, name):
        resp = self._request(name, method="HEAD")
        return int(resp.headers.get("Content-Length", 0))

    def open(self, name, mode="rb"):
        resp = self._request(name, method="GET")
        return File(ContentFile(resp.read()), name=name)

    def delete(self, name):
        if not name:
            return
        url = "%s?url=%s" % (API_BASE, quote(name))
        try:
            self._request(url, method="DELETE", headers=self._auth_headers())
        except Exception:
            pass

    def get_available_name(self, name, max_length=None):
        # The Blob server adds a random suffix, so local collision handling is
        # not needed.
        return name
