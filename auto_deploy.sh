#!/bin/bash
set -e

SERVER="10.0.0.60"
USER="root"
PASSWORD="gQJwgfG9obG57p"
PROJECT_DIR="/opt/execl_mix"

echo "=== Step 1: Transferring files ==="
sshpass -p "$PASSWORD" rsync -avz --progress \
  --exclude 'data/' \
  --exclude 'node_modules/' \
  --exclude '__pycache__/' \
  --exclude '.venv/' \
  --exclude '.git/' \
  --exclude '*.pyc' \
  --exclude '.idea/' \
  --exclude 'dist/' \
  --exclude 'build/' \
  --exclude '.claude/' \
  --exclude 'everything-claude-code/' \
  -e "ssh -p 22 -o StrictHostKeyChecking=no" \
  ./ $USER@$SERVER:$PROJECT_DIR/

echo ""
echo "=== Step 2: Installing backend ==="
sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no -p 22 $USER@$SERVER << 'ENDSSH'
cd /opt/execl_mix
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt
ENDSSH

echo ""
echo "=== Step 3: Creating directories ==="
sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no -p 22 $USER@$SERVER \
  "mkdir -p /opt/execl_mix/data/{uploads,outputs,templates}"

echo ""
echo "=== Step 4: Installing frontend ==="
sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no -p 22 $USER@$SERVER << 'ENDSSH'
cd /opt/execl_mix/frontend
npm install
npm run build
ENDSSH

echo ""
echo "=== Step 5: Creating systemd service ==="
sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no -p 22 $USER@$SERVER << 'ENDSSH'
cat > /etc/systemd/system/execl-mix.service << 'EOF'
[Unit]
Description=Excel Mix Backend
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/execl_mix
Environment="PATH=/opt/execl_mix/.venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/opt/execl_mix/.venv/bin/uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable execl-mix
systemctl restart execl-mix
sleep 2
systemctl status execl-mix --no-pager
ENDSSH

echo ""
echo "=== Deployment Complete ==="
echo "Backend: http://$SERVER:8000"
