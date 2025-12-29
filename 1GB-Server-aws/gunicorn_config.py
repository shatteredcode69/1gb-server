# Gunicorn configuration for 1GB RAM EC2 instance
import multiprocessing

# Server socket
bind = "127.0.0.1:5000"
backlog = 512

# Worker processes (optimized for 1GB RAM)
workers = 2  # 2 workers to fit in 1GB
worker_class = "sync"
worker_connections = 100
timeout = 30
keepalive = 2

# Memory optimization
max_requests = 1000  # Restart workers after 1000 requests to prevent memory leaks
max_requests_jitter = 50

# Logging
accesslog = "/var/log/1gb-server/access.log"
errorlog = "/var/log/1gb-server/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "1gb-server"

# Server mechanics
daemon = False
pidfile = "/var/run/1gb-server.pid"
umask = 0
user = None
group = None
tmp_upload_dir = None

# Preload app for memory efficiency
preload_app = True
