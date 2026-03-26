# Supported Deployment

This repository has one supported deployment workflow: deploy the current brownfield app to Linux with a Python virtual environment, a built frontend bundle, and a `systemd` backend service.

This document intentionally does not promote Docker, workstation-only helpers, or server-specific rescue scripts as equivalent options.

## Supported Deployment Contract

The supported deployment path keeps the existing runtime behavior:

- Backend entrypoint: `python -m backend.run`
- Backend bind: `127.0.0.1:8000`
- Frontend build output: `frontend/dist`
- Database migrations: Alembic from `backend/alembic.ini`
- Export templates: configured from repo-controlled fixtures or explicit deploy-time paths, not workstation Desktop paths

## 1. Provision The Host

Install the baseline packages on a Linux host:

```bash
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3-pip nodejs npm
```

Create the application directory and place the repository there:

```bash
sudo mkdir -p /opt/execl_mix
sudo chown "$USER":"$USER" /opt/execl_mix
git clone <repo-url> /opt/execl_mix
cd /opt/execl_mix
```

## 2. Configure Environment

Copy the example environment file and fill in production values:

```bash
cp .env.example .env
```

These settings are mandatory for a supported deployment:

```env
DATABASE_URL=sqlite:///./data/app.db
ADMIN_PASSWORD=<set-a-non-default-password>
HR_PASSWORD=<set-a-non-default-password>
AUTH_SECRET_KEY=<generate-a-random-secret>
SALARY_TEMPLATE_PATH=./data/templates/regression/salary-template.xlsx
FINAL_TOOL_TEMPLATE_PATH=./data/templates/regression/final-tool-template.xlsx
VITE_API_BASE_URL=https://your-domain.example/api/v1
```

Production rules:

- `ADMIN_PASSWORD` must not keep the repo default value
- `HR_PASSWORD` must not keep the repo default value
- `AUTH_SECRET_KEY` must be a strong random secret
- `SALARY_TEMPLATE_PATH` and `FINAL_TOOL_TEMPLATE_PATH` must point to repo-controlled fixtures or explicit deployment-managed copies
- Do not depend on `C:\Users\...Desktop\...` template locations in a supported deployment

If you want to use different template copies, keep them under deployment-managed storage and update `SALARY_TEMPLATE_PATH` and `FINAL_TOOL_TEMPLATE_PATH` explicitly.

## 3. Prepare Runtime Directories

```bash
mkdir -p data/uploads data/samples data/templates data/outputs
```

If you use the checked-in regression templates as the deploy default, copy them into place or point the environment variables directly at `data/templates/regression/...`.

## 4. Create The Virtual Environment And Install Backend Dependencies

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
python -m alembic -c backend/alembic.ini upgrade head
```

## 5. Install Frontend Dependencies And Build

```bash
cd frontend
npm install
npm run build
cd /opt/execl_mix
```

The supported deployment artifact for the frontend is the built `frontend/dist` directory. Serve that bundle with your standard static hosting layer for the environment.

## 6. Configure systemd For The Backend

Create `/etc/systemd/system/execl-mix-backend.service`:

```ini
[Unit]
Description=execl_mix backend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/execl_mix
EnvironmentFile=/opt/execl_mix/.env
ExecStart=/opt/execl_mix/.venv/bin/python -m backend.run
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable execl-mix-backend
sudo systemctl start execl-mix-backend
sudo systemctl status execl-mix-backend
```

Check logs with:

```bash
sudo journalctl -u execl-mix-backend -f
```

## 7. Verify The Deployment

From the host, confirm the backend is reachable on the local bind address:

```bash
curl http://127.0.0.1:8000/health
```

Recommended follow-up verification:

- confirm the frontend build exists at `frontend/dist`
- confirm login works with the configured `ADMIN_PASSWORD` and `HR_PASSWORD`
- confirm both template paths resolve before running exports

## Unsupported Or Historical References

These may still exist in the repository, but they are not the supported deployment path:

- `DEPLOYMENT_SERVER.md`
- `deploy_all.sh`
- `start_service.py`
- server-specific `10.0.0.60` helpers
- Docker-oriented notes or rescue scripts

If those materials are needed for investigation or recovery, treat them as historical references rather than the canonical operator workflow.
