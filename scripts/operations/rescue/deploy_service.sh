#!/bin/bash
# Create systemd service for backend

SERVER="root@10.0.0.60"
PROJECT_DIR="/opt/execl_mix"

echo "=== Creating systemd service file ==="
ssh -p 22 $SERVER "cat > /etc/systemd/system/execl-mix.service << 'EOF'
[Unit]
Description=Social Security Spreadsheet Aggregation Tool - Backend
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$PROJECT_DIR
Environment=\"PATH=$PROJECT_DIR/.venv/bin:/usr/local/bin:/usr/bin:/bin\"
ExecStart=$PROJECT_DIR/.venv/bin/uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF"

echo ""
echo "=== Enabling and starting service ==="
ssh -p 22 $SERVER "systemctl daemon-reload && systemctl enable execl-mix && systemctl start execl-mix && systemctl status execl-mix"

echo ""
echo "Service commands:"
echo "  systemctl status execl-mix"
echo "  systemctl restart execl-mix"
echo "  systemctl stop execl-mix"
echo "  journalctl -u execl-mix -f"
