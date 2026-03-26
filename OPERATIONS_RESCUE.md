# Rescue And Legacy Operations

`OPERATIONS.md` and `DEPLOYMENT.md` define the supported workflows for this repository. Everything listed here is non-canonical rescue, legacy, or server-specific tooling kept only for investigation and emergency recovery.

## Supported Vs Rescue

- Supported local workflow: `start_project_local.cmd` or `start_project_local.ps1`
- Supported deployment workflow: the Linux `systemd` checklist in `DEPLOYMENT.md`
- Rescue or legacy tooling: anything now relocated under `scripts/operations/rescue/`

Do not treat the rescue directory as an alternate quick start. Operators should follow `OPERATIONS.md` first and only reach for rescue files when they are intentionally investigating an old server-specific path.

## Rescue Inventory

The following repo-root helpers were relocated to `scripts/operations/rescue/` so they no longer masquerade as canonical entrypoints:

### Server-Specific Deploy And Restart Helpers

- `absolute_path_deploy.py`
- `auto_deploy.py`
- `auto_deploy.sh`
- `check_service.py`
- `clean_cache_deploy.py`
- `clean_deploy.py`
- `clean_env_start.py`
- `deploy.sh`
- `deploy_all.sh`
- `deploy_auto.py`
- `deploy_complete.py`
- `deploy_service.sh`
- `final.py`
- `final_deploy.py`
- `final_deploy_clean.py`
- `final_fix.py`
- `final_start.py`
- `force_rebuild.py`
- `kill_and_restart.py`
- `manual_start.py`
- `rebuild_venv.py`
- `redeploy.py`
- `restart_clean.py`
- `setup_nginx.py`
- `simple_start.py`
- `start_service.py`
- `upload_and_start.py`
- `upload_fixed.py`

### One-Off Repair And Environment Helpers

- `debug_error.py`
- `debug_venv.py`
- `fix_all_types.py`
- `fix_deploy.py`
- `fix_mapped.py`
- `fix_nginx.py`
- `fix_nginx_default.py`
- `fix_on_server.py`
- `fix_server_files.py`
- `fix_types.py`
- `init_db.py`
- `install_python311.py`
- `install_python39.py`
- `install_xlrd.py`
- `venv_copies.py`

## How To Read These Files

- Treat them as historical or rescue artifacts, not as the supported operating model.
- Many scripts embed assumptions about `10.0.0.60`, root SSH access, or ad hoc repair steps.
- If one of these files must be inspected or run, start from the repo root so existing relative paths still make sense.

## Related References

- `OPERATIONS.md`: supported local workflow and the canonical deployment pointer
- `DEPLOYMENT.md`: supported Linux and `systemd` deployment path
- `DEPLOYMENT_SERVER.md`: legacy and server-specific notes for the old deployment surface
- `scripts/operations/rescue/README.md`: on-disk warning banner for the relocated rescue surface
