@echo off

:: Year input
set /p year="Enter the year: "
:: User input
set /p user="Enter you user number: "

::Ensure python dependencies
call check_deps.cmd

::rem Get excels files
echo Downloading files ...
call py -3 get_exports_requests.py --year %year% --user %user%

::rem using selenium
::rem python -3 get_exports_selenium.py
::IF %ERRORLEVEL% NEQ 0 (Echo An error was found &Exit /b 1)

::rem Parse exports
call py -3 process_exports.py --year %year%

echo Script finished!
pause
