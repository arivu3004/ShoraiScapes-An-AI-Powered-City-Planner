@echo off
REM Run Flask with Waitress WSGI Server
cd /d "%~dp0"
python -m pip install -q waitress 2>nul
echo Starting Flask with Waitress WSGI Server...
echo.
echo Visit: http://localhost:5000
echo.
python -m waitress --host=0.0.0.0 --port=5000 wsgi:app
pause
