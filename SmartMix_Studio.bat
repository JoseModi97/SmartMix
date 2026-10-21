@echo off
title SmartMix Studio - DJ Continuous Mixtape Engine
cd /d "%~dp0"

start "" pythonw smartmix_gui.py
if errorlevel 1 (
    python smartmix_gui.py
    pause
)
