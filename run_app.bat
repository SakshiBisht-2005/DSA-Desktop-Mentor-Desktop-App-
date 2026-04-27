@echo off
setlocal

set "APP_DIR=%~dp0"
set "PYTHON_EXE=C:\Users\ACER\AppData\Local\Programs\Python\Python314\python.exe"

if exist "%PYTHON_EXE%" (
    "%PYTHON_EXE%" "%APP_DIR%main.py"
) else (
    python "%APP_DIR%main.py"
)

endlocal
