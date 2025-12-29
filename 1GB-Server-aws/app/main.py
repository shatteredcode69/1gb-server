from __future__ import annotations

from flask import Flask, jsonify, render_template
import psutil
import platform
import time
from datetime import datetime, timezone
import os

# Flask defaults expect:
#   templates/ for HTML
#   static/ for css/js
app = Flask(__name__)

# Prime cpu_percent so the first call isn't always 0.0
psutil.cpu_percent(interval=None)

START_TS = time.time()
METRICS_HISTORY: list[dict] = []  # last 60 points


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _disk_path() -> str:
    """
    Pick a valid disk root depending on OS.
    Linux/Ubuntu: '/'
    Windows: 'C:\\'
    Allow override via env DISK_PATH for special mounts.
    """
    override = os.getenv("DISK_PATH")
    if override:
        return override

    return "C:\\" if platform.system().lower().startswith("win") else "/"


def _system_uptime_seconds() -> float:
    # Instance uptime (not app uptime)
    return max(0.0, time.time() - psutil.boot_time())


def _app_uptime_seconds() -> float:
    return max(0.0, time.time() - START_TS)


def _net_io() -> dict:
    io = psutil.net_io_counters()
    return {
        "bytes_sent_mb": round(io.bytes_sent / 1024 / 1024, 2),
        "bytes_recv_mb": round(io.bytes_recv / 1024 / 1024, 2),
        "packets_sent": int(io.packets_sent),
        "packets_recv": int(io.packets_recv),
    }


def get_system_metrics() -> dict:
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage(_disk_path())
    proc = psutil.Process()
    rss_mb = proc.memory_info().rss / 1024 / 1024

    cpu_percent = psutil.cpu_percent(interval=None)

    return {
        "cpu": {
            "percent": round(float(cpu_percent), 2),
            "cores": int(psutil.cpu_count(logical=True) or 1),
        },
        "memory": {
            "total_mb": round(mem.total / 1024 / 1024, 2),
            "used_mb": round(mem.used / 1024 / 1024, 2),
            "available_mb": round(mem.available / 1024 / 1024, 2),
            "percent": round(mem.percent, 2),
        },
        "disk": {
            "path": _disk_path(),
            "total_gb": round(disk.total / 1024 / 1024 / 1024, 2),
            "used_gb": round(disk.used / 1024 / 1024 / 1024, 2),
            "free_gb": round(disk.free / 1024 / 1024 / 1024, 2),
            "percent": round(disk.percent, 2),
        },
        "network": _net_io(),
        "process": {
            "rss_mb": round(rss_mb, 2),
            "threads": int(proc.num_threads()),
        },
        "system": {
            "platform": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "python_version": platform.python_version(),
            "hostname": platform.node(),
        },
        # Provide both, but keep "uptime" as INSTANCE uptime (EC2 proof)
        "uptime": round(_system_uptime_seconds(), 2),
        "app_uptime": round(_app_uptime_seconds(), 2),
    }


def _health_status(memory_percent: float) -> str:
    # healthy/warning/critical
    if memory_percent >= 90:
        return "critical"
    if memory_percent >= 80:
        return "warning"
    return "healthy"


@app.get("/")
def home():
    return render_template("index.html")


@app.get("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.get("/docs")
def docs():
    return render_template("docs.html")


@app.get("/api/v1/health")
def health():
    current = get_system_metrics()
    app_rss_mb = float(current["process"]["rss_mb"])
    memory_budget_mb = 1024.0
    headroom_mb = round(memory_budget_mb - app_rss_mb, 2)

    return jsonify(
        {
            "status": _health_status(float(current["memory"]["percent"])),
            "timestamp": _utc_iso(),
            "app_rss_mb": round(app_rss_mb, 2),
            "memory_budget_mb": 1024,
            "headroom_mb": headroom_mb,
            "is_1gb_ready": bool(app_rss_mb < memory_budget_mb),
            "metrics": current,
            "developer": "Muhammad Abbas",
            "version": "1.0.0",
        }
    )


@app.get("/api/v1/metrics")
def metrics():
    current = get_system_metrics()

    METRICS_HISTORY.append(
        {
            "timestamp": _utc_iso(),
            "memory": float(current["memory"]["percent"]),
            "cpu": float(current["cpu"]["percent"]),
        }
    )
    if len(METRICS_HISTORY) > 60:
        del METRICS_HISTORY[0 : len(METRICS_HISTORY) - 60]

    return jsonify({"current": current, "history": METRICS_HISTORY})


@app.get("/api/v1/system")
def system():
    return jsonify(get_system_metrics())


@app.get("/api/v1/story")
def story():
    return jsonify(
        {
            "title": "The 1GB Server: A Developer's Journey",
            "author": "Muhammad Abbas",
            "tagline": "Building Excellence Under Constraint",
            "story": {
                "chapter_1": "In a world obsessed with unlimited resources...",
                "chapter_2": "One developer chose the path of optimization...",
                "chapter_3": "And built something remarkable with just 1GB of RAM.",
                "moral": "True engineering skill shines brightest under constraints.",
            },
            "stats": {
                "memory_budget": "1024 MB",
                "deployment_time": "<30 seconds",
                "uptime_target": "99.9%",
            },
        }
    )


@app.get("/api/v1/challenge")
def challenge():
    # This endpoint matches docs.html and is the canonical route.
    return jsonify(
        {
            "name": "1GB Server",
            "objective": "Build a production-grade system with only 1GB RAM",
            "components": [
                "Flask Web Application",
                "Real-time Monitoring Dashboard",
                "Production Deployment (Nginx + Gunicorn + systemd)",
                "Health Monitoring",
                "Performance Optimization",
            ],
            "skills_learned": [
                "Resource Optimization",
                "DevOps Best Practices",
                "System Monitoring",
                "Production Deployment",
                "Performance Tuning",
            ],
            "developer": {"name": "Muhammad Abbas", "role": "Aspiring Cloud Enthusiast"},
        }
    )


# Backward-compatible alias for your old mixed-case route:
@app.get("/api/v1/Server")
def challenge_legacy():
    return challenge()


if __name__ == "__main__":
    # Local-only convenience. Production must use Gunicorn + systemd.
    # IMPORTANT: no debug/reloader here (keeps memory low and avoids double-process).
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
