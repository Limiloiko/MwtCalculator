@echo off

:: User input
set /p user="Enter you user number: "
:: Year input
set /p year="Enter the year: "

::Ensure python dependencies
call check_deps.cmd

::rem Get excels files
echo Downloading files ...
call py -3 get_exports_requests.py --year %year% --user %user%

::rem Parse exports
call py -3 process_exports.py --year %year%

echo Script finished!
pause
