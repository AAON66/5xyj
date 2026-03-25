# Deployment Guide

## Prerequisites
- SSH access to 10.0.0.60 (root user)
- rsync installed locally

## Quick Deploy

```bash
# Make scripts executable
chmod +x deploy.sh deploy_service.sh

# Run deployment
./deploy.sh

# Setup systemd service
./deploy_service.sh
```

## Manual Steps

If scripts fail, run commands manually:

### 1. Transfer files
```bash
rsync -avz --exclude 'data/' --exclude 'node_modules/' --exclude '.venv/' \
  -e "ssh -p 22" ./ root@10.0.0.60:/opt/execl_mix/
```

### 2. SSH into server
```bash
ssh -p 22 root@10.0.0.60
```

### 3. Setup backend
```bash
cd /opt/execl_mix
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

### 4. Setup frontend
```bash
cd frontend
npm install
npm run build
```

### 5. Initialize data
```bash
cd /opt/execl_mix
mkdir -p data/uploads data/outputs data/templates
source .venv/bin/activate
python -c 'from backend.app.database import init_db; init_db()'
```

### 6. Start service
```bash
source .venv/bin/activate
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

## Access
- Backend API: http://10.0.0.60:8000
- Frontend: Serve from backend or use nginx
