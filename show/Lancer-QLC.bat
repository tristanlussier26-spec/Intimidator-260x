@echo off
rem Lance QLC+ avec l acces web (pour le plugin Stream Deck) et le show en mode show.
set "QLC=C:\QLC+\qlcplus.exe"
if not exist "%QLC%" set "QLC=C:\Program Files\QLC+\qlcplus.exe"
if not exist "%QLC%" set "QLC=C:\Program Files (x86)\QLC+\qlcplus.exe"
if not exist "%QLC%" (
  echo QLC+ introuvable. Modifie la ligne set "QLC=..." dans ce fichier.
  pause
  exit /b
)
start "" "%QLC%" -w -p -o "%~dp0Show-Rock.qxw"
