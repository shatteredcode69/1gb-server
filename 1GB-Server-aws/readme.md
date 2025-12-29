# 🚀 1GB Server

A production-grade monitoring system designed to run within **1GB RAM**.

This project demonstrates real-world **DevOps & Cloud engineering** skills:
- Resource optimization
- Production Flask deployment
- AWS EC2 hosting
- Memory-aware health checks
- Real-time monitoring dashboard

---

## 🔧 Tech Stack
- Python 3.11
- Flask
- Gunicorn
- psutil
- AWS EC2 (t3.micro)

---

## 🚀 Run on AWS EC2

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

export MAX_APP_MEMORY_MB=1024
gunicorn -w 2 -b 0.0.0.0:5000 app.main:app
