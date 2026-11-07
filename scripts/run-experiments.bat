@echo off
rem Chay thuc nghiem geofence + realtime tren server lingoprism.id.vn va tai ket qua ve (can Git for Windows).
chcp 65001 >nul
set "BASH=C:\Program Files\Git\bin\bash.exe"
if not exist "%BASH%" (
  echo Chua cai Git for Windows: https://git-scm.com/download/win
  pause
  exit /b 1
)
"%BASH%" "%~dp0..\deploy\run-experiments.sh"
echo.
pause
