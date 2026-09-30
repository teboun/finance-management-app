@echo off
REM Lance l application Salaires (Windows)
cd /d "%~dp0"
where pyw >nul 2>nul
if %errorlevel%==0 (
    start "" pyw -m salary_app.app
    exit /b
)
where pythonw >nul 2>nul
if %errorlevel%==0 (
    start "" pythonw -m salary_app.app
    exit /b
)
echo Python n est pas installe. Installez-le depuis https://www.python.org/downloads/
echo Python is not installed. Install it from https://www.python.org/downloads/
pause
