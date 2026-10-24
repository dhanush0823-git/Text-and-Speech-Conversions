@echo off
setlocal EnableExtensions
REM VoxAura launcher. Requires Python 3.12 (kokoro does not support 3.13 yet).
pushd "%~dp0"

set "PY="
REM 1) Prefer the Windows py launcher with an explicit 3.12 request.
py -3.12 -c "import sys" >nul 2>&1
if not errorlevel 1 (
    for /f "delims=" %%i in ('py -3.12 -c "import sys;print(sys.executable)"') do set "PY=%%i"
)
REM 2) Otherwise accept `python` on PATH only if it is 3.12.
if not defined PY (
    python -c "import sys;sys.exit(0 if sys.version_info[:2]==(3,12) else 1)" >nul 2>&1
    if not errorlevel 1 (
        for /f "delims=" %%i in ('python -c "import sys;print(sys.executable)"') do set "PY=%%i"
    )
)
if not defined PY goto :nopython

REM An existing .venv must also be 3.12. It is never deleted automatically.
if not exist ".venv\Scripts\python.exe" goto :createvenv
".venv\Scripts\python.exe" -c "import sys;sys.exit(0 if sys.version_info[:2]==(3,12) else 1)" >nul 2>&1
if errorlevel 1 goto :badvenv
goto :venvready

:createvenv
echo Creating virtual environment in .venv ...
"%PY%" -m venv .venv
if errorlevel 1 goto :fail

:venvready
REM Reinstall only when requirements.txt changed since the last successful install.
for %%F in (requirements.txt) do set "REQSTAMP=%%~tF %%~zF"
set "OLDSTAMP="
if exist ".venv\.voxaura_installed" set /p OLDSTAMP=<".venv\.voxaura_installed"
if not "%REQSTAMP%"=="%OLDSTAMP%" (
    echo Installing dependencies. The first install downloads PyTorch and can take several minutes...
    ".venv\Scripts\python.exe" -m pip install --upgrade pip
    if errorlevel 1 goto :fail
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 goto :fail
    >".venv\.voxaura_installed" echo %REQSTAMP%
)

echo.
echo VoxAura is starting. Open  http://127.0.0.1:8000  in your browser.
echo Press Ctrl+C in this window to stop.
echo.
".venv\Scripts\python.exe" -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
if errorlevel 1 goto :fail
goto :end

:nopython
echo.
echo ERROR: Python 3.12 was not found.
echo VoxAura needs Python 3.12 because the Kokoro TTS package does not support Python 3.13.
echo Install it side by side with your other versions (it will not affect them):
echo   winget install Python.Python.3.12
echo or download it from https://www.python.org/downloads/windows/
echo Then run this script again.
goto :fail_pause

:badvenv
echo.
echo ERROR: The existing .venv folder was not created with Python 3.12.
echo Nothing has been deleted. To fix this, delete the .venv folder yourself
echo and run this script again so it can be recreated with Python 3.12.
goto :fail_pause

:fail
echo.
echo VoxAura stopped because of an error. See the messages above.
:fail_pause
pause
popd
exit /b 1

:end
popd
endlocal
