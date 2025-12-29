import json
import logging
import os
import platform
import time
import uuid
from collections import deque
from datetime import datetime, timezone
from typing import Any, Deque, Dict, Optional, Tuple

import psutil
from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import HTTPException

# Prime CPU percent so later calls are fast/non-blocking and not misleading
psutil.cpu_percent(interval=None)


# ======================
# Config (EC2 + prod friendly)
# ======================
def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _env_str(name: str, default: str) -> str:
    raw = os.getenv(name)
    return default if raw is None or raw.strip() == "" else raw.strip()


def _env_int(name: str, default: int, *, min_value: Optional[int] = None, max_value: Optional[int] = None) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        val = default
    else:
        try:
            val = int(raw)
        except ValueError:
            val = default
    if min_value is not None:
        val = max(min_value, val)
    if max_value is not None:
        val = min(max_value, val)
    return val


def _env_float(name: str, default: float, *, min_value: Optional[float] = None, max_value: Optional[float] = None) -> float:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        val = default
    else:
        try:
            val = float(raw)
        except ValueError:
            val = default
    if min_value is not None:
        val = max(min_value, val)
    if max_value is not None:
        val = min(max_value, val)
    return val


APP_NAME = _env_str("APP_NAME", "1GB Server")
APP_VERSION = _env_str("APP_VERSION", "2.0.0")

# When using systemd+gunicorn, PORT is typically not used by Flask directly.
# Gunicorn bind is configured in gunicorn.conf.py (or via systemd env).
PORT = _env_int("PORT", 8000, min_value=1, max_value=65535)

# Disk path must be configurable to avoid Windows-only assumptions and allow EC2 mount paths.
DISK_PATH = _env_str("DISK_PATH", "/")

# Health budget (RSS-based)
MAX_APP_MEMORY_MB = _env_int("MAX_APP_MEMORY_MB", 1024, min_value=64, max_value=65536)
APP_MEMORY_WARN_RATIO = _env_float("APP_MEMORY_WARN_RATIO", 0.85, min_value=0.10, max_value=0.99)

# Readiness warmup: avoid flapping while instance is booting / DNS is settling
WARMUP_SECONDS = _env_int("WARMUP_SECONDS", 2, min_value=0, max_value=60)

# Hard requirement: bounded history (60 seconds)
METRICS_HISTORY: Deque[Dict[str, Any]] = deque(maxlen=60)

# Real backend logs exposed to UI (bounded)
LOGS_BUFFER_LEN = _env_int("LOGS_BUFFER_LEN", 500, min_value=50, max_value=5000)
LOGS_BUFFER: Deque[Dict[str, Any]] = deque(maxlen=LOGS_BUFFER_LEN)

LOG_LEVEL = _env_str("LOG_LEVEL", "INFO").upper()


