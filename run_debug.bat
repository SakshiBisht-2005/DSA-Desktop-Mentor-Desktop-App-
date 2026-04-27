@echo off
setlocal

set "APP_DIR=%~dp0"
set "PYTHON_EXE=C:\Users\ACER\AppData\Local\Programs\Python\Python314\python.exe"

echo Starting DSA Mentor Studio...
echo.

if exist "%PYTHON_EXE%" (
    "%PYTHON_EXE%" -u "%APP_DIR%main.py"
) else (
    python -u "%APP_DIR%main.py"
)

echo.
echo App process ended. Press any key to close this window.
pause >nul

endlocal
