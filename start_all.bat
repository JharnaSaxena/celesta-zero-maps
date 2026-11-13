@echo off
title TerraScope Mars - Launch Full Application
echo =================================================================
echo   TERRASCOPE MARS - FULL-STACK JEZERO EXPLORER ^& BACKEND
echo =================================================================
echo 1. Starting Full-Stack Server on http://localhost:5000 ...
start "Jezero Crater Server" python run_backend.py
timeout /t 3 /nobreak >nul
echo 2. Opening 3D Mars Explorer in browser...
start http://localhost:5000
echo =================================================================
echo Server is running on http://localhost:5000
echo  - 3D Mars Explorer:     http://localhost:5000
echo  - Earth Explorer:       http://localhost:5000/earth.html
echo  - Interactive API Docs: http://localhost:5000/docs
echo =================================================================
pause
