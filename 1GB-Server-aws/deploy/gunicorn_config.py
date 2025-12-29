# Gunicorn config tuned for EC2 t3.micro (1GB RAM)
# Run: gunicorn -c deploy/gunicorn.conf.py main:app

import os

bind = "127.0.0.1:5000"
workers = int(os.getenv("GUNICORN_WORKERS", "2"))  # set to 1 if memory pressure
worker_class = "sync"
threads = 1

timeout = 30
keepalive = 2

# Prevent long-running memory growth
max_requests = 800
max_requests_jitter = 100

# Logging: systemd will capture stdout/stderr
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info")

# preload_app can reduce per-worker memory due to copy-on-write
preload_app = True
