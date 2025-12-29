# 1GB Server — Flask Monitoring App (EC2 t3.micro ready)

A lightweight monitoring dashboard that proves it can run on a **1GB RAM** server by showing the app’s **RSS memory** in real time.

## Features
- Real-time metrics (1s refresh): CPU, RAM, Disk, Network I/O
- Instance uptime + app uptime
- App process RSS memory (proof for 1GB)
- Responsive UI (mobile + desktop)
- Production deployment: **Nginx (80) → Gunicorn (127.0.0.1:5000) → Flask (systemd)**

## Project Structure (required)
Place files like this:


## API Endpoints
- `GET /api/v1/health` – health + 1GB proof fields (`app_rss_mb`, `headroom_mb`, `is_1gb_ready`)
- `GET /api/v1/metrics` – current metrics + 60-point history
- `GET /api/v1/system` – system + metrics
- `GET /api/v1/story` – story JSON
- `GET /api/v1/challenge` – challenge info JSON
- `GET /api/v1/Server` – legacy alias (backward compatible)

---

# Local run (optional)
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 main.py
# open http://localhost:5000/dashboard
