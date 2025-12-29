#!/bin/bash

# 1GB Server Deployment Script for AWS EC2 t3.micro
# Author: Muhammad Abbas

set -e

echo "================================"
echo "🚀 1GB SERVER DEPLOYMENT"
echo "================================"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if running as ubuntu user
if [ "$USER" != "ubuntu" ]; then
    echo "❌ Please run as ubuntu user"
    exit 1
fi

# Create log directory
echo -e "${YELLOW}📁 Creating log directory...${NC}"
sudo mkdir -p /var/log/1gb-server
sudo chown ubuntu:www-data /var/log/1gb-server

# Setup virtual environment
echo -e "${YELLOW}🐍 Setting up Python virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo -e "${YELLOW}📦 Installing dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# Setup Nginx
echo -e "${YELLOW}🌐 Configuring Nginx...${NC}"
sudo cp nginx.conf /etc/nginx/sites-available/1gb-server
sudo ln -sf /etc/nginx/sites-available/1gb-server /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

# Setup systemd service
echo -e "${YELLOW}⚙️  Installing systemd service...${NC}"
sudo cp 1gb-server.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable 1gb-server
sudo systemctl restart 1gb-server

# Check status
echo -e "${GREEN}✅ Deployment complete!${NC}"
echo ""
echo "Service status:"
sudo systemctl status 1gb-server --no-pager -l

echo ""
echo "================================"
echo "✨ 1GB Server is now running!"
echo "Access at: http://$(curl -s ifconfig.me)"
echo "================================"
