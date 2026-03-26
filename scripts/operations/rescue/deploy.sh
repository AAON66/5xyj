#!/bin/bash
# Deployment script for Social Security Spreadsheet Aggregation Tool
# Target: 10.0.0.60

SERVER="root@10.0.0.60"
PROJECT_DIR="/opt/execl_mix"

echo "=== Step 1: Creating project directory on server ==="
ssh -p 22 $SERVER "mkdir -p $PROJECT_DIR && cd $PROJECT_DIR && pwd"

echo ""
echo "=== Step 2: Transferring project files (excluding data and cache) ==="
rsync -avz --progress \
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
  -e "ssh -p 22" \
  ./ $SERVER:$PROJECT_DIR/

echo ""
echo "=== Step 3: Setting up backend environment ==="
ssh -p 22 $SERVER "cd $PROJECT_DIR && python3 -m venv .venv && source .venv/bin/activate && pip install --upgrade pip && pip install -r backend/requirements.txt"

echo ""
echo "=== Step 4: Creating data directories ==="
ssh -p 22 $SERVER "cd $PROJECT_DIR && mkdir -p data/uploads data/outputs data/templates"

echo ""
echo "=== Step 5: Initializing database ==="
ssh -p 22 $SERVER "cd $PROJECT_DIR && source .venv/bin/activate && python -c 'from backend.app.database import init_db; init_db()'"

echo ""
echo "=== Step 6: Installing frontend dependencies ==="
ssh -p 22 $SERVER "cd $PROJECT_DIR/frontend && npm install"

echo ""
echo "=== Step 7: Building frontend ==="
ssh -p 22 $SERVER "cd $PROJECT_DIR/frontend && npm run build"

echo ""
echo "=== Deployment complete! ==="
echo "Next steps:"
echo "1. Configure systemd service (see deploy_service.sh)"
echo "2. Start the backend service"
