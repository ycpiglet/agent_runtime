@echo off
setlocal

rem TASK-AR-509: non-blocking upstream release notice at session start.
rem Runs `agent_runtime update-notify` (installed CLI) and never blocks the
rem session: every branch exits 0 and interpreter errors stay silent.

set "VENV_PY=%~dp0..\.venv\Scripts\python.exe"
if exist "%VENV_PY%" (
    "%VENV_PY%" -m agent_runtime.cli update-notify 2>nul
    exit /b 0
)

if defined PYTHON_EXE (
    if exist "%PYTHON_EXE%" (
        "%PYTHON_EXE%" -m agent_runtime.cli update-notify 2>nul
        exit /b 0
    )
)

set "LOCAL_PY=%LocalAppData%\Programs\Python\Python310\python.exe"
if exist "%LOCAL_PY%" (
    "%LOCAL_PY%" -m agent_runtime.cli update-notify 2>nul
    exit /b 0
)

where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    python -m agent_runtime.cli update-notify 2>nul
    exit /b 0
)

where py >nul 2>nul
if %ERRORLEVEL% equ 0 (
    py -3 -m agent_runtime.cli update-notify 2>nul
    exit /b 0
)

exit /b 0
