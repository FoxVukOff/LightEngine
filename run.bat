@echo off
rem запуск движка из исходников
cd /d "%~dp0\.."
python main.py %*
