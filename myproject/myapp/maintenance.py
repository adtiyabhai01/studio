"""Maintenance-mode flag, cached lightly so public pages read it cheaply."""

import time

from .models import SiteSettings

_STATE = {"on": False, "at": 0.0}
_TTL = 3.0


def maintenance_enabled():
    now = time.time()
    if now - _STATE["at"] >= _TTL:
        try:
            obj = SiteSettings.objects.first()
            _STATE["on"] = bool(obj and obj.maintenance_mode)
        except Exception:
            _STATE["on"] = False
        _STATE["at"] = now
    return _STATE["on"]