# ======================
# Structured Logging (JSON)
# ======================
class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "ts": _utc_iso(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        for key in ("request_id", "method", "path", "status_code", "duration_ms", "remote_addr"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, separators=(",", ":"), ensure_ascii=False)


class RingBufferLogHandler(logging.Handler):
    """
    Stores the last N logs for the dashboard.
    This makes the UI logs "real" while staying safe under 1GB RAM (bounded memory).
    """

    def emit(self, record: logging.LogRecord) -> None:
        try:
            entry: Dict[str, Any] = {
                "ts": _utc_iso(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
            }
            for key in ("request_id", "method", "path", "status_code", "duration_ms", "remote_addr"):
                if hasattr(record, key):
                    entry[key] = getattr(record, key)
            if record.exc_info:
                entry["exc_info"] = self.formatException(record.exc_info)

            LOGS_BUFFER.append(entry)
        except Exception:
            # Logging must never crash the service
            pass


logger = logging.getLogger(APP_NAME)
logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
logger.handlers.clear()
logger.propagate = False

_stream = logging.StreamHandler()
_stream.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
_stream.setFormatter(JsonFormatter())

_ring = RingBufferLogHandler()
_ring.setLevel(logging.INFO)
_ring.setFormatter(JsonFormatter())

logger.addHandler(_stream)
logger.addHandler(_ring)


# ======================
# Flask App
# ======================
app = Flask(__name__)
START_TIME = time.time()


# ======================
# Helpers
# ======================
def _app_rss_mb() -> float:
    proc = psutil.Process(os.getpid())
    return proc.memory_info().rss / 1024 / 1024


def _safe_disk_usage(path: str) -> Tuple[Optional[psutil._common.sdiskusage], Optional[str]]:
    try:
        return psutil.disk_usage(path), None
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def system_metrics() -> Dict[str, Any]:
    """
    IMPORTANT: Must match existing dashboard.js expectations:
      current.memory.total/used/available (MB)
      current.disk.total/used/free (GB)
      current.system.python_version
      current.uptime
      current.process.memory_mb
    """
    vm = psutil.virtual_memory()
    cpu_pct = psutil.cpu_percent(interval=None)

    disk, disk_err = _safe_disk_usage(DISK_PATH)

    proc = psutil.Process(os.getpid())
    rss = _app_rss_mb()

    return {
        "memory": {
            "total": round(vm.total / 1024 / 1024, 2),
            "used": round(vm.used / 1024 / 1024, 2),
            "available": round(vm.available / 1024 / 1024, 2),
            "percent": float(vm.percent),
        },
        "disk": {
            "total": round(disk.total / 1024 / 1024 / 1024, 2) if disk else None,
            "used": round(disk.used / 1024 / 1024 / 1024, 2) if disk else None,
            "free": round(disk.free / 1024 / 1024 / 1024, 2) if disk else None,
            "percent": float(disk.percent) if disk else None,
            "path": DISK_PATH,
            "error": disk_err,
        },
        "cpu": {
            "percent": float(cpu_pct),
            "cores": int(psutil.cpu_count() or 0),
        },
        "process": {
            "memory_mb": round(rss, 2),
            "threads": int(proc.num_threads()),
            "pid": int(proc.pid),
        },
        "system": {
            "platform": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "python_version": platform.python_version(),
        },
        "uptime": round(time.time() - START_TIME, 2),
        "uptime_seconds": round(time.time() - START_TIME, 2),
    }


def health_state() -> Tuple[str, Dict[str, Any]]:
    rss = _app_rss_mb()
    warn_at = MAX_APP_MEMORY_MB * APP_MEMORY_WARN_RATIO

    if rss > MAX_APP_MEMORY_MB:
        return "critical", {
            "reason": "app_rss_over_budget",
            "rss_mb": round(rss, 2),
            "budget_mb": MAX_APP_MEMORY_MB,
        }
    if rss > warn_at:
        return "warning", {
            "reason": "app_rss_near_budget",
            "rss_mb": round(rss, 2),
            "budget_mb": MAX_APP_MEMORY_MB,
            "warn_threshold_mb": round(warn_at, 2),
        }
    return "healthy", {
        "reason": "ok",
        "rss_mb": round(rss, 2),
        "budget_mb": MAX_APP_MEMORY_MB,
        "warn_threshold_mb": round(warn_at, 2),
    }


def readiness_state() -> Tuple[bool, str]:
    if (time.time() - START_TIME) < WARMUP_SECONDS:
        return False, "warming_up"

    # If disk path is misconfigured, metrics break for the dashboard: don't accept traffic.
    m = system_metrics()
    if m["disk"]["error"] is not None:
        return False, "disk_metrics_unavailable"

    status, _detail = health_state()
    if status == "critical":
        return False, "app_memory_critical"

    return True, "ready"


def _json_error(status_code: int, error: str, message: str, **extra: Any):
    payload = {
        "error": error,
        "message": message,
        "status_code": status_code,
        "timestamp": _utc_iso(),
        "request_id": getattr(request, "request_id", None),
    }
    payload.update(extra)
    return jsonify(payload), status_code


# ======================
# Request lifecycle: request-id + access logs
# ======================
@app.before_request
def _assign_request_id():
    request.request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
    request._start_ts = time.time()


@app.after_request
def _access_log(resp):
    try:
        duration_ms = round((time.time() - getattr(request, "_start_ts", time.time())) * 1000, 2)
        extra = {
            "request_id": getattr(request, "request_id", None),
            "method": request.method,
            "path": request.path,
            "status_code": resp.status_code,
            "duration_ms": duration_ms,
            "remote_addr": request.headers.get("X-Forwarded-For", request.remote_addr),
        }
        if resp.status_code >= 500:
            logger.error("request_complete", extra=extra)
        elif resp.status_code >= 400:
            logger.warning("request_complete", extra=extra)
        else:
            logger.info("request_complete", extra=extra)
    except Exception:
        pass
    return resp


# ======================
# Error handlers: always JSON for APIs
# ======================
@app.errorhandler(HTTPException)
def _handle_http_exc(e: HTTPException):
    return _json_error(
        e.code or 500,
        "http_error",
        e.description,
        path=request.path,
        method=request.method,
    )


@app.errorhandler(Exception)
def _handle_exc(e: Exception):
    logger.error(
        "unhandled_exception",
        exc_info=True,
        extra={
            "request_id": getattr(request, "request_id", None),
            "method": request.method,
            "path": request.path,
        },
    )
    return _json_error(
        500,
        "internal_server_error",
        "An internal error occurred",
        path=request.path,
        method=request.method,
    )


# ======================
# UI Routes (keep UI features)
# ======================
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.route("/docs")
def docs():
    return render_template("docs.html")


# ======================
# Probes (Kubernetes-style, also useful for EC2 + ALB)
# ======================
@app.route("/healthz")
def healthz():
    status, detail = health_state()
    if status == "critical":
        return jsonify({"status": "fail", "detail": detail, "timestamp": _utc_iso()}), 500
    return jsonify({"status": "ok", "detail": detail, "timestamp": _utc_iso()}), 200


@app.route("/readyz")
def readyz():
    ok, reason = readiness_state()
    return jsonify({"status": "ready" if ok else "not_ready", "reason": reason, "timestamp": _utc_iso()}), (200 if ok else 503)


# ======================
# APIs used by UI
# ======================
@app.route("/api/v1/health")
def api_health():
    status, detail = health_state()
    m = system_metrics()
    return jsonify(
        {
            "status": status,
            "detail": detail,
            "timestamp": _utc_iso(),
            "application_memory_mb": m["process"]["memory_mb"],
            "memory_budget_mb": MAX_APP_MEMORY_MB,
            "uptime_seconds": m["uptime_seconds"],
            "version": APP_VERSION,
            "app_name": APP_NAME,
        }
    )


@app.route("/api/v1/metrics")
def api_metrics():
    current = system_metrics()

    METRICS_HISTORY.append(
        {
            "timestamp": _utc_iso(),
            "cpu": current["cpu"]["percent"],
            "memory": current["memory"]["percent"],
        }
    )

    return jsonify({"current": current, "history": list(METRICS_HISTORY)})


@app.route("/api/v1/system")
def api_system():
    return jsonify(system_metrics())


@app.route("/api/v1/logs")
def api_logs():
    """
    Real backend logs for the dashboard “Live System Logs”.
    Query:
      ?limit=80 (1..500)
    """
    limit_raw = request.args.get("limit", "80")
    try:
        limit = max(1, min(int(limit_raw), 500))
    except Exception:
        return _json_error(400, "bad_request", "limit must be an integer")
    return jsonify({"logs": list(LOGS_BUFFER)[-limit:], "timestamp": _utc_iso()})


@app.route("/api/v1/story")
def api_story():
    return jsonify(
        {
            "title": "The Story Behind the 1GB Server",
            "why": "Engineering excellence comes from constraint, not abundance.",
            "challenge": "Run a production-grade monitoring dashboard on a real 1GB EC2 instance.",
            "timestamp": _utc_iso(),
        }
    )


@app.route("/api/v1/challenge")
def api_challenge():
    return jsonify(
        {
            "project": APP_NAME,
            "version": APP_VERSION,
            "constraints": {
                "max_app_memory_mb": MAX_APP_MEMORY_MB,
                "metrics_history_points": 60,
            },
            "features": [
                "Gunicorn production server (systemd-managed)",
                "Nginx reverse proxy on port 80",
                "Real-time dashboard (1s refresh)",
                "App RSS-based health logic",
                "Readiness gating (warmup + disk metrics + memory)",
                "Structured JSON logging + dashboard log streaming",
            ],
            "timestamp": _utc_iso(),
        }
    )


# ======================
# Startup logs (visible in /api/v1/logs)
# ======================
logger.info(f"{APP_NAME} v{APP_VERSION} booted")
logger.info(f"DISK_PATH={DISK_PATH} MAX_APP_MEMORY_MB={MAX_APP_MEMORY_MB} WARN_RATIO={APP_MEMORY_WARN_RATIO}")
logger.info(f"WARMUP_SECONDS={WARMUP_SECONDS} PORT={PORT}")
