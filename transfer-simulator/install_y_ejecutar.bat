@echo off
echo ============================================================
echo   POS Transfer Simulator — Instalacion y arranque
echo ============================================================
echo.

REM Verificar Python
python --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo [ERROR] Python no encontrado. Instala Python 3.10 o superior desde:
    echo         https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/3] Instalando dependencias...
pip install -r requirements.txt --quiet

IF ERRORLEVEL 1 (
    echo [ERROR] No se pudieron instalar las dependencias.
    echo         Ejecuta manualmente:  pip install -r requirements.txt
    pause
    exit /b 1
)

echo [2/3] Dependencias instaladas correctamente.
echo [3/3] Iniciando POS Transfer Simulator...
echo.

python main.py

pause
