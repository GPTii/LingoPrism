@echo off
rem Chep ban sao luu (database, anh, .env) tu server lingoprism.id.vn ve D:\backup-lingoprism (can Git for Windows).
chcp 65001 >nul
set "BASH=C:\Program Files\Git\bin\bash.exe"
if not exist "%BASH%" (
  echo Chua cai Git for Windows: https://git-scm.com/download/win
  pause
  exit /b 1
)
"%BASH%" "%~dp0..\deploy\pull-backups.sh"
if "%1"=="" pause
