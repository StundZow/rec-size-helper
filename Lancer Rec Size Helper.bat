@echo off
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
    echo Python n'est pas installe ou pas dans le PATH.
    echo Installez Python depuis https://www.python.org/downloads/ puis relancez ce fichier.
    pause
    exit /b 1
)
python -c "import PySide6" >nul 2>nul
if errorlevel 1 (
    echo Installation des dependances (une seule fois)...
    pip install -r requirements.txt
)
start "" pythonw.exe main.py
