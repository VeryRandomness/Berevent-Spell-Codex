@echo off
setlocal
echo ============================================
echo   Building Berevent Spell Codex (.exe)
echo ============================================
echo.

where python >nul 2>&1
if errorlevel 1 (
  echo ERROR: Python was not found on your PATH.
  echo.
  echo   1. Install Python 3 from https://www.python.org/downloads/
  echo   2. During setup, TICK "Add python.exe to PATH"
  echo   3. Re-run this build.bat
  echo.
  pause
  exit /b 1
)

echo Installing PyInstaller (one-time)...
python -m pip install --upgrade pip >nul 2>&1
python -m pip install pyinstaller
if errorlevel 1 ( echo. & echo ERROR: could not install PyInstaller. & pause & exit /b 1 )

echo.
echo Building... this takes a minute.
python -m PyInstaller --noconfirm BereventSpellCodex.spec
if errorlevel 1 ( echo. & echo ERROR: build failed - see messages above. & pause & exit /b 1 )

echo.
echo ============================================
echo   Done.
echo   Your portable app:  dist\BereventSpellCodex.exe
echo   Hand that single file to players - nothing to install.
echo ============================================
pause
