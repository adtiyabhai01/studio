import re

from django import template

register = template.Library()

# Only allow safe Cloudinary transformation tokens (letters, digits, _ , : .).
_SAFE_OPTS_RE = re.compile(r"^[a-zA-Z0-9_,:.]+$")


@register.filter
def imgopt(url, options=""):
    """
    Inject delivery-only Cloudinary transformations into an /upload/ URL.
    The original uploaded asset is never modified — this only changes how the
    file is delivered to the browser. Non-Cloudinary URLs (local dev media)
    and already-optimised URLs pass through unchanged.
    """
    if not url:
        return url
    url = str(url)
    opts = (options or "").strip().strip("'\"")
    if not opts or not _SAFE_OPTS_RE.match(opts):
        return url
    if "/upload/" not in url or "f_auto" in url:
        return url
    return url.replace("/upload/", f"/upload/{opts}/", 1)
