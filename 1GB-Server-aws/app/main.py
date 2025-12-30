from flask import Flask, jsonify, render_template
import psutil
import os
from datetime import datetime
import platform
import time
import urllib.request

app = Flask(__name__)

metrics_history = []
start_time = time.time()

# ---- OS-safe defaults ----
DEFAULT_DISK_PATH = "C:\\" if os.name == "nt" else "/"
DISK_PATH = os.environ.get("DISK_PATH", DEFAULT_DISK_PATH)

# Prime CPU so the first read isn't always 0.0
psutil.cpu_percent(interval=None)


def _read_memtotal_mb_from_proc():
    """Best-effort MemTotal from /proc/meminfo (Linux)."""
    try:
        with open("/proc/meminfo", "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    # Example: "MemTotal:       1024000 kB"
                    kb = int(line.split()[1])
                    return round(kb / 1024.0, 2)
    except Exception:
        return None
    return None


def _get_ec2_metadata(timeout_sec=0.2):
    """
    Best-effort EC2 instance metadata (IMDSv2).
    Returns {} if not on EC2 or if blocked.
    """
    base = "http://169.254.169.254/latest"
    try:
        # IMDSv2 token
        token_req = urllib.request.Request(
            f"{base}/api/token",
            method="PUT",
            headers={"X-aws-ec2-metadata-token-ttl-seconds": "60"},
        )
        with urllib.request.urlopen(token_req, timeout=timeout_sec) as resp:
            token = resp.read().decode("utf-8")

        def fetch(path):
            req = urllib.request.Request(
                f"{base}/meta-data/{path}",
                headers={"X-aws-ec2-metadata-token": token},
            )
            with urllib.request.urlopen(req, timeout=timeout_sec) as r:
                return r.read().decode("utf-8")

        return {
            "instance_id": fetch("instance-id"),
            "instance_type": fetch("instance-type"),
            "availability_zone": fetch("placement/availability-zone"),
        }
    except Exception:
        return {}


def get_system_metrics():
    memory = psutil.virtual_memory()

    # Linux-safe disk path (configurable via DISK_PATH)
    disk = psutil.disk_usage(DISK_PATH)

    # Non-blocking CPU read
    cpu_percent = psutil.cpu_percent(interval=None)

    process = psutil.Process()
    process_memory = process.memory_info().rss / 1024 / 1024
    uptime = time.time() - start_time

    proof = {
        "disk_path": DISK_PATH,
        "memtotal_proc_mb": _read_memtotal_mb_from_proc(),
        "ec2": _get_ec2_metadata(),
    }

    return {
        "memory": {
            "total": round(memory.total / 1024 / 1024, 2),
            "used": round(memory.used / 1024 / 1024, 2),
            "available": round(memory.available / 1024 / 1024, 2),
            "percent": memory.percent,
        },
        "disk": {
            "total": round(disk.total / 1024 / 1024 / 1024, 2),
            "used": round(disk.used / 1024 / 1024 / 1024, 2),
            "free": round(disk.free / 1024 / 1024 / 1024, 2),
            "percent": disk.percent,
        },
        "cpu": {
            "percent": float(cpu_percent),
            "cores": psutil.cpu_count(),
        },
        "process": {
            "memory_mb": round(process_memory, 2),
            "threads": process.num_threads(),
        },
        "system": {
            "platform": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "python_version": platform.python_version(),
        },
        "uptime": uptime,
        "proof": proof,
    }


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.route("/docs")
def docs():
    return render_template("docs.html")


@app.route("/api/v1/health")
def health():
    metrics = get_system_metrics()
    process = psutil.Process()

    status = "healthy"
    if metrics["memory"]["percent"] > 95:
        status = "critical"
    elif metrics["memory"]["percent"] > 90:
        status = "warning"

    return jsonify(
        {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics,
            "application_memory_mb": round(process.memory_info().rss / 1024 / 1024, 2),
            "memory_efficient": process.memory_info().rss < 1024 * 1024 * 512,  # Under 512MB
            "developer": "Muhammad Abbas",
            "version": "1.0.0",
        }
    )


@app.route("/api/v1/metrics")
def metrics():
    current_metrics = get_system_metrics()

    metrics_history.append(
        {
            "timestamp": datetime.now().isoformat(),
            "memory": current_metrics["memory"]["percent"],
            "cpu": current_metrics["cpu"]["percent"],
        }
    )
    if len(metrics_history) > 60:
        metrics_history.pop(0)

    return jsonify({"current": current_metrics, "history": metrics_history})


@app.route("/api/v1/story")
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


# Docs expect /api/v1/challenge [[12]]; your old code exposed /api/v1/Server [[18]]
@app.route("/api/v1/challenge")
def challenge():
    return jsonify(
        {
            "name": "1GB Server",
            "objective": "Build a production-grade system with only 1GB RAM",
            "components": [
                "Flask Web Application",
                "Real-time Monitoring Dashboard",
                "CI/CD Pipeline",
                "Zero-downtime Deployment",
                "Automatic Rollback",
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


# Backward-compatible alias (optional)
@app.route("/api/v1/Server")
def challenge_alias():
    return challenge()


@app.route("/api/v1/system")
def system():
    return jsonify(get_system_metrics())


if __name__ == "__main__":
    # For local/dev only. On EC2 production use Gunicorn.
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
