@echo off
setlocal

echo === Checking Python ===
where python >nul 2>nul
if errorlevel 1 (
    echo Python not found in PATH. Install it from https://www.python.org/downloads/
    echo IMPORTANT: during install, tick "Add python.exe to PATH".
    exit /b 1
)

echo === Creating virtual environment (venv) ===
python -m venv venv
if errorlevel 1 goto :error

call venv\Scripts\activate.bat

echo === Installing dependencies ===
pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 goto :error
pip install pyinstaller
if errorlevel 1 goto :error

echo === Building whale_mirror_bot.exe ===
pyinstaller --clean --noconfirm bot.spec
if errorlevel 1 goto :error

echo.
echo === Done ===
echo Exe is at: dist\whale_mirror_bot\whale_mirror_bot.exe
echo Copy config.yaml, .env and this whole dist\whale_mirror_bot\ folder together before running.
goto :eof

:error
echo.
echo Build failed, see the error above.
exit /b 1
