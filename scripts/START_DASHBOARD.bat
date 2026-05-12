@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Diamond Task Orchestrator UI

REM Always run from this script's folder (fixes wrong cwd when launched via shortcut / some contexts)
cd /d "%~dp0"

echo.
echo  ============================================
echo   Diamond Task Orchestrator UI - Starting...
echo  ============================================
echo   Working dir: %CD%
echo.

set "VENV_PY=%~dp0backend\venv\Scripts\python.exe"
set "APP=%~dp0tools\orchestrator_ui\app.py"

if not exist "%APP%" (
    echo [ERROR] app.py not found:
    echo         %APP%
    echo.
    pause
    exit /b 1
)

REM --- Pick first free port (8501..8510) to avoid "Port 8501 is not available" ---
set "PORT="
for /L %%P in (8501,1,8510) do (
    netstat -ano | findstr /C:":%%P " >nul
    if !errorlevel! == 1 (
        set "PORT=%%P"
        goto :port_found
    )
)
:port_found
if "!PORT!"=="" (
    echo.
    echo [ERROR] No free port found in 8501..8510.
    pause
    exit /b 1
)
echo.
echo [OK] Using port !PORT!

REM --- Prefer backend venv + python -m streamlit (works even if streamlit.exe shim is missing) ---
if exist "%VENV_PY%" (
    echo [OK] Using backend\venv (python -m streamlit)
    "%VENV_PY%" -m streamlit run "%APP%" --server.port !PORT! --browser.gatherUsageStats false
    if errorlevel 1 (
        echo.
        echo [ERROR] streamlit exited with an error. If streamlit is missing, run:
        echo         "%VENV_PY%" -m pip install streamlit filelock pydantic
        echo.
        pause
    )
    goto :eof
)

REM --- Fallback: hardcoded Python (legacy) ---
if exist "C:\python311\Scripts\python.exe" (
    echo [OK] Using C:\python311
    C:\python311\Scripts\python.exe -m streamlit run "%APP%" --server.port !PORT! --browser.gatherUsageStats false
    if errorlevel 1 pause
    goto :eof
)

REM --- Fallback: global ---
where python >nul 2>&1
if %ERRORLEVEL% == 0 (
    echo [OK] Using python on PATH
    python -m streamlit run "%APP%" --server.port !PORT! --browser.gatherUsageStats false
    if errorlevel 1 pause
    goto :eof
)

echo.
echo [ERROR] No Python found. Expected: backend\venv\Scripts\python.exe
echo.
pause
exit /b 1

