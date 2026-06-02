@echo off

cd /d "%~dp0"

powershell -ExecutionPolicy Bypass -File ".\scripts\update_repo.ps1"

pause