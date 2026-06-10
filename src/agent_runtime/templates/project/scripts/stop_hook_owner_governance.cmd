@echo off
setlocal

if defined PYTHON_EXE (
    if exist "%PYTHON_EXE%" (
        "%PYTHON_EXE%" "%~dp0stop_hook_owner_governance.py" %*
        exit /b %ERRORLEVEL%
    )
)

set "LOCAL_PY=%LocalAppData%\Programs\Python\Python310\python.exe"
if exist "%LOCAL_PY%" (
    "%LOCAL_PY%" "%~dp0stop_hook_owner_governance.py" %*
    exit /b %ERRORLEVEL%
)

where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    python "%~dp0stop_hook_owner_governance.py" %*
    exit /b %ERRORLEVEL%
)

where py >nul 2>nul
if %ERRORLEVEL% equ 0 (
    py -3 "%~dp0stop_hook_owner_governance.py" %*
    exit /b %ERRORLEVEL%
)

echo {"decision":"block","reason":"Python interpreter not found for owner governance Stop hook","systemMessage":"Set PYTHON_EXE or install Python 3."}
exit /b 0
