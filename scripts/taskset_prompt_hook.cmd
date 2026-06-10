@echo off
setlocal

if defined PYTHON_EXE (
    if exist "%PYTHON_EXE%" (
        "%PYTHON_EXE%" "%~dp0taskset_prompt_hook.py" %*
        exit /b %ERRORLEVEL%
    )
)

set "LOCAL_PY=%LocalAppData%\Programs\Python\Python310\python.exe"
if exist "%LOCAL_PY%" (
    "%LOCAL_PY%" "%~dp0taskset_prompt_hook.py" %*
    exit /b %ERRORLEVEL%
)

where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    python "%~dp0taskset_prompt_hook.py" %*
    exit /b %ERRORLEVEL%
)

where py >nul 2>nul
if %ERRORLEVEL% equ 0 (
    py -3 "%~dp0taskset_prompt_hook.py" %*
    exit /b %ERRORLEVEL%
)

echo {}
exit /b 0
