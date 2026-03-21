@echo off
cd /d %~dp0
set DATABASE_URL=sqlite:///./data/app.db
.\.venv\Scripts\python.exe -m alembic -c backend\alembic.ini upgrade head
.\.venv\Scripts\python.exe -m backend.run
