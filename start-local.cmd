@echo off
start "ArenaFlow backend" /b cmd /c "cd /d C:\Users\ext_hedemitr\Documents\ArenaSystem_All\arenasystem && venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000 --noreload > backend-local.log 2>&1"
start "ArenaFlow frontend" /b cmd /c "cd /d C:\Users\ext_hedemitr\Documents\ArenaSystem_All\arenasystem-web && npm.cmd run dev -- --host 127.0.0.1 --port 5173 > frontend-local.log 2>&1"
