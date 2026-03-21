@echo off
cd /d %~dp0
start "backend" cmd /k "%~dp0start_backend_local.cmd"
start "frontend" cmd /k "%~dp0start_frontend_local.cmd"
