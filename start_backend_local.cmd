@echo off
chcp 65001 >nul
cd /d %~dp0
set DATABASE_URL=sqlite:///./data/app.db
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
.\.venv\Scripts\python.exe -m alembic -c backend\alembic.ini upgrade head
.\.venv\Scripts\python.exe -m backend.run
