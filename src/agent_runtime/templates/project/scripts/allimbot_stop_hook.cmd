@echo off
setlocal

if defined PYTHON_EXE (
    if exist "%PYTHON_EXE%" (
        "%PYTHON_EXE%" "%~dp0allimbot.py" "agent_runtime session stop requested" -t "agent_runtime session"
        exit /b 0
    )
)

set "LOCAL_PY=%LocalAppData%\Programs\Python\Python310\python.exe"
if exist "%LOCAL_PY%" (
    "%LOCAL_PY%" "%~dp0allimbot.py" "agent_runtime session stop requested" -t "agent_runtime session"
    exit /b 0
)

where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    python "%~dp0allimbot.py" "agent_runtime session stop requested" -t "agent_runtime session"
    exit /b 0
)

where py >nul 2>nul
if %ERRORLEVEL% equ 0 (
    py -3 "%~dp0allimbot.py" "agent_runtime session stop requested" -t "agent_runtime session"
)

exit /b 0
