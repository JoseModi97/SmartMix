@echo off
title SmartMix - 1-Click Master Mixtape and Scratch Compiler
cd /d "%~dp0"

echo ==============================================================================
echo  SMARTMIX: 1-CLICK ALL-IN-ONE DJ MIXTAPE AND SCRATCH ENGINE
echo ==============================================================================
echo Reading VirtualDJ Automix queue, analyzing cue points, and compiling all mixes...
echo.

python smartmix.py %*

echo.
echo ==============================================================================
echo Execution complete. Check the output directory for your compiled MP3 files.
echo ==============================================================================
pause
