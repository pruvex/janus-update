@echo off
title Janus Local Image Engine - Deinstallation
color 0C

echo =======================================================
echo     Janus-Projekt: Deinstallation der Bild-Engine
echo =======================================================
echo.

set "GPU_DIR=C:\KI\Janus-Image-Engine"
set "CPU_DIR=C:\KI\Janus-Image-Engine-CPU"

if exist "%GPU_DIR%" (
    echo Entferne GPU-Engine Verzeichnis: %GPU_DIR%
    rmdir /s /q "%GPU_DIR%"
)

if exist "%CPU_DIR%" (
    echo Entferne CPU-Engine Verzeichnis: %CPU_DIR%
    rmdir /s /q "%CPU_DIR%"
)

echo.
echo Deinstallation abgeschlossen.
pause
