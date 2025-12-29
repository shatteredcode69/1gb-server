#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/home/ubuntu/1gb-server"
SITE_NAME="1gb-server"

echo "[1/7] Installing OS packages..."
sudo apt update -y
sudo apt install -y python3-pip python3-venv nginx

echo "[2/7] Creating log-friendly permissions..."
sudo usermod -aG www-data ubuntu || true

echo "[3/7] Creating venv + installing Python deps..."
cd "$APP_DIR"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "[4/7] Installing systemd service..."
sudo cp deploy/1gb-server.service /etc/systemd/system/1gb-server.service
sudo systemctl daemon-reload
sudo systemctl enable 1gb-server
sudo systemctl restart 1gb-server

echo "[5/7] Configuring Nginx..."
sudo cp deploy/nginx-1gb-server.conf /etc/nginx/sites-available/$SITE_NAME
sudo ln -sf /etc/nginx/sites-available/$SITE_NAME /etc/nginx/sites-enabled/$SITE_NAME
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

echo "[6/7] Status checks..."
sudo systemctl --no-pager --full status 1gb-server || true
sudo systemctl --no-pager --full status nginx || true

echo "[7/7] Smoke test (local)..."
curl -s http://127.0.0.1:5000/api/v1/health | head -c 300 || true
echo
echo "Done. Open: http://<EC2_PUBLIC_IP>/dashboard"
