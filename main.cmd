@echo off

::Ensure python dependencies
call check_deps.cmd

::rem Get excels files
echo Downloading files ...
call py -3 get_exports_requests.py

::rem using selenium
::rem python -3 get_exports_selenium.py
::IF %ERRORLEVEL% NEQ 0 (Echo An error was found &Exit /b 1)

::rem Parse exports

echo Script finished!
pause
