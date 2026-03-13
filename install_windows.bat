@echo off
echo Installing IRIS v7.0 Secure Dependencies...
echo.

REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

echo Installing core dependencies...
pip install flask flask-cors flask-wtf flask-limiter werkzeug python-dotenv

echo Installing AI dependencies...
pip install groq

echo.
echo Installing optional dependencies (voice, system, charts)...
pip install edge-tts psutil pyautogui matplotlib numpy

echo.
echo Installing Pillow (image processing)...
REM Try pre-built wheel first to avoid compilation
pip install Pillow --only-binary :all:
if errorlevel 1 (
    echo Pillow wheel failed, trying source build...
    pip install Pillow
)

echo.
echo Installation complete!
echo.
echo Now:
echo 1. Copy .env.example to .env
echo 2. Add your API keys to .env
echo 3. Run: python app.py
echo.
pause
