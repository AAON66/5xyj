# Legacy Server-Specific Deployment Notes

This file is a legacy, server-specific reference for the old `10.0.0.60` deployment surface. It is not the canonical deployment path.

Normal operators should start with `OPERATIONS.md` and then follow `DEPLOYMENT.md` for the supported Linux and `systemd` workflow.

## What This File Covers

- historical notes for the `10.0.0.60` host
- direct SSH and `rsync` steps that assume root access
- older helper scripts that now live under `scripts/operations/rescue/`

## Legacy Helper Locations

The old quick-deploy scripts were relocated so they are visibly non-canonical:

- `scripts/operations/rescue/deploy.sh`
- `scripts/operations/rescue/deploy_service.sh`
- `scripts/operations/rescue/deploy_all.sh`
- `scripts/operations/rescue/start_service.py`

Those files may still help when auditing a previous server state, but they should not be treated as the supported workflow for new environments.

## Historical Host Assumptions

These notes describe an older server-specific path with assumptions such as:

- SSH access to `10.0.0.60` as `root`
- direct file transfer into `/opt/execl_mix`
- manual frontend build and backend restart steps on that server

Keep those assumptions isolated to rescue and audit work. For current supported deployment guidance, return to `OPERATIONS.md` and `DEPLOYMENT.md`.

## Historical Commands

If you are auditing the old environment, the legacy notes used the following style of commands:

```bash
rsync -avz --exclude 'data/' --exclude 'node_modules/' --exclude '.venv/' \
  -e "ssh -p 22" ./ root@10.0.0.60:/opt/execl_mix/
ssh -p 22 root@10.0.0.60
```

These commands are intentionally preserved as reference material only. They are not the supported deployment contract.

## Access Reference

- Historical backend API: `http://10.0.0.60:8000`
- Historical frontend serving: backend static hosting or ad hoc nginx setup
