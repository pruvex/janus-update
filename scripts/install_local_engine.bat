@echo off
title Janus Local Image Engine - Hardware Detection
color 0E

echo =======================================================
echo     Janus-Projekt: Hardware-Erkennung
echo =======================================================
echo Pruefe auf Nvidia GPU und CUDA-Treiber...
echo.

nvidia-smi >nul 2>nul

if %ERRORLEVEL% equ 0 (
    echo [OK] Nvidia GPU erkannt! Starte GPU-optimierte Installation (ComfyUI).
    call "%~dp0\install_comfyui_gpu.bat"
) else (
    echo [INFO] Keine Nvidia GPU gefunden. Starte CPU-basierte Installation.
    call "%~dp0\install_diffusers_cpu.bat"
)

echo.
echo =======================================================
echo Installation abgeschlossen.
echo =======================================================
pause
