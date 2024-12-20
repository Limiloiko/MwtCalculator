@echo off

pip install -r requirements.txt
pip install pyinstaller

pyinstaller --onefile main.py

:: rem Move the exe and comprise the folder
set PATH=%PATH%;C:\Program Files\7-Zip
7z a -tzip Executable.zip dist
