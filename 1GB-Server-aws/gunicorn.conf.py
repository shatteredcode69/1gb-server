import os

# Bind to localhost by default (Nginx will expose port 80 publicly)
bind = os.getenv("BIND", f"127.0.0.1:{os.getenv('PORT', '8000')}")

# On a real 1GB instance (t3.micro), keep it conservative by default
workers = int(os.getenv("WEB_CONCURRENCY", "1"))
threads = int(os.getenv("GUNICORN_THREADS", "2"))
worker_class = os.getenv("GUNICORN_WORKER_CLASS", "gthread")

timeout = int(os.getenv("GUNICORN_TIMEOUT", "30"))
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", "20"))
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", "2"))

max_requests = int(os.getenv("GUNICORN_MAX_REQUESTS", "1000"))
max_requests_jitter = int(os.getenv("GUNICORN_MAX_REQUESTS_JITTER", "50"))

accesslog = "-"
errorlog = "-"
loglevel = os.getenv("GUNICORN_LOG_LEVEL", os.getenv("LOG_LEVEL", "info")).lower()

preload_app = os.getenv("GUNICORN_PRELOAD_APP", "false").lower() == "true"
