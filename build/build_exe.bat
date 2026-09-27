@echo off
rem сборка движка в exe
cd /d "%~dp0\.."
python build\build_exe.py %*
pause
