@echo off
title TerraScope Mars Server
echo =================================================================
echo   TERRASCOPE MARS - FULL-STACK JEZERO CRATER SERVER
echo =================================================================
echo Starting Full-Stack Server on http://localhost:5000 ...
echo  - 3D Mars Explorer:     http://localhost:5000
echo  - Earth Explorer:       http://localhost:5000/earth.html
echo  - Interactive API Docs: http://localhost:5000/docs
echo =================================================================
python run_backend.py
pause
