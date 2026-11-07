@echo off
rem Cap nhat code len server lingoprism.id.vn: double-click file nay (can Git for Windows).
chcp 65001 >nul
set "BASH=C:\Program Files\Git\bin\bash.exe"
if not exist "%BASH%" (
  echo Chua cai Git for Windows: https://git-scm.com/download/win
  pause
  exit /b 1
)
"%BASH%" "%~dp0..\deploy\push.sh"
echo.
pause
