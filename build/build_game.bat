@echo off
rem сборка игры из проекта в exe: build_game.bat путь_к_проекту [имя]
cd /d "%~dp0\.."
python build\build_game.py %*
pause
