@echo off
title CodeForge AI - Launcher
color 0b
rem All launch logic lives in run_codeforge.ps1. Pass --dev for the hot-reload dev server.
if /i "%~1"=="--dev" (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_codeforge.ps1" -Dev
) else (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_codeforge.ps1"
)
echo Keep the backend and frontend terminal windows open.
pause
