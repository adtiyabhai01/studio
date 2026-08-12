"""Real-time telemetry for the admin portal Site Health dashboard."""

import os
import time
from datetime import datetime, timezone

from django.conf import settings
from django.db import connection

try:
    import psutil
except Exception:
    psutil = None

try:
    import pynvml
except Exception:
    pynvml = None

try:
    from cloudinary import api as cloudinary_api
except Exception:
    cloudinary_api = None

CPU_WARN = 75
CPU_CRIT = 90
STORAGE_WARN = 80
STORAGE_CRIT = 95

GIGABYTE = 1024 * 1024 * 1024
DB_STORAGE_LIMIT = int(os.environ.get("DB_STORAGE_LIMIT_BYTES", 512 * GIGABYTE // 1))
MEDIA_STORAGE_LIMIT = int(os.environ.get("MEDIA_STORAGE_LIMIT_BYTES", 25 * GIGABYTE))

HEALTH_LABELS = {
    "ok": "Normal",
    "warn": "Warning",
    "crit": "Critical",
    "na": "Unavailable",
}


def _level(percent, warn, crit):
    if percent is None:
        return "na"
    if percent >= crit:
        return "crit"
    if percent >= warn:
        return "warn"
    return "ok"


def _cpu_report():
    if psutil is None:
        return {"available": False, "level": "na", "percent": None, "cores": None, "error": "psutil not installed"}
    try:
        cores = os.cpu_count() or None
        percent = psutil.cpu_percent(interval=0.25)
        return {"available": True, "level": _level(percent, CPU_WARN, CPU_CRIT), "percent": round(percent, 1), "cores": cores}
    except Exception as exc:
        return {"available": False, "level": "na", "percent": None, "cores": None, "error": str(exc)[:200]}


def _gpu_report():
    if pynvml is None:
        return {"available": False, "level": "na", "percent": None, "name": None, "error": "gpu monitoring library unavailable"}
    try:
        pynvml.nvmlInit()
    except Exception:
        return {"available": False, "level": "na", "percent": None, "name": None, "error": "no nvidia gpu detected"}
    try:
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        name = pynvml.nvmlDeviceGetName(handle)
        rates = pynvml.nvmlDeviceGetUtilizationRates(handle)
        load = float(getattr(rates, "gpu", 0) or 0)
        return {
            "available": True,
            "level": _level(load, CPU_WARN, CPU_CRIT),
            "percent": round(load, 1),
            "name": name,
        }
    except Exception as exc:
        return {"available": False, "level": "na", "percent": None, "name": None, "error": str(exc)[:200]}
    finally:
        try:
            pynvml.nvmlShutdown()
        except Exception:
            pass


def _db_report():
    engine = settings.DATABASES["default"].get("ENGINE") or ""
    engine_label = "PostgreSQL" if "postgres" in engine else ("SQLite" if "sqlite" in engine else engine)
    used = None
    try:
        with connection.cursor() as cursor:
            if "postgres" in engine:
                cursor.execute("SELECT pg_database_size(current_database())")
            else:
                cursor.execute("SELECT page_count * page_size FROM pragma_page_count(), pragma_page_size()")
            row = cursor.fetchone()
            if row and row[0] is not None:
                used = int(row[0])
    except Exception:
        used = None
    if used is None:
        name = settings.DATABASES["default"].get("NAME")
        if name and "sqlite" in engine:
            try:
                used = os.path.getsize(str(name))
            except Exception:
                used = None
    if used is None:
        return {
            "available": False, "level": "na", "engine": engine_label,
            "used": None, "limit": None, "total": None, "available": None,
            "percent": None, "error": "could not measure database size",
        }
    limit = DB_STORAGE_LIMIT
    total = limit
    avail = max(0, total - used)
    percent = min(100.0, used / total * 100.0) if total else None
    return {
        "available": True, "level": _level(percent, STORAGE_WARN, STORAGE_CRIT),
        "engine": engine_label, "used": used, "limit": limit, "total": total,
        "available": avail, "percent": round(percent, 1),
    }


_USAGE_CACHE = {"at": 0.0, "data": None}
_USAGE_CACHE_TTL = 300


def _usage_report():
    if cloudinary_api is None or not settings.CLOUDINARY_STORAGE.get("CLOUD_NAME"):
        return {"error": "cloudinary not configured"}
    now = time.time()
    try:
        if _USAGE_CACHE["data"] is None or now - _USAGE_CACHE["at"] >= _USAGE_CACHE_TTL:
            _USAGE_CACHE["data"] = cloudinary_api.usage()
            _USAGE_CACHE["at"] = now
        usage = _USAGE_CACHE["data"]

        def _sum_bytes(resource_type, max_pages=20, max_results=500):
            total = 0
            next_cursor = None
            for _ in range(max_pages):
                opts = {} if not next_cursor else {"next_cursor": next_cursor}
                payload = cloudinary_api.resources(
                    resource_type=resource_type,
                    max_results=max_results,
                    fields="bytes",
                    **opts,
                )
                for res in payload.get("resources") or []:
                    total += int(res.get("bytes") or 0)
                next_cursor = payload.get("next_cursor")
                if not next_cursor:
                    break
            return total

        image_bytes = _sum_bytes("image")
        video_bytes = _sum_bytes("video")
    except Exception as exc:
        return {"error": str(exc)[:200]}

    credits = (usage.get("credits") or {}).get("limit")
    plan_limit = int(credits) * GIGABYTE if credits else MEDIA_STORAGE_LIMIT
    limit = int(os.environ.get("MEDIA_STORAGE_LIMIT_BYTES", plan_limit))

    reports = {}
    for key, used in (("photos", image_bytes), ("videos", video_bytes), ("overall", image_bytes + video_bytes)):
        avail = max(0, limit - used)
        percent = min(100.0, used / limit * 100.0) if limit else None
        reports[key] = {
            "available": True,
            "level": _level(percent, STORAGE_WARN, STORAGE_CRIT),
            "used": int(used), "limit": int(limit), "total": int(limit),
            "available": int(avail), "percent": round(percent, 1),
            "engine": "Cloudinary",
        }
    reports["plan"] = usage.get("plan")
    return reports


def build_health_report():
    media = _usage_report()
    media_ok = isinstance(media, dict) and "error" not in media

    db = _db_report()
    report = {
        "cpu": _cpu_report(),
        "gpu": _gpu_report(),
        "database": db,
        "photos": media.get("photos") if media_ok else None,
        "videos": media.get("videos") if media_ok else None,
        "overall": None,
        "media_error": media.get("error") if isinstance(media, dict) else None,
        "media_plan": media.get("plan") if media_ok else None,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    db_used = db.get("used") if db and db.get("available") else 0
    db_limit = db.get("limit") if db and db.get("available") else 0
    photos = report["photos"]
    videos = report["videos"]
    media_used = (photos["used"] if photos else 0) + (videos["used"] if videos else 0)
    media_limit = (photos["limit"] if photos else 0) or (videos["limit"] if videos else 0)

    if db_limit or media_limit:
        used = db_used + media_used
        total = db_limit + media_limit
        avail = max(0, total - used)
        percent = min(100.0, used / total * 100.0) if total else 0.0
        report["overall"] = {
            "available": True,
            "level": _level(percent, STORAGE_WARN, STORAGE_CRIT),
            "used": int(used), "limit": int(total), "total": int(total),
            "available": int(avail), "percent": round(percent, 1),
        }
    return